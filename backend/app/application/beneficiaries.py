from app.domain.contracts import BeneficiaryUpdate, Professional
from app.domain.ports import BeneficiaryRepository


class BeneficiaryService:
    def __init__(self, repository: BeneficiaryRepository):
        self.repository = repository

    def read(
        self, action_id: str, person_id: str, professional: Professional, second_copy: bool = False
    ) -> dict:
        if not professional.allowed:
            raise PermissionError("Perfil não autorizado.")
        return self.repository.read(action_id, person_id, professional, second_copy)

    def update(
        self, action_id: str, person_id: str, data: BeneficiaryUpdate, professional: Professional
    ) -> dict:
        if not professional.allowed:
            raise PermissionError("Perfil não autorizado.")
        return self.repository.update(action_id, person_id, data, professional)
