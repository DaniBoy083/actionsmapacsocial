import base64
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.domain.contracts import Professional
from app.domain.institutions import InstitutionInput
from app.infrastructure.actions import audit
from app.infrastructure.database import get_engine
from app.infrastructure.institutions import register, search
from app.infrastructure.models import InstitutionLogo
from app.security.session import current_professional, writer

router = APIRouter(prefix="/api/v1/instituicoes")


@router.get("")
def search_institutions(
    busca: str = Query("", max_length=160), actor: Professional = Depends(current_professional)
):
    with Session(get_engine()) as session:
        return search(session, busca)


@router.post("", status_code=201)
def create_institution(data: InstitutionInput, actor: Professional = Depends(writer)):
    with Session(get_engine()) as session, session.begin():
        row = register(session, data)
        audit(session, actor, "instituicoes.save", row.id)
        return {"id": row.id, "nome": row.nome, "tipo": row.tipo}


@router.get("/{institution_id}/marcas/{logo_id}")
def logo(institution_id: UUID, logo_id: UUID, actor: Professional = Depends(current_professional)):
    with Session(get_engine()) as session, session.begin():
        row = session.get(InstitutionLogo, str(logo_id))
        if not row or row.instituicao_id != str(institution_id):
            raise HTTPException(404, "Marca não encontrada nesta instituição.")
        audit(session, actor, "instituicoes.marcas.read", row.id)
        return Response(base64.b64decode(row.conteudo_base64), media_type="image/png")
