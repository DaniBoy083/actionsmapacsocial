from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.domain.clinical import ClinicalInput, ClinicalView
from app.domain.contracts import Professional
from app.infrastructure.clinical import SqlClinicalRepository
from app.infrastructure.database import get_engine
from app.security.session import current_professional, writer

router = APIRouter(prefix="/api/v1/acoes/{action_id}")


@router.get("/acesso-clinico")
def clinical_access(action_id: UUID, actor: Professional = Depends(current_professional)):
    with Session(get_engine()) as session, session.begin():
        try:
            SqlClinicalRepository(session, actor).scope(str(action_id))
        except HTTPException as error:
            if error.status_code in {403, 503}:
                return {"permitido": False}
            raise
        return {"permitido": True}


@router.get("/beneficiarios/{person_id}/clinica", response_model=ClinicalView)
def clinical_read(
    action_id: UUID,
    person_id: UUID,
    versao: int | None = Query(None, ge=1),
    actor: Professional = Depends(current_professional),
):
    with Session(get_engine()) as session, session.begin():
        return SqlClinicalRepository(session, actor).read(str(action_id), str(person_id), versao)


@router.put("/beneficiarios/{person_id}/clinica", response_model=ClinicalView)
def clinical_save(
    action_id: UUID, person_id: UUID, data: ClinicalInput, actor: Professional = Depends(writer)
):
    with Session(get_engine()) as session, session.begin():
        return SqlClinicalRepository(session, actor).save(str(action_id), str(person_id), data)
