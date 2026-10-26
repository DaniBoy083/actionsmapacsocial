import json

import pytest
from app.infrastructure.actions import cipher
from app.infrastructure.historical_import import HistoricalManifest, import_history
from app.infrastructure.models import Action, Audit, Beneficiary, ImportBatch, Outbox, Participation
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.orm import Session


def manifest(**changes):
    return HistoricalManifest.model_validate(
        {
            "hash_arquivo": "b" * 64,
            "paginas": 3,
            "acao": {"nome": "Programa sintético", "locais": [{"municipio_ibge": "2508901"}]},
            "registros": [
                {"pagina": 1, "nome": "Pessoa sintética", "revisado": True},
                {"pagina": 2, "nome": "Pessoa sintética", "revisado": True},
            ],
            "pendencias": [{"pagina": 3, "motivo": "confirmar_grafia"}],
            **changes,
        }
    )


def count(session, model):
    return session.scalar(select(func.count()).select_from(model))


def test_historical_load_is_idempotent_encrypted_and_does_not_merge_names(api_client):
    _, engine, repo = api_client
    data = manifest()
    with Session(engine) as session, session.begin():
        result = import_history(session, data, repo.professional)
        assert result["incluidos"] == 2 and result["pendentes"] == 1
    with Session(engine) as session, session.begin():
        repeat = import_history(session, data, repo.professional)
        assert not repeat["acao_criada"] and repeat["existentes"] == 2
        assert count(session, Action) == 1
        assert count(session, Beneficiary) == count(session, Participation) == 2
        assert count(session, ImportBatch) == 1
        assert count(session, Outbox) == 2
        action = session.get(Action, data.action_id)
        assert action.status == "rascunho" and action.inicio_em is None
        for beneficiary in session.scalars(select(Beneficiary)):
            assert "Pessoa" not in beneficiary.dados_cifrados
            assert json.loads(cipher().decrypt(beneficiary.dados_cifrados.encode())) == {
                "id": beneficiary.id,
                "nome": "Pessoa sintética",
            }
        for message in session.scalars(select(Outbox)):
            assert "Pessoa" not in json.dumps(message.payload)
            assert message.payload["publicavel"] is False


def test_action_can_be_created_while_all_names_wait_for_review(api_client):
    _, engine, repo = api_client
    data = manifest()
    with Session(engine) as session, session.begin():
        result = import_history(session, data, repo.professional, action_only=True)
        assert result["acao_criada"] and result["pendentes"] == 3
    with Session(engine) as session, session.begin():
        result = import_history(session, data, repo.professional, action_only=True)
        assert not result["acao_criada"]
        assert count(session, Beneficiary) == count(session, ImportBatch) == 0
        assert count(session, Outbox) == count(session, Audit) == 1


def test_unreviewed_name_blocks_entire_load(api_client):
    _, engine, repo = api_client
    data = manifest()
    data.registros[1].revisado = False
    with pytest.raises(ValueError, match="Revise"), Session(engine) as session, session.begin():
        import_history(session, data, repo.professional)
    with Session(engine) as session:
        assert count(session, Action) == count(session, Beneficiary) == 0


@pytest.mark.parametrize(
    "changes",
    [
        {"pendencias": []},
        {"pendencias": [{"pagina": 2, "motivo": "confirmar_grafia"}]},
        {"pendencias": [{"pagina": 4, "motivo": "confirmar_grafia"}]},
        {"registros": [{"pagina": 1, "nome": "Pessoa teste", "cpf": "ignored", "revisado": True}]},
    ],
)
def test_manifest_rejects_unaccounted_duplicate_pages_and_unapproved_fields(changes):
    with pytest.raises(ValidationError):
        manifest(**changes)


def test_conflicting_reimport_rolls_back_new_page_and_preserves_original(api_client):
    _, engine, repo = api_client
    initial = manifest(
        registros=[{"pagina": 2, "nome": "Pessoa original", "revisado": True}],
        pendencias=[
            {"pagina": 1, "motivo": "confirmar_grafia"},
            {"pagina": 3, "motivo": "confirmar_grafia"},
        ],
    )
    with Session(engine) as session, session.begin():
        import_history(session, initial, repo.professional)
    changed = manifest()
    with pytest.raises(HTTPException), Session(engine) as session, session.begin():
        # Página 1 seria inserida antes do conflito da página 2.
        import_history(session, changed, repo.professional)
    with Session(engine) as session:
        assert count(session, Beneficiary) == count(session, Participation) == 1
        assert count(session, Outbox) == 2


def test_load_never_overwrites_manual_changes_or_creates_second_action(api_client):
    _, engine, repo = api_client
    data = manifest()
    with Session(engine) as session, session.begin():
        import_history(session, data, repo.professional, action_only=True)
        session.get(Action, data.action_id).nome = "Nome corrigido manualmente"
    with pytest.raises(ValueError, match="alterado"), Session(engine) as session, session.begin():
        import_history(session, data, repo.professional)
    with Session(engine) as session:
        assert count(session, Action) == 1 and count(session, Beneficiary) == 0


def test_unauthorized_operator_cannot_load(api_client):
    _, engine, repo = api_client
    repo.professional.equipe = "outro"
    with pytest.raises(PermissionError), Session(engine) as session, session.begin():
        import_history(session, manifest(), repo.professional)
