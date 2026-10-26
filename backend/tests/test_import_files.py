import hashlib
import json
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pymupdf
import pytest
from app.infrastructure.import_files import CHUNK_SIZE
from app.infrastructure.models import Beneficiary, ImportBatch, ImportChunk, ImportDocument
from sqlalchemy import func, select
from sqlalchemy.orm import Session


def start(client, content, kind="csv", **changes):
    response = client.post(
        "/api/v1/importacoes/arquivos",
        json={
            "formato": kind,
            "tamanho": len(content),
            "hash_arquivo": hashlib.sha256(content).hexdigest(),
            **changes,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def upload(client, content, kind="csv"):
    identifier = start(client, content, kind)
    for index, offset in enumerate(range(0, len(content), CHUNK_SIZE)):
        response = client.put(
            f"/api/v1/importacoes/{identifier}/partes/{index}",
            content=content[offset : offset + CHUNK_SIZE],
            headers={"Content-Type": "application/octet-stream"},
        )
        assert response.status_code == 200, response.text
    return identifier, client.post(f"/api/v1/importacoes/{identifier}/preparar", json={})


def pdf(active=False):
    with pymupdf.open() as document:
        page = document.new_page()
        page.insert_text((60, 80), "FICHA SINTETICA")
        if active:
            document.xref_set_key(
                document.pdf_catalog(), "OpenAction", "<< /S /JavaScript /JS (x) >>"
            )
        return document.tobytes()


def test_csv_upload_private_review_commit_idempotency_and_removal(authenticated, monkeypatch):
    client, engine, _ = authenticated
    content = (
        "nome;municipio_residencia_ibge\nPessoa Sintética;2508901\nPessoa Sintética;\n".encode()
    )
    identifier, response = upload(client, content)
    assert response.status_code == 200, response.text
    preview = response.json()
    assert preview["paginas"] == 2 and preview["possiveis_duplicidades"] == [2]
    assert not preview["registros"][0]["revisado"]
    with Session(engine) as session:
        assert session.scalar(select(func.count()).select_from(Beneficiary)) == 0
        document = session.get(ImportDocument, identifier)
        assert "Pessoa" not in document.conteudo_cifrado
        assert session.scalar(select(func.count()).select_from(ImportChunk)) == 0
    action = client.post(
        "/api/v1/acoes", json={"nome": "Ação sintética", "locais": [{"municipio_ibge": "2508901"}]}
    ).json()
    data = {
        "acao_id": action["id"],
        "importacao_id": identifier,
        "registros": [{**preview["registros"][0], "revisado": True}],
    }
    monkeypatch.setattr("app.api.routes.get_settings", lambda: SimpleNamespace(production=True))
    assert client.post("/api/v1/importacoes/confirmar", json=data).status_code == 422
    data["confirmacao_producao"] = True
    result = client.post("/api/v1/importacoes/confirmar", json=data)
    assert result.status_code == 200, result.text
    assert result.json() == {"incluidos": 1, "existentes": 0, "pendentes": 1}
    assert client.post("/api/v1/importacoes/confirmar", json=data).json()["existentes"] == 1
    assert client.delete(f"/api/v1/importacoes/{identifier}").status_code == 204
    assert client.get(f"/api/v1/importacoes/{identifier}").status_code == 404
    with Session(engine) as session:
        assert session.scalar(select(func.count()).select_from(Beneficiary)) == 1


def test_pdf_preview_can_rotate_and_rejects_active_or_fake_pdf(authenticated):
    client, _, _ = authenticated
    identifier, response = upload(client, pdf(), "pdf")
    assert response.status_code == 200, response.text
    assert response.json()["paginas"] == 1 and response.json()["registros"] == []
    for rotation in (0, 90, 180, 270):
        page = client.get(f"/api/v1/importacoes/{identifier}/paginas/1?rotacao={rotation}")
        assert page.status_code == 200 and page.headers["content-type"] == "image/jpeg"
        assert page.content.startswith(b"\xff\xd8") and page.headers["cache-control"] == "no-store"
    assert client.get(f"/api/v1/importacoes/{identifier}/paginas/1?rotacao=45").status_code == 422
    assert upload(client, pdf(active=True), "pdf")[1].status_code == 422
    assert upload(client, b"not-a-pdf", "pdf")[1].status_code == 422


@pytest.mark.parametrize(
    "content,kind",
    [
        (b"nome;cpf\nPessoa teste;private-value", "csv"),
        (b"nome;nome\nPessoa;Pessoa", "csv"),
        (b"nome;municipio_residencia_ibge\nPessoa;9999999", "csv"),
        (b'{"nome":"Pessoa teste"}', "json"),
        (b'[{"nome":"Pessoa teste", "receita":"private-value"}]', "json"),
        (b"nome\n" + b"Pessoa\n" * 201, "csv"),
    ],
)
def test_invalid_structured_files_are_rejected_without_echoing_pii(authenticated, content, kind):
    client, _, _ = authenticated
    _, response = upload(client, content, kind)
    assert response.status_code == 422
    assert "private-value" not in response.text


def test_binary_chunk_roundtrip_integrity_and_conflicting_retry(authenticated):
    client, _, _ = authenticated
    content = json.dumps([{"nome": "Pessoa " + "á" * 80}] * 200, ensure_ascii=False).encode()
    # Espaçamento JSON produz um arquivo com mais de uma parte, ainda com 200 registros.
    content = b" " * CHUNK_SIZE + content
    identifier = start(client, content, "json")
    first = content[:CHUNK_SIZE]
    url = f"/api/v1/importacoes/{identifier}/partes/0"
    headers = {"Content-Type": "application/octet-stream"}
    assert client.put(url, content=first, headers=headers).status_code == 200
    assert client.put(url, content=first, headers=headers).status_code == 200
    assert client.put(url, content=b"x" * len(first), headers=headers).status_code == 409
    assert client.post(f"/api/v1/importacoes/{identifier}/preparar", json={}).status_code == 409
    assert (
        client.put(
            f"/api/v1/importacoes/{identifier}/partes/1",
            content=content[CHUNK_SIZE:],
            headers=headers,
        ).status_code
        == 200
    )
    assert client.post(f"/api/v1/importacoes/{identifier}/preparar", json={}).status_code == 200


def test_owner_expiry_quota_and_csrf_are_enforced(authenticated):
    client, engine, repo = authenticated
    identifier, response = upload(client, b"nome\nPessoa de teste")
    assert response.status_code == 200
    with Session(engine) as session, session.begin():
        session.get(ImportBatch, identifier).autor_id = "other-professional"
    assert client.get(f"/api/v1/importacoes/{identifier}").status_code == 404
    with Session(engine) as session, session.begin():
        session.get(ImportBatch, identifier).autor_id = repo.professional.profissional_id
    with Session(engine) as session, session.begin():
        session.get(ImportDocument, identifier).expires_at = datetime.now(UTC) - timedelta(
            seconds=1
        )
    assert client.get(f"/api/v1/importacoes/{identifier}").status_code == 410
    start(client, b"nome\nOutra pessoa")
    with Session(engine) as session:
        assert session.get(ImportDocument, identifier) is None
    for _ in range(19):
        start(client, b"nome\nOutra pessoa")
    payload = {"formato": "csv", "tamanho": 10, "hash_arquivo": "a" * 64}
    assert client.post("/api/v1/importacoes/arquivos", json=payload).status_code == 429
    assert (
        client.post(
            "/api/v1/importacoes/arquivos", json=payload, headers={"X-CSRF-Token": "invalid"}
        ).status_code
        == 403
    )
