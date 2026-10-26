"""Carga operacional assistida. O padrão é prévia, sem commit no banco.

O PDF e o manifesto nominal permanecem locais e fora do Git/deploy.
"""

import argparse
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

from cryptography.fernet import Fernet
from dotenv import dotenv_values
from sqlalchemy import inspect, select, text
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.config import get_settings
from app.infrastructure.database import get_engine
from app.infrastructure.historical_import import HistoricalManifest, import_history
from app.infrastructure.identity import IdentityRepository
from app.infrastructure.imports import file_hash
from app.infrastructure.models import Base


def backup_module(connection, key: str) -> Path:
    """Snapshot consistente somente das tabelas do módulo, cifrado antes de gravar."""
    snapshot = {
        table.name: [dict(row) for row in connection.execute(select(table)).mappings()]
        for table in Base.metadata.sorted_tables
        if inspect(connection).has_table(table.name, schema="actions_map")
    }
    plaintext = json.dumps(snapshot, ensure_ascii=False, default=str).encode()
    crypt = Fernet(key.encode())
    encrypted = crypt.encrypt(plaintext)
    if crypt.decrypt(encrypted) != plaintext:
        raise ValueError("Backup não passou na verificação de integridade.")
    directory = ROOT / "artifacts/private-import/backups"
    directory.mkdir(parents=True, exist_ok=True)
    dest = directory / (datetime.now(UTC).strftime("%Y%m%dT%H%M%S%f") + ".fernet")
    with dest.open("xb") as stream:
        stream.write(encrypted)
    if crypt.decrypt(dest.read_bytes()) != plaintext:
        raise ValueError("Backup gravado não corresponde ao snapshot.")
    return dest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--operator-email", required=True)
    parser.add_argument("--action-only", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm-production", action="store_true")
    args = parser.parse_args()

    manifest = HistoricalManifest.model_validate_json(
        args.manifest.read_text(encoding="utf-8")
    )
    if file_hash(args.source) != manifest.hash_arquivo:
        raise ValueError("O arquivo de origem não corresponde ao manifesto.")
    # O parser local não recebe conexões, segredos ou acesso a serviços externos.
    import pymupdf

    with pymupdf.open(args.source) as document:
        if len(document) != manifest.paginas:
            raise ValueError("Quantidade de páginas divergente.")

    for key, value in dotenv_values(ROOT / "artifacts/production-config.env").items():
        if value is not None:
            os.environ[key] = value
    get_settings.cache_clear()
    config = get_settings()
    if not config.production:
        raise ValueError(
            "Use a configuração restrita de produção preparada neste projeto."
        )
    if args.apply and not args.confirm_production:
        raise ValueError("Confirmação administrativa de produção ausente.")
    found = IdentityRepository().find(args.operator_email.strip().lower())
    if not found or not found[0].allowed:
        raise ValueError("Operador não autorizado.")
    professional, _digest = found
    engine = get_engine()
    backup = None
    with engine.connect() as connection, connection.begin():
        connection.execute(text("SET LOCAL lock_timeout='5s'"))
        connection.execute(text("SET LOCAL statement_timeout='30s'"))
        connection.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ"))
        if not connection.scalar(
            text("SELECT pg_try_advisory_xact_lock(hashtext(:source))"),
            {"source": "actions_map.import:" + manifest.hash_arquivo},
        ):
            raise ValueError("Outra carga desta fonte está em execução.")
        if args.apply:
            backup = backup_module(
                connection, config.beneficiaries_key.get_secret_value()
            )
        with Session(
            bind=connection, join_transaction_mode="create_savepoint"
        ) as session:
            result = import_history(
                session, manifest, professional, action_only=args.action_only
            )
            session.commit()
        if not args.apply:
            connection.rollback()
    print(
        json.dumps(
            {
                "modo": "aplicado" if args.apply else "previa_sem_gravacao",
                **result,
                "backup_verificado": backup is not None,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as error:  # noqa: BLE001 -- não exibir nomes, SQL ou credenciais.
        print(
            "IMPORTACAO_INTERROMPIDA: "
            + type(error).__name__
            + "; nenhum segredo exibido."
        )
        raise SystemExit(1) from None
