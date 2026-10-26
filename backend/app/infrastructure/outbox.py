from datetime import UTC, datetime, timedelta

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.domain.contracts import Summary
from app.infrastructure.database import get_engine
from app.infrastructure.models import Outbox


def dispatch_pending() -> dict[str, int]:
    """Worker explícito. Só entrega após ACK do event_id e da versão do contrato."""
    config = get_settings()
    if not config.agenda_summaries_url or not config.agenda_service_token.get_secret_value():
        return {"entregues": 0, "pendentes_configuracao": 1}
    if not config.agenda_summaries_url.startswith("https://"):
        raise RuntimeError("Integração exige HTTPS.")
    delivered = 0
    # Um worker por armazenamento SQLite. PostgreSQL exige SKIP LOCKED na homologação.
    with Session(get_engine()) as session, session.begin():
        rows = session.scalars(
            select(Outbox)
            .where(
                Outbox.status != "entregue",
                Outbox.tentativas < 10,
                Outbox.proxima_tentativa <= datetime.now(UTC),
            )
            .order_by(Outbox.proxima_tentativa)
            .limit(25)
        ).all()
        with httpx.Client(timeout=10, follow_redirects=False) as client:
            for row in rows:
                row.tentativas += 1
                try:
                    payload = Summary.model_validate(row.payload).model_dump(mode="json")
                    response = client.post(
                        config.agenda_summaries_url,
                        json=payload,
                        headers={
                            "Authorization": "Bearer "
                            + config.agenda_service_token.get_secret_value(),
                            "Idempotency-Key": row.idempotency_key,
                        },
                    )
                    response.raise_for_status()
                    ack = response.json()
                    if (
                        ack.get("event_id") != row.id
                        or ack.get("schema_version") != "1.0"
                        or ack.get("status") not in {"accepted", "duplicate"}
                    ):
                        raise ValueError("ACK_INVALIDO")
                    row.status, row.enviado_em, row.erro = "entregue", datetime.now(UTC), None
                    delivered += 1
                except (httpx.HTTPError, ValueError):
                    row.status = "falha" if row.tentativas >= 10 else "pendente"
                    row.erro = "AGENDA_SEM_CONFIRMACAO"
                    row.proxima_tentativa = datetime.now(UTC) + timedelta(
                        seconds=min(3600, 30 * 2**row.tentativas)
                    )
    return {"entregues": delivered}


if __name__ == "__main__":
    print(dispatch_pending())
