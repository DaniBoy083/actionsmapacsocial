from contextlib import contextmanager
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.application.staff import StaffService
from app.domain.contracts import Professional
from app.domain.staff import (
    AssignmentInput,
    AssignmentPage,
    AssignmentUpdate,
    AssignmentView,
    StaffInput,
    StaffPage,
    StaffView,
)
from app.infrastructure.database import get_engine
from app.infrastructure.staff import SqlStaffRepository
from app.security.session import current_professional, writer

router = APIRouter(prefix="/api/v1")


@contextmanager
def service_scope(actor: Professional):
    try:
        with Session(get_engine()) as session, session.begin():
            yield StaffService(SqlStaffRepository(session), actor)
    except IntegrityError:
        raise HTTPException(
            409, "Registro ou atribuição já cadastrados. Recarregue a lista."
        ) from None


@router.get("/profissionais", response_model=StaffPage)
def list_staff(
    busca: str = Query("", max_length=160),
    ativo: bool | None = None,
    pagina: int = Query(1, ge=1),
    tamanho: int = Query(20, ge=1, le=100),
    actor: Professional = Depends(current_professional),
):
    with service_scope(actor) as service:
        return service.list_staff(search=busca, active=ativo, page=pagina, size=tamanho)


@router.post("/profissionais", response_model=StaffView, status_code=201)
def create_staff(data: StaffInput, actor: Professional = Depends(writer)):
    with service_scope(actor) as service:
        return service.save(data)


@router.get("/profissionais/{identifier}", response_model=StaffView)
def read_staff(identifier: UUID, actor: Professional = Depends(current_professional)):
    with service_scope(actor) as service:
        return service.read(str(identifier))


@router.patch("/profissionais/{identifier}", response_model=StaffView)
def update_staff(identifier: UUID, data: StaffInput, actor: Professional = Depends(writer)):
    with service_scope(actor) as service:
        return service.save(data, str(identifier))


@router.get("/profissionais/{identifier}/historico")
def staff_history(
    identifier: UUID,
    pagina: int = Query(1, ge=1),
    tamanho: int = Query(20, ge=1, le=100),
    actor: Professional = Depends(current_professional),
):
    with service_scope(actor) as service:
        return service.history(str(identifier), page=pagina, size=tamanho)


@router.get("/acoes/{action_id}/atribuicoes", response_model=AssignmentPage)
def action_assignments(
    action_id: UUID,
    pagina: int = Query(1, ge=1),
    tamanho: int = Query(20, ge=1, le=100),
    actor: Professional = Depends(current_professional),
):
    with service_scope(actor) as service:
        return service.list_assignments(str(action_id), page=pagina, size=tamanho)


@router.post("/acoes/{action_id}/atribuicoes", response_model=AssignmentView, status_code=201)
def assign_staff(action_id: UUID, data: AssignmentInput, actor: Professional = Depends(writer)):
    with service_scope(actor) as service:
        return service.assign(str(action_id), data)


@router.get("/acoes/{action_id}/atribuicoes/{identifier}/historico")
def assignment_history(
    action_id: UUID,
    identifier: UUID,
    pagina: int = Query(1, ge=1),
    tamanho: int = Query(20, ge=1, le=100),
    actor: Professional = Depends(current_professional),
):
    with service_scope(actor) as service:
        return service.assignment_history(
            str(action_id), str(identifier), page=pagina, size=tamanho
        )


@router.patch("/acoes/{action_id}/atribuicoes/{identifier}", response_model=AssignmentView)
def update_assignment(
    action_id: UUID, identifier: UUID, data: AssignmentUpdate, actor: Professional = Depends(writer)
):
    with service_scope(actor) as service:
        return service.assign(str(action_id), data, str(identifier))
