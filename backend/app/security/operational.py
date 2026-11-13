"""Sessão exclusiva LOCAL; cookies e tabela distintos do login institucional."""

import hmac
from datetime import UTC, datetime

from fastapi import Depends, HTTPException, Request
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.domain.contracts import Professional
from app.infrastructure.database import get_engine
from app.infrastructure.models import OperationalAccount, OperationalSession, StaffRecord
from app.infrastructure.operational_access import operator_actor, require_operational_enabled
from app.security.session import csrf, digest, enforce_origin


def operational_cookie(request: Request):
    return (
        "ac_actions_demo_operational"
        if getattr(request.app.state, "demonstracao", False)
        else "ac_actions_operational"
    )


def current_operator(request: Request) -> Professional:
    require_operational_enabled()
    token = request.cookies.get(operational_cookie(request), "")
    with Session(get_engine()) as session, session.begin():
        found = session.execute(
            select(OperationalSession, OperationalAccount, StaffRecord)
            .join(OperationalAccount, OperationalAccount.id == OperationalSession.conta_id)
            .join(StaffRecord, StaffRecord.id == OperationalAccount.profissional_id)
            .where(OperationalSession.token_hash == digest(token))
        ).first()
        if not token or not found or found[0].expires_at.replace(tzinfo=UTC) <= datetime.now(UTC):
            raise HTTPException(401, "Entre com seu acesso do Actions Map.")
        return operator_actor(found[1], found[2])


def operational_writer(request: Request, actor: Professional = Depends(current_operator)):
    enforce_origin(request)
    if not hmac.compare_digest(
        request.headers.get("x-csrf-token", ""),
        csrf(request.cookies.get(operational_cookie(request), "")),
    ):
        raise HTTPException(403, "Recarregue a página para renovar a proteção da sessão.")
    return actor


def revoke_operator_session(session, token):
    session.execute(
        delete(OperationalSession).where(OperationalSession.token_hash == digest(token))
    )
