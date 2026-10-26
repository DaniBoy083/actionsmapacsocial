from app.domain.contracts import Professional
from app.domain.integrations import CredentialInput, CredentialRepository


class CredentialService:
    def __init__(self, repository: CredentialRepository):
        self.repository = repository

    @staticmethod
    def authorize(professional: Professional) -> None:
        if not professional.allowed or professional.equipe != "tecnologia":
            raise PermissionError("Área exclusiva da equipe Tecnologia.")

    def create(self, data: CredentialInput, professional: Professional) -> dict:
        self.authorize(professional)
        return self.repository.create(data, professional)

    def revoke(self, identifier: str, professional: Professional) -> dict:
        self.authorize(professional)
        return self.repository.revoke(identifier, professional)

    def rotate(self, identifier: str, data: CredentialInput, professional: Professional) -> dict:
        self.authorize(professional)
        return self.repository.rotate(identifier, data, professional)
