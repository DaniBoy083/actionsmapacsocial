"""Complete only missing fields from a private reviewed manifest. Default: rollback."""

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

from dotenv import dotenv_values
from sqlalchemy import select, text
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.config import get_settings
from app.domain.contracts import Professional
from app.infrastructure.actions import cipher
from app.infrastructure.beneficiary_completion import CompletionManifest, complete_missing
from app.infrastructure.database import get_engine
from app.infrastructure.imports import file_hash
from app.infrastructure.models import Action, Outbox, Participation
from import_historical_pdf import backup_module


def operational_state(session, action_id):
    action = session.get(Action, action_id)
    if not action:
        raise ValueError("Ação de origem não encontrada.")
    data = {
        "acao": {column.name: getattr(action, column.name) for column in Action.__table__.columns},
        "participacoes": [
            tuple(row)
            for row in session.execute(
                select(
                    Participation.id,
                    Participation.beneficiario_id,
                    Participation.origem,
                    Participation.local_indice,
                )
                .where(Participation.acao_id == action_id)
                .order_by(Participation.id)
            )
        ],
        "outbox": [
            tuple(row)
            for row in session.execute(
                select(Outbox.id, Outbox.payload)
                .where(Outbox.idempotency_key.like("acao:" + action_id + ":%"))
                .order_by(Outbox.id)
            )
        ],
    }
    return hashlib.sha256(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--production-config", type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm-production", action="store_true")
    args = parser.parse_args()
    if args.production_config:
        for key, value in dotenv_values(args.production_config).items():
            if value is not None:
                os.environ[key] = value
    get_settings.cache_clear()
    config = get_settings()
    if not config.production or args.apply and not args.confirm_production:
        raise ValueError("Operação produtiva requer configuração e confirmação explícitas.")
    content = args.manifest.read_bytes()
    if args.manifest.suffix == ".fernet":
        content = cipher().decrypt(content)
    manifest = CompletionManifest.model_validate_json(content)
    if file_hash(args.source) != manifest.hash_arquivo:
        raise ValueError("Documento de origem divergente.")
    import pymupdf

    with pymupdf.open(args.source) as document:
        if len(document) != manifest.paginas:
            raise ValueError("Quantidade de páginas divergente.")
    # Explicit administrative actor, never a forged institutional employee/session.
    operator = Professional(
        profissional_id="operacao-assistida:complemento-pdf",
        nome="Operação assistida autorizada",
        tipo_login="administracao",
        equipe="tecnologia",
    )
    backup = None
    with get_engine().connect() as connection, connection.begin():
        connection.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ"))
        connection.execute(text("SET LOCAL lock_timeout='5s'"))
        connection.execute(text("SET LOCAL statement_timeout='30s'"))
        if not connection.scalar(
            text("SELECT pg_try_advisory_xact_lock(hashtext(:source))"),
            {"source": "actions_map.complete:" + manifest.hash_arquivo},
        ):
            raise ValueError("Outra complementação está em execução.")
        if args.apply:
            backup = backup_module(connection, config.beneficiaries_key.get_secret_value())
        with Session(bind=connection, join_transaction_mode="create_savepoint") as session:
            before = operational_state(session, manifest.acao_id)
            result = complete_missing(session, manifest, operator)
            session.flush()
            if operational_state(session, manifest.acao_id) != before:
                raise ValueError("Ação, participações ou resumos foram alterados; lote cancelado.")
            session.commit()
        if not args.apply:
            connection.rollback()
    print(
        json.dumps(
            {
                "modo": "aplicado" if args.apply else "previa_sem_gravacao",
                "backup_verificado": backup is not None,
                "acao_participacoes_e_resumos_preservados": True,
                **result,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as error:  # noqa: BLE001 -- private SQL and data never printed.
        print(json.dumps({"operacao_interrompida": type(error).__name__}))
        raise SystemExit(1) from None
