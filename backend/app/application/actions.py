from app.domain.contracts import ActionInput, Professional
from app.domain.ports import ActionRepository


class ActionService:
    """Casos de uso dependem de portas; transação/auditoria/outbox pertencem ao adaptador."""

    def __init__(self, repository: ActionRepository):
        self.repository = repository

    def save(
        self, data: ActionInput, professional: Professional, identifier: str | None = None
    ) -> dict:
        if not professional.allowed:
            raise PermissionError("Perfil não autorizado.")
        return self.repository.save(data, professional, identifier)

    def transition(
        self, identifier: str, version: int, target: str, professional: Professional
    ) -> dict:
        if not professional.allowed:
            raise PermissionError("Perfil não autorizado.")
        return self.repository.transition(identifier, version, target, professional)
