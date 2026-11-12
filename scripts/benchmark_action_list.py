"""Baseline isolada, somente dados sintéticos em memória; não lê configuração/banco real."""

import json
import statistics
import sys
import time
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.infrastructure.models import Action, Base

from app.api import routes


def main():
    engine = create_engine("sqlite://", poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as session, session.begin():
        session.add_all(
            [
                Action(
                    nome=f"Acao sintetica {index}",
                    criado_por="benchmark",
                    locais=[{"municipio_ibge": "2507507", "nome_local": "Local"}],
                )
                for index in range(500)
            ]
        )
    routes.get_engine = lambda: engine
    statements = []
    event.listen(engine, "before_cursor_execute", lambda *args: statements.append(1))
    timings, counts = [], []
    for iteration in range(21):
        statements.clear()
        started = time.perf_counter()
        result = routes.list_actions(
            busca="",
            municipio="",
            status="",
            categoria="",
            inicio="",
            fim="",
            pagina=1,
            tamanho=20,
            filtros=dict.fromkeys(
                [
                    "instrumento",
                    "numero_instrumento",
                    "autor",
                    "orgao",
                    "clinica",
                    "apoio",
                ],
                "",
            ),
            _professional=None,
        )
        elapsed = (time.perf_counter() - started) * 1000
        assert result["total"] == 500 and len(result["items"]) == 20
        if iteration:
            timings.append(elapsed)
            counts.append(len(statements))
    print(
        json.dumps(
            {
                "scenario": "500 synthetic actions, page of 20, SQLite memory",
                "samples": len(timings),
                "median_ms": round(statistics.median(timings), 2),
                "p95_ms": round(sorted(timings)[18], 2),
                "queries_per_request": sorted(set(counts)),
            }
        )
    )
    engine.dispose()


if __name__ == "__main__":
    main()
