import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta

from fastapi import Depends, HTTPException, Request
from sqlalchemy import delete
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Session

from app.config import get_settings
from app.domain.contracts import Professional
from app.infrastructure.database import get_engine
from app.infrastructure.identity import IdentityRepository
from app.infrastructure.models import Audit, LoginLimit, SessionRecord

COOKIE = "ac_actions_session"


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def identities() -> IdentityRepository:
    return IdentityRepository()


def secret() -> bytes:
    value = get_settings().session_secret.get_secret_value()
    if len(value) < 32:
        raise HTTPException(503, "Configuração de sessão pendente. Execute a preparação local.")
    return value.encode()


def csrf(token: str) -> str:
    return hmac.new(secret(), ("csrf:" + token).encode(), hashlib.sha256).hexdigest()


def enforce_origin(request: Request) -> None:
    if request.headers.get("origin") != get_settings().frontend_origin:
        raise HTTPException(403, "Origem não autorizada.")


def consume_login(identifier: str, address: str) -> None:
    now = datetime.now(UTC)
    allowed = True
    with Session(get_engine()) as session, session.begin():
        session.execute(delete(LoginLimit).where(LoginLimit.expires_at <= now))
        for value, limit in [(identifier, 5), ("address:" + address, 25)]:
            key = hmac.new(secret(), value.encode(), hashlib.sha256).hexdigest()
            statement = insert(LoginLimit).values(
                key=key, attempts=1, expires_at=now + timedelta(minutes=10)
            )
            statement = statement.on_conflict_do_update(
                index_elements=[LoginLimit.key],
                set_={"attempts": LoginLimit.attempts + 1},
            ).returning(LoginLimit.attempts)
            allowed = session.scalar(statement) <= limit and allowed
    if not allowed:
        raise HTTPException(
            429, "Muitas tentativas. Aguarde dez minutos.", headers={"Retry-After": "600"}
        )


def create_session(professional: Professional) -> str:
    token = secrets.token_urlsafe(32)
    with Session(get_engine()) as session, session.begin():
        session.execute(delete(SessionRecord).where(SessionRecord.expires_at <= datetime.now(UTC)))
        session.add(
            SessionRecord(
                token_hash=digest(token),
                profissional_id=professional.profissional_id,
                expires_at=datetime.now(UTC) + timedelta(hours=8),
            )
        )
        session.add(
            Audit(
                profissional_id=professional.profissional_id,
                operacao="auth.login",
                entidade_id=professional.profissional_id,
            )
        )
    return token


def clear_login_failures(identifier: str) -> None:
    # A conta não acumula logins bem-sucedidos como falhas; limite de IP permanece.
    key = hmac.new(secret(), identifier.encode(), hashlib.sha256).hexdigest()
    with Session(get_engine()) as session, session.begin():
        session.execute(delete(LoginLimit).where(LoginLimit.key == key))


def current_professional(
    request: Request, repository: IdentityRepository = Depends(identities)
) -> Professional:
    token = request.cookies.get(COOKIE, "")
    if not token:
        raise HTTPException(401, "Entre com sua conta institucional.")
    with Session(get_engine()) as session:
        row = session.get(SessionRecord, digest(token))
        if not row or row.expires_at.replace(tzinfo=UTC) <= datetime.now(UTC):
            raise HTTPException(401, "Sua sessão expirou. Entre novamente.")
        professional_id = row.profissional_id
    result = repository.find(professional_id, by_id=True)
    if not result or not result[0].allowed:
        with Session(get_engine()) as session, session.begin():
            session.execute(delete(SessionRecord).where(SessionRecord.token_hash == digest(token)))
        raise HTTPException(403, "Seu perfil não possui acesso a este módulo.")
    return result[0]


def writer(
    request: Request, professional: Professional = Depends(current_professional)
) -> Professional:
    enforce_origin(request)
    if not hmac.compare_digest(
        request.headers.get("x-csrf-token", ""), csrf(request.cookies.get(COOKIE, ""))
    ):
        raise HTTPException(403, "Recarregue a página para renovar a proteção da sessão.")
    return professional


def technologist(professional: Professional = Depends(current_professional)) -> Professional:
    if professional.equipe != "tecnologia":
        raise HTTPException(403, "Sem permissão. Área exclusiva da equipe Tecnologia.")
    return professional
