from typing import Protocol

from app.domain.contracts import ActionInput, BeneficiaryUpdate, Professional


class ActionRepository(Protocol):
    def save(
        self, data: ActionInput, professional: Professional, identifier: str | None = None
    ) -> dict: ...
    def transition(
        self, identifier: str, version: int, target: str, professional: Professional
    ) -> dict: ...


class BeneficiaryRepository(Protocol):
    def read(
        self, action_id: str, person_id: str, professional: Professional, second_copy: bool
    ) -> dict: ...
    def update(
        self, action_id: str, person_id: str, data: BeneficiaryUpdate, professional: Professional
    ) -> dict: ...
