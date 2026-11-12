"""Gera contratos a partir dos DTOs executáveis, sem consultar banco ou segredos."""

import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "backend"))
from app.domain.clinical import ClinicalDesignationInput, ClinicalInput
from app.domain.contracts import (
    ActionInput,
    BeneficiaryInput,
    BeneficiaryUpdate,
    Summary,
)
from app.domain.institutions import InstitutionInput
from app.domain.integrations import ExportPage
from app.domain.staff import AssignmentInput, AssignmentUpdate, StaffInput
from app.main import app

destination = root / "docs/contracts"
destination.mkdir(parents=True, exist_ok=True)
for filename, document in [
    ("actions-map.openapi.json", app.openapi()),
    ("action-registration.schema.json", ActionInput.model_json_schema()),
    ("staff-registration.schema.json", StaffInput.model_json_schema()),
    ("clinical-fields.schema.json", ClinicalInput.model_json_schema()),
    ("clinical-designation.schema.json", ClinicalDesignationInput.model_json_schema()),
    ("institution-registration.schema.json", InstitutionInput.model_json_schema()),
    ("staff-assignment.schema.json", AssignmentInput.model_json_schema()),
    ("staff-assignment-update.schema.json", AssignmentUpdate.model_json_schema()),
    ("agenda-summary.schema.json", Summary.model_json_schema()),
    ("integration-export.schema.json", ExportPage.model_json_schema()),
    ("beneficiary-registration.schema.json", BeneficiaryInput.model_json_schema()),
    ("beneficiary-update.schema.json", BeneficiaryUpdate.model_json_schema()),
]:
    (destination / filename).write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
print("Contratos exportados sem acesso a dados.")
