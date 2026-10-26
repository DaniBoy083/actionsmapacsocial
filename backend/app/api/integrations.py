from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.application.integrations import CredentialService
from app.domain.contracts import Professional
from app.domain.integrations import (
    CredentialAuthorization,
    CredentialInput,
    CredentialMetadata,
    ExportPage,
    IssuedCredential,
    ServiceHealth,
)
from app.infrastructure.actions import audit
from app.infrastructure.database import get_engine
from app.infrastructure.identity import IdentityRepository, verify_password
from app.infrastructure.integrations import (
    RATE_LIMIT,
    SqlCredentialRepository,
    consume_service_token,
    export_page,
    metadata,
)
from app.infrastructure.models import IntegrationCredential
from app.security.session import (
    clear_login_failures,
    consume_login,
    identities,
    technologist,
    writer,
)

router = APIRouter(prefix="/api/v1")
bearer = HTTPBearer(auto_error=False, scheme_name="IntegrationBearer")


def reauthorize(
    data: CredentialAuthorization,
    request: Request,
    professional: Professional,
    repository: IdentityRepository,
) -> None:
    identifier = "integration-reauth:" + professional.profissional_id
    consume_login(identifier, request.client.host if request.client else "unknown")
    found = repository.find(professional.profissional_id, by_id=True)
    valid = verify_password(data.password.get_secret_value(), found[1] if found else "")
    if not found or not found[0].allowed or found[0].equipe != "tecnologia" or not valid:
        with Session(get_engine()) as session, session.begin():
            audit(session, professional, "integracoes.reauth.denied", professional.profissional_id)
        raise HTTPException(401, "Confirme sua senha institucional para gerenciar tokens.")
    clear_login_failures(identifier)


@router.get("/tecnologia/tokens", response_model=list[CredentialMetadata])
def list_credentials(professional: Professional = Depends(technologist)):
    with Session(get_engine()) as session, session.begin():
        rows = session.scalars(
            select(IntegrationCredential)
            .order_by(
                (
                    IntegrationCredential.revogado_em.is_(None)
                    & (
                        IntegrationCredential.expira_em.is_(None)
                        | (IntegrationCredential.expira_em > datetime.now(UTC))
                    )
                ).desc(),
                IntegrationCredential.criado_em.desc(),
            )
            .limit(100)
        ).all()
        audit(session, professional, "integracoes.token.list", "agenda-digital")
        return [metadata(row) for row in rows]


@router.post("/tecnologia/tokens", status_code=201, response_model=IssuedCredential)
def create_credential(
    data: CredentialInput,
    request: Request,
    _writer: Professional = Depends(writer),
    professional: Professional = Depends(technologist),
    repository: IdentityRepository = Depends(identities),
):
    reauthorize(data, request, professional, repository)
    with Session(get_engine()) as session, session.begin():
        return CredentialService(SqlCredentialRepository(session)).create(data, professional)


@router.post("/tecnologia/tokens/{identifier}/revogar", response_model=CredentialMetadata)
def revoke_credential(
    identifier: UUID,
    data: CredentialAuthorization,
    request: Request,
    _writer: Professional = Depends(writer),
    professional: Professional = Depends(technologist),
    repository: IdentityRepository = Depends(identities),
):
    reauthorize(data, request, professional, repository)
    with Session(get_engine()) as session, session.begin():
        return CredentialService(SqlCredentialRepository(session)).revoke(
            str(identifier), professional
        )


@router.post(
    "/tecnologia/tokens/{identifier}/rotacionar", status_code=201, response_model=IssuedCredential
)
def rotate_credential(
    identifier: UUID,
    data: CredentialInput,
    request: Request,
    _writer: Professional = Depends(writer),
    professional: Professional = Depends(technologist),
    repository: IdentityRepository = Depends(identities),
):
    reauthorize(data, request, professional, repository)
    with Session(get_engine()) as session, session.begin():
        return CredentialService(SqlCredentialRepository(session)).rotate(
            str(identifier), data, professional
        )


def service_credential(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> str:
    with Session(get_engine()) as session, session.begin():
        identifier, status = consume_service_token(
            session, "Bearer " + credentials.credentials if credentials else ""
        )
    if status == 401:
        raise HTTPException(
            401,
            "Token de integração ausente, inválido, expirado ou revogado.",
            headers={"WWW-Authenticate": 'Bearer realm="actions-map-integrations"'},
        )
    if status == 429:
        raise HTTPException(
            429,
            "Limite de consultas atingido. Aguarde a próxima janela.",
            headers={"Retry-After": str(60 - datetime.now(UTC).second)},
        )
    return identifier


@router.get("/integracoes/health", response_model=ServiceHealth)
def service_health(_credential: str = Depends(service_credential)):
    with Session(get_engine()) as session:
        session.scalar(text("SELECT 1"))
    return {"status": "API_OK", "schema_version": "1.1", "limite_por_minuto": RATE_LIMIT}


@router.get("/integracoes/acoes/resumos", response_model=ExportPage)
def service_summaries(
    page: int = Query(1, ge=1, le=10),
    exportacao_id: UUID | None = None,
    credential: str = Depends(service_credential),
):
    with Session(get_engine()) as session, session.begin():
        return export_page(session, credential, page, str(exportacao_id) if exportacao_id else None)
