"""Gera contratos a partir dos DTOs executáveis, sem consultar banco ou segredos."""

import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "backend"))
from app.domain.contracts import Summary
from app.domain.integrations import ExportPage
from app.main import app

destination = root / "docs/contracts"
destination.mkdir(parents=True, exist_ok=True)
for filename, document in [
    ("actions-map.openapi.json", app.openapi()),
    ("agenda-summary.schema.json", Summary.model_json_schema()),
    ("integration-export.schema.json", ExportPage.model_json_schema()),
]:
    (destination / filename).write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
print("Contratos exportados sem acesso a dados.")
