"""Arquivos temporários cifrados; nenhum objeto público ou OCR externo."""

import csv
import hashlib
import io
import json
import math
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.domain.contracts import BeneficiaryInput, Professional, normalize
from app.infrastructure.actions import cipher
from app.infrastructure.imports import worker
from app.infrastructure.models import ImportBatch, ImportChunk, ImportDocument

MAX_FILE = 8 * 1024 * 1024
CHUNK_SIZE = 512 * 1024
MAX_OPERATOR_BYTES = 32 * 1024 * 1024
MAX_TOTAL_BYTES = 256 * 1024 * 1024


def purge_expired(session: Session) -> int:
    ids = select(ImportDocument.id).where(ImportDocument.expires_at <= datetime.now(UTC))
    session.execute(delete(ImportChunk).where(ImportChunk.documento_id.in_(ids)))
    removed = session.execute(delete(ImportDocument).where(ImportDocument.id.in_(ids)))
    return removed.rowcount


def document_for(
    session: Session, identifier: str, professional: Professional, *, ready: bool = True
) -> tuple[ImportBatch, ImportDocument]:
    row = session.execute(
        select(ImportBatch, ImportDocument)
        .join(ImportDocument, ImportDocument.id == ImportBatch.id)
        .where(ImportBatch.id == identifier, ImportBatch.autor_id == professional.profissional_id)
        .with_for_update()
    ).first()
    if not row:
        raise HTTPException(404, "Arquivo não encontrado ou já removido.")
    batch, document = row
    if document.expires_at.replace(tzinfo=UTC) <= datetime.now(UTC):
        raise HTTPException(410, "Arquivo expirado. Selecione o arquivo novamente.")
    if ready and document.estado != "pronto":
        raise HTTPException(409, "Conclua o envio e a análise do arquivo.")
    return batch, document


def store_chunk(session: Session, document: ImportDocument, index: int, body: bytes) -> None:
    parts = math.ceil(document.tamanho / CHUNK_SIZE)
    expected = min(CHUNK_SIZE, document.tamanho - index * CHUNK_SIZE)
    if not 0 <= index < parts or len(body) != expected:
        raise HTTPException(422, "Parte do arquivo inválida ou incompleta.")
    if document.estado != "recebendo":
        raise HTTPException(409, "Este arquivo já foi preparado.")
    previous = session.get(ImportChunk, (document.id, index))
    if previous:
        if cipher().decrypt(previous.conteudo_cifrado.encode()) != body:
            raise HTTPException(409, "Parte já recebida com conteúdo diferente.")
        return
    session.add(
        ImportChunk(
            documento_id=document.id,
            indice=index,
            conteudo_cifrado=cipher().encrypt(body).decode(),
        )
    )


def structured_records(content: bytes, kind: str) -> list[dict]:
    try:
        source = content.decode("utf-8-sig")
        if kind == "json":
            rows = json.loads(source)
            if not isinstance(rows, list):
                raise ValueError("LISTA_ESPERADA")
        else:
            delimiter = ";" if ";" in source.partition("\n")[0] else ","
            reader = csv.DictReader(io.StringIO(source), delimiter=delimiter)
            if (
                not reader.fieldnames
                or len(reader.fieldnames) != len(set(reader.fieldnames))
                or not set(reader.fieldnames)
                <= set(BeneficiaryInput.model_fields) - {"local_indice"}
                or "nome" not in reader.fieldnames
            ):
                raise ValueError("CABECALHO_INVALIDO")
            rows = []
            for row in reader:
                rows.append(row)
                if len(rows) > 200:
                    raise ValueError("LIMITE_REGISTROS")
        if not 1 <= len(rows) <= 200:
            raise ValueError("LIMITE_REGISTROS")
        result = []
        for index, row in enumerate(rows, 1):
            if not isinstance(row, dict) or not set(row) <= set(BeneficiaryInput.model_fields) - {
                "local_indice"
            }:
                raise ValueError("CAMPOS_NAO_PERMITIDOS")
            row = {**row, "municipio_residencia_ibge": row.get("municipio_residencia_ibge") or None}
            row = {key: value if value != "" else None for key, value in row.items()}
            if kind == "csv" and row.get("recebimento_confirmado") is not None:
                receipt = row["recebimento_confirmado"].strip().lower()
                if receipt not in {"sim", "nao", "não"}:
                    raise ValueError("RECEBIMENTO_INVALIDO")
                row["recebimento_confirmado"] = receipt == "sim"
            data = BeneficiaryInput.model_validate(row)
            result.append({"pagina": index, **data.model_dump(), "revisado": False})
        return result
    except (ValueError, TypeError, csv.Error, UnicodeError, RecursionError):
        raise HTTPException(
            422,
            "Arquivo inválido. Use UTF-8, até 200 registros e os campos do modelo de cadastro, "
            "sem graus ou dados oculares.",
        ) from None


def analyze_pdf(content: bytes, page: int | None = None, rotation: int = 0):
    if not content.startswith(b"%PDF-"):
        raise HTTPException(422, "O conteúdo não corresponde a um PDF válido.")
    with tempfile.TemporaryDirectory(prefix="actions-import-") as directory:
        source = Path(directory) / "source.pdf"
        source.write_bytes(content)
        if page is None:
            return json.loads(worker(str(source)))["paginas"]
        output = Path(directory) / "page.jpg"
        worker(str(source), str(page), str(output), str(rotation))
        return output.read_bytes()


def finalize_file(session: Session, batch: ImportBatch, document: ImportDocument) -> None:
    if document.estado == "pronto":
        return
    chunks = session.scalars(
        select(ImportChunk)
        .where(ImportChunk.documento_id == document.id)
        .order_by(ImportChunk.indice)
    ).all()
    if [chunk.indice for chunk in chunks] != list(range(math.ceil(document.tamanho / CHUNK_SIZE))):
        raise HTTPException(409, "Envio incompleto. Reenvie as partes faltantes.")
    content = b"".join(cipher().decrypt(chunk.conteudo_cifrado.encode()) for chunk in chunks)
    if (
        len(content) != document.tamanho
        or hashlib.sha256(content).hexdigest() != batch.hash_arquivo
    ):
        raise HTTPException(422, "Falha na integridade do arquivo. Selecione-o novamente.")
    batch.paginas = (
        analyze_pdf(content)
        if document.formato == "pdf"
        else len(structured_records(content, document.formato))
    )
    document.conteudo_cifrado = cipher().encrypt(content).decode()
    document.estado = "pronto"
    session.execute(delete(ImportChunk).where(ImportChunk.documento_id == document.id))


def file_preview(batch: ImportBatch, document: ImportDocument) -> dict:
    rows = (
        []
        if document.formato == "pdf"
        else structured_records(
            cipher().decrypt(document.conteudo_cifrado.encode()), document.formato
        )
    )
    seen = set()
    duplicates = []
    for record in rows:
        key = normalize(record["nome"])
        if key in seen:
            duplicates.append(record["pagina"])
        seen.add(key)
    return {
        "id": batch.id,
        "formato": document.formato,
        "paginas": batch.paginas,
        "registros": rows,
        "possiveis_duplicidades": duplicates,
        "expira_em": document.expires_at,
    }
