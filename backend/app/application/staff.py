from app.domain.contracts import Professional
from app.domain.ports import StaffRepository
from app.domain.staff import AssignmentInput, AssignmentUpdate, StaffInput


class StaffService:
    def __init__(self, repository: StaffRepository, actor: Professional):
        if not actor.allowed:
            raise PermissionError("Cadastro de profissionais restrito à Administração/Tecnologia.")
        self.repository = repository
        self.actor = actor

    def list_staff(self, **filters) -> dict:
        return self.repository.list_staff(self.actor, **filters)

    def read(self, identifier: str) -> dict:
        return self.repository.read(identifier, self.actor)

    def history(self, identifier: str, **pagination) -> dict:
        return self.repository.history(identifier, self.actor, **pagination)

    def assignment_history(self, action_id: str, identifier: str, **pagination) -> dict:
        return self.repository.assignment_history(action_id, identifier, self.actor, **pagination)

    def save(self, data: StaffInput, identifier: str | None = None) -> dict:
        return self.repository.save(data, self.actor, identifier)

    def list_assignments(self, action_id: str, **pagination) -> dict:
        return self.repository.list_assignments(action_id, self.actor, **pagination)

    def assign(
        self,
        action_id: str,
        data: AssignmentInput | AssignmentUpdate,
        identifier: str | None = None,
    ) -> dict:
        return self.repository.assign(action_id, data, self.actor, identifier)
