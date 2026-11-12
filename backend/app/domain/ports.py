from typing import Protocol

from app.domain.contracts import ActionInput, BeneficiaryUpdate, Professional
from app.domain.staff import AssignmentInput, AssignmentUpdate, StaffInput


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


class StaffRepository(Protocol):
    def assignment_history(
        self, action_id: str, identifier: str, actor: Professional, *, page: int, size: int
    ) -> dict: ...
    def list_staff(
        self, actor: Professional, *, search: str, active: bool | None, page: int, size: int
    ) -> dict: ...
    def read(self, identifier: str, actor: Professional) -> dict: ...
    def history(self, identifier: str, actor: Professional, *, page: int, size: int) -> dict: ...
    def save(
        self, data: StaffInput, actor: Professional, identifier: str | None = None
    ) -> dict: ...
    def list_assignments(
        self, action_id: str, actor: Professional, *, page: int, size: int
    ) -> dict: ...
    def assign(
        self,
        action_id: str,
        data: AssignmentInput | AssignmentUpdate,
        actor: Professional,
        identifier: str | None = None,
    ) -> dict: ...
