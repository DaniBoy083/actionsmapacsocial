"""Expurga arquivos temporários expirados; mantém ações, beneficiários e auditoria."""

import os
import sys
from pathlib import Path

from dotenv import dotenv_values
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.config import get_settings
from app.infrastructure.database import get_engine
from app.infrastructure.import_files import purge_expired
from app.infrastructure.models import Audit


def main():
    for key, value in dotenv_values(ROOT / "artifacts/production-config.env").items():
        if value is not None:
            os.environ[key] = value
    get_settings.cache_clear()
    with Session(get_engine()) as session, session.begin():
        count = purge_expired(session)
        if count:
            session.add(Audit(profissional_id="system:expiry", operacao="importacoes.expire", entidade_id="temporary-files"))
    print(f"EXPURGO_OK: {count} arquivo(s) temporário(s) expirado(s).")


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001 -- fronteira operacional sem dados em mensagens.
        print("EXPURGO_INDISPONIVEL: credenciais e dados omitidos.")
        raise SystemExit(1) from None
