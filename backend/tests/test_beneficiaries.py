import json

import pytest
from app.domain.contracts import BeneficiaryData
from app.infrastructure.actions import cipher
from app.infrastructure.beneficiary_completion import CompletionManifest, complete_missing
from app.infrastructure.models import Audit, Beneficiary, ImportBatch, Outbox, Participation
from sqlalchemy import func, select
from sqlalchemy.orm import Session


def create(client, **values):
    action = client.post(
        "/api/v1/acoes", json={"nome": "Ação sintética", "locais": [{"municipio_ibge": "2508901"}]}
    ).json()
    base = f"/api/v1/acoes/{action['id']}/beneficiarios"
    assert client.post(base, json={"nome": "Pessoa Sintética", **values}).status_code == 201
    person = client.get(base).json()["items"][0]
    return base, person["id"], action["id"]


def sample():
    # Deliberately synthetic fixture, never copied from the scanned records.
    return {
        "cpf": "52998224725",
        "telefone": "83999990000",
        "data_nascimento": "2000-01-02",
        "data_ficha": "2026-09-17",
        "municipio_ficha_ibge": "2508901",
        "responsavel": "Responsável sintético",
        "observacoes": "Anotação geral sintética",
        "recebimento_confirmado": True,
    }


def test_complete_registration_is_private_encrypted_and_excluded_from_integration(authenticated):
    client, engine, _ = authenticated
    base, identifier, _ = create(client, **sample())
    listing = client.get(base)
    assert "cpf" not in listing.text and "telefone" not in listing.text
    result = client.get(base + "/" + identifier)
    assert result.status_code == 200
    assert result.headers["cache-control"] == "no-store"
    for key, value in sample().items():
        assert result.json()[key] == value
    with Session(engine) as session:
        encrypted = session.get(Beneficiary, identifier).dados_cifrados
        for value in ["52998224725", "83999990000", "2000-01-02", "Pessoa Sintética"]:
            assert value not in encrypted
        for event in session.scalars(select(Outbox)):
            assert not set(sample()).intersection(event.payload)


@pytest.mark.parametrize(
    "changes",
    [
        {"cpf": "11111111111"},
        {"cpf": "123"},
        {"cpf": "<script>"},
        {"telefone": "invasor"},
        {"telefone": "123"},
        {"data_nascimento": "2999-01-01"},
        {"data_ficha": "1990-01-01", "data_nascimento": "2000-01-01"},
        {"municipio_ficha_ibge": "9999999"},
        {"recebimento_confirmado": "sim"},
        {"observacoes": "x" * 1001},
        {"esferico": "+1"},
        {"cilindrico": "-1"},
        {"eixo": 90},
        {"dp": 60},
        {"adicao": 2},
        {"lentes": "private-marker"},
        {"olho_direito": "private-marker"},
        {"assinatura_base64": "private-marker"},
    ],
)
def test_invalid_or_ocular_data_is_rejected_without_echo(authenticated, changes):
    client, _, _ = authenticated
    action = client.post(
        "/api/v1/acoes", json={"nome": "Ação sintética", "locais": [{"municipio_ibge": "2508901"}]}
    ).json()
    result = client.post(
        f"/api/v1/acoes/{action['id']}/beneficiarios", json={"nome": "Pessoa Sintética", **changes}
    )
    assert result.status_code == 422
    assert "private-marker" not in result.text


def test_documentary_cpf_is_separate_from_validated_cpf_and_phone_does_not_invent_ddd(
    authenticated,
):
    client, _, _ = authenticated
    base, identifier, _ = create(client, cpf_documento="111.111.111-11", telefone="1234-5678")
    result = client.get(base + "/" + identifier).json()
    assert result["cpf"] is None and result["cpf_documento"] == "11111111111"
    assert result["telefone"] == "12345678"


def test_second_copy_is_restricted_audited_and_does_not_confirm_receipt(authenticated):
    client, engine, _ = authenticated
    base, identifier, _ = create(client)
    result = client.get(base + "/" + identifier + "/segunda-via")
    assert result.status_code == 200 and result.json()["segunda_via"] is True
    assert result.json()["emitido_em"] and result.json()["recebimento_confirmado"] is None
    assert client.get(base + "/wrong-person/segunda-via").status_code == 404
    with Session(engine) as session:
        event = session.scalar(select(Audit).where(Audit.operacao == "beneficiarios.segunda_via"))
        assert event.entidade_id == identifier
    assert client.post("/api/v1/auth/logout", json={}).status_code == 204
    assert client.get(base + "/" + identifier + "/segunda-via").status_code == 401


def test_edit_completes_legacy_registration_and_prevents_lost_updates(authenticated):
    client, engine, _ = authenticated
    base, identifier, _ = create(client)
    with Session(engine) as session, session.begin():
        session.get(Beneficiary, identifier).dados_cifrados = (
            cipher()
            .encrypt(json.dumps({"id": identifier, "nome": "Pessoa Sintética"}).encode())
            .decode()
        )
    original = client.get(base + "/" + identifier).json()
    assert original["versao"] == 1 and original["cpf"] is None
    values = {"nome": original["nome"], "versao": 1, **sample()}
    updated = client.patch(base + "/" + identifier, json=values)
    assert updated.status_code == 200 and updated.json()["versao"] == 2
    assert client.patch(base + "/" + identifier, json=values).status_code == 409
    assert (
        client.patch(
            base + "/" + identifier, json={**values, "versao": 2}, headers={"X-CSRF-Token": "wrong"}
        ).status_code
        == 403
    )


def test_registration_cannot_be_read_through_an_unrelated_action_and_revoked_profile(authenticated):
    client, _, identities = authenticated
    _, identifier, _ = create(client)
    other, _, _ = create(client)
    assert client.get(other + "/" + identifier).status_code == 404
    identities.professional.equipe = "outra"
    assert client.get(other + "/" + identifier + "/segunda-via").status_code == 403


def test_ciphertext_cannot_be_moved_to_another_beneficiary(authenticated):
    client, engine, _ = authenticated
    base, identifier, _ = create(client)
    with Session(engine) as session, session.begin():
        session.get(Beneficiary, identifier).dados_cifrados = (
            cipher().encrypt(b'{"id":"wrong","nome":"private-marker"}').decode()
        )
    result = client.get(base + "/" + identifier)
    assert result.status_code == 503 and "private-marker" not in result.text


def imported_record(client, engine, operator):
    action = client.post(
        "/api/v1/acoes",
        json={"nome": "Ação histórica sintética", "locais": [{"municipio_ibge": "2508901"}]},
    ).json()
    with Session(engine) as session, session.begin():
        batch = ImportBatch(hash_arquivo="b" * 64, paginas=2, autor_id=operator.profissional_id)
        session.add(batch)
        session.flush()
        batch_id = batch.id
    assert (
        client.post(
            "/api/v1/importacoes/confirmar",
            json={
                "importacao_id": batch_id,
                "acao_id": action["id"],
                "registros": [{"pagina": 1, "nome": "Pessoa Sintética", "revisado": True}],
            },
        ).status_code
        == 200
    )
    return action["id"]


def completion(action_id, **changes):
    return CompletionManifest.model_validate(
        {
            "acao_id": action_id,
            "hash_arquivo": "b" * 64,
            "paginas": 2,
            "registros": [{"pagina": 1, "revisado": True, "campos": sample()}],
            **changes,
        }
    )


def test_completion_by_exact_page_is_idempotent_and_preserves_existing_fields(authenticated):
    client, engine, identities = authenticated
    action_id = imported_record(client, engine, identities.professional)
    manifest = completion(action_id)
    with Session(engine) as session, session.begin():
        result = complete_missing(session, manifest, identities.professional)
        assert result["registros_atualizados"] == 1 and result["campos_preenchidos"]["cpf"] == 1
    with Session(engine) as session, session.begin():
        assert (
            complete_missing(session, manifest, identities.professional)["registros_atualizados"]
            == 0
        )
        manifest.registros[0].campos["telefone"] = "83988880000"
        conflict = complete_missing(session, manifest, identities.professional)
        assert conflict["registros_atualizados"] == 0 and conflict["conflitos_preservados"] == [
            {"pagina": 1, "campo": "telefone"}
        ]
        assert session.scalar(select(func.count()).select_from(Participation)) == 1
    assert client.get(f"/api/v1/acoes/{action_id}/beneficiarios").json()["total"] == 1


def test_missing_source_page_aborts_entire_completion_before_any_update(authenticated):
    client, engine, identities = authenticated
    action_id = imported_record(client, engine, identities.professional)
    manifest = completion(
        action_id,
        registros=[
            {"pagina": 1, "revisado": True, "campos": sample()},
            {"pagina": 2, "revisado": True, "campos": sample()},
        ],
    )
    with pytest.raises(ValueError), Session(engine) as session, session.begin():
        complete_missing(session, manifest, identities.professional)
    base = f"/api/v1/acoes/{action_id}/beneficiarios"
    identifier = client.get(base).json()["items"][0]["id"]
    assert client.get(base + "/" + identifier).json()["cpf"] is None


def test_full_csv_registration_roundtrips_and_rejects_ocular_extra_fields():
    from app.infrastructure.import_files import structured_records

    result = structured_records(
        b"nome;telefone;cpf;data_nascimento;data_ficha;municipio_ficha_ibge;recebimento_confirmado\nPessoa teste;12345678;52998224725;2000-01-02;2026-09-17;2508901;sim",
        "csv",
    )
    assert result[0]["cpf"] == "52998224725" and result[0]["recebimento_confirmado"] is True
    assert BeneficiaryData(nome="Pessoa teste").cpf_documento is None


def test_removed_map_has_no_backend_endpoint(api_client):
    client, _, _ = api_client
    assert client.get("/api/v1/mapa-acoes").status_code == 404
