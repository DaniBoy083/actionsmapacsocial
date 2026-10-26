from typing import Protocol

from app.domain.contracts import ActionInput, Professional


class ActionRepository(Protocol):
    def save(
        self, data: ActionInput, professional: Professional, identifier: str | None = None
    ) -> dict: ...
    def transition(
        self, identifier: str, version: int, target: str, professional: Professional
    ) -> dict: ...
