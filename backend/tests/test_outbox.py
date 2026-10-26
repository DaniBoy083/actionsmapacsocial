import httpx
import pytest
from app.config import get_settings
from app.infrastructure.models import Outbox
from app.infrastructure.outbox import dispatch_pending
from sqlalchemy import select
from sqlalchemy.orm import Session
from test_actions import create


@pytest.mark.parametrize("scenario", ["accepted", "duplicate", "invalid_ack", "unavailable"])
def test_delivery_requires_ack_and_retries_safely(authenticated, monkeypatch, scenario):
    client, engine, _ = authenticated
    create(client)
    monkeypatch.setenv(
        "AGENDA_SUMMARIES_URL", "https://agenda.example.invalid/api/integracoes/v1/acoes/resumos"
    )
    monkeypatch.setenv("AGENDA_SERVICE_TOKEN", "synthetic-service-token")
    get_settings.cache_clear()
    monkeypatch.setattr("app.infrastructure.outbox.get_engine", lambda: engine)
    seen = []

    def handler(request):
        seen.append(request)
        event = __import__("json").loads(request.content)
        if scenario == "unavailable":
            return httpx.Response(503)
        return httpx.Response(
            200,
            json={
                "status": scenario,
                "event_id": event["event_id"] if scenario != "invalid_ack" else "wrong",
                "schema_version": "1.0",
            },
        )

    original_client = httpx.Client
    monkeypatch.setattr(
        "app.infrastructure.outbox.httpx.Client",
        lambda **kwargs: original_client(transport=httpx.MockTransport(handler), **kwargs),
    )
    result = dispatch_pending()
    good = scenario in {"accepted", "duplicate"}
    assert result["entregues"] == int(good)
    assert seen[0].headers["idempotency-key"]
    with Session(engine) as session:
        row = session.scalar(select(Outbox))
        assert row.status == ("entregue" if good else "pendente")
        assert row.tentativas == 1
        assert row.erro is None if good else row.erro == "AGENDA_SEM_CONFIRMACAO"
    # Entregas não se repetem; falhas aguardam o backoff.
    assert dispatch_pending()["entregues"] == 0
    assert len(seen) == 1
