from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.application.beneficiaries import BeneficiaryService
from app.domain.contracts import BeneficiarySheet, BeneficiaryUpdate, Professional
from app.infrastructure.beneficiaries import SqlBeneficiariesRepository
from app.infrastructure.database import get_engine
from app.security.session import current_professional, writer

router = APIRouter(prefix="/api/v1/acoes/{action_id}/beneficiarios")


@router.get("/{person_id}", response_model=BeneficiarySheet)
def read_beneficiary(
    action_id: str, person_id: str, professional: Professional = Depends(current_professional)
):
    with Session(get_engine()) as session, session.begin():
        return BeneficiaryService(SqlBeneficiariesRepository(session)).read(
            action_id, person_id, professional
        )


@router.get("/{person_id}/segunda-via", response_model=BeneficiarySheet)
def second_copy(
    action_id: str, person_id: str, professional: Professional = Depends(current_professional)
):
    with Session(get_engine()) as session, session.begin():
        return BeneficiaryService(SqlBeneficiariesRepository(session)).read(
            action_id, person_id, professional, True
        )


@router.patch("/{person_id}", response_model=BeneficiarySheet)
def update_beneficiary(
    action_id: str,
    person_id: str,
    data: BeneficiaryUpdate,
    professional: Professional = Depends(writer),
):
    with Session(get_engine()) as session, session.begin():
        return BeneficiaryService(SqlBeneficiariesRepository(session)).update(
            action_id, person_id, data, professional
        )
