import json

import httpx
import pytest
from app.config import get_settings
from app.infrastructure.models import Action, Outbox
from app.infrastructure.outbox import dispatch_pending
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from test_actions import create


def test_publishing_sends_people_action_and_municipality_and_receives_ack(
    authenticated, monkeypatch
):
    client, engine, _ = authenticated
    monkeypatch.setenv(
        "AGENDA_SUMMARIES_URL", "https://agenda.example.invalid/api/integracoes/v1/acoes/resumos"
    )
    monkeypatch.setenv("AGENDA_SERVICE_TOKEN", "synthetic-service-only")
    get_settings.cache_clear()
    monkeypatch.setattr("app.infrastructure.outbox.get_engine", lambda: engine)
    received = []

    def receive(request):
        data = json.loads(request.content)
        received.append(data)
        assert request.headers["authorization"] == "Bearer synthetic-service-only"
        return httpx.Response(
            200, json={"event_id": data["event_id"], "schema_version": "1.1", "status": "accepted"}
        )

    original = httpx.Client
    monkeypatch.setattr(
        "app.infrastructure.outbox.httpx.Client",
        lambda **kwargs: original(transport=httpx.MockTransport(receive), **kwargs),
    )
    row = create(client, resumo_publico="Resumo institucional aprovado.")
    assert row["status"] == "em_revisao"
    url = "/api/v1/acoes/" + row["id"]
    assert client.post(url + "/publicar", json={"versao": 1}).status_code == 409
    assert client.post(url + "/beneficiarios", json={"nome": "Pessoa sintética"}).status_code == 201
    assert client.post(url + "/aprovar", json={"versao": 2}).status_code == 200
    response = client.post(url + "/publicar", json={"versao": 3})
    assert response.status_code == 200 and response.json()["status"] == "publicada"
    # O background da resposta só confirma após o ACK do receptor.
    current = client.get(url).json()
    assert current["integracao"]["status"] == "entregue"
    event = received[-1]
    assert event["quantidade_pessoas_contempladas"] == 1
    assert event["quantidade_acoes"] == 1
    assert set(event["municipios_ibge"]) == {"2507507", "2504009"}
    assert event["publicavel"] is True
    assert "Pessoa" not in json.dumps(event) and "nome" not in event
    changed = client.patch(
        url,
        json={
            "nome": "Ação corrigida",
            "locais": [
                {"municipio_ibge": place["municipio_ibge"], "nome_local": place["nome_local"]}
                for place in row["locais"]
            ],
            "versao": 4,
        },
    )
    assert changed.status_code == 200 and changed.json()["status"] == "em_revisao"
    assert received[-1]["publicavel"] is False


def test_removed_state_rejected_in_filter_and_database(authenticated):
    client, engine, _ = authenticated
    row = create(client)
    assert client.get("/api/v1/acoes", params={"status": "rascunho"}).status_code == 422
    with pytest.raises(IntegrityError), Session(engine) as session, session.begin():
        session.get(Action, row["id"]).status = "rascunho"


def test_pending_superseded_events_never_replace_latest_snapshot(authenticated, monkeypatch):
    client, engine, _ = authenticated
    row = create(client)
    client.patch(
        "/api/v1/acoes/" + row["id"],
        json={"nome": "Atualizada", "locais": [{"municipio_ibge": "2508901"}], "versao": 1},
    )
    monkeypatch.setenv(
        "AGENDA_SUMMARIES_URL", "https://agenda.example.invalid/api/integracoes/v1/acoes/resumos"
    )
    monkeypatch.setenv("AGENDA_SERVICE_TOKEN", "synthetic-service-only")
    get_settings.cache_clear()
    monkeypatch.setattr("app.infrastructure.outbox.get_engine", lambda: engine)
    sent = []
    original = httpx.Client

    def receive(request):
        data = json.loads(request.content)
        sent.append(data)
        return httpx.Response(
            200, json={"event_id": data["event_id"], "schema_version": "1.1", "status": "accepted"}
        )

    monkeypatch.setattr(
        "app.infrastructure.outbox.httpx.Client",
        lambda **kwargs: original(transport=httpx.MockTransport(receive), **kwargs),
    )
    assert dispatch_pending()["entregues"] == 1
    assert len(sent) == 1 and sent[0]["revisao"] == 2
    with Session(engine) as session:
        old = session.scalar(select(Outbox).where(Outbox.idempotency_key.endswith(":v1")))
        assert old.status == "substituido" and old.tentativas == 0
