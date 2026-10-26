import math
from datetime import UTC, datetime, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import Field
from sqlalchemy import delete, func, select, text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.domain.contracts import Professional, StrictModel
from app.infrastructure.actions import audit
from app.infrastructure.database import get_engine
from app.infrastructure.import_files import (
    CHUNK_SIZE,
    MAX_FILE,
    MAX_OPERATOR_BYTES,
    MAX_TOTAL_BYTES,
    document_for,
    file_preview,
    finalize_file,
    purge_expired,
    store_chunk,
)
from app.infrastructure.models import ImportBatch, ImportChunk, ImportDocument
from app.security.session import current_professional, writer

router = APIRouter(prefix="/api/v1/importacoes")


class FileStart(StrictModel):
    formato: Literal["pdf", "csv", "json"]
    tamanho: int = Field(gt=0, le=MAX_FILE)
    hash_arquivo: str = Field(pattern=r"^[0-9a-f]{64}$")


@router.post("/arquivos", status_code=201)
def start_file(data: FileStart, professional: Professional = Depends(writer)):
    with Session(get_engine()) as session, session.begin():
        if session.bind.dialect.name == "postgresql":
            session.execute(text("SET LOCAL lock_timeout='5s'"))
            session.execute(text("SET LOCAL statement_timeout='20s'"))
            session.execute(
                text("SELECT pg_advisory_xact_lock(hashtext('actions_map.upload_quota'))")
            )
        purge_expired(session)
        total = session.scalar(select(func.coalesce(func.sum(ImportDocument.tamanho), 0)))
        own = session.execute(
            select(func.coalesce(func.sum(ImportDocument.tamanho), 0), func.count())
            .join(ImportBatch, ImportBatch.id == ImportDocument.id)
            .where(ImportBatch.autor_id == professional.profissional_id)
        ).one()
        if (
            own[0] + data.tamanho > MAX_OPERATOR_BYTES
            or own[1] >= 20
            or total + data.tamanho > MAX_TOTAL_BYTES
        ):
            raise HTTPException(
                429, "Limite de arquivos temporários atingido. Remova arquivos anteriores."
            )
        batch = ImportBatch(
            hash_arquivo=data.hash_arquivo, paginas=1, autor_id=professional.profissional_id
        )
        session.add(batch)
        session.flush()
        session.add(
            ImportDocument(
                id=batch.id,
                formato=data.formato,
                tamanho=data.tamanho,
                expires_at=datetime.now(UTC) + timedelta(hours=24),
            )
        )
        audit(session, professional, "importacoes.upload", batch.id)
        return {
            "id": batch.id,
            "tamanho_parte": CHUNK_SIZE,
            "partes": math.ceil(data.tamanho / CHUNK_SIZE),
        }


@router.put("/{identifier}/partes/{index}")
async def upload_chunk(
    identifier: str, index: int, request: Request, professional: Professional = Depends(writer)
):
    body = await request.body()
    if request.headers.get("content-type", "").split(";")[0] != "application/octet-stream":
        raise HTTPException(415, "Envie partes binárias do arquivo selecionado.")
    with Session(get_engine()) as session, session.begin():
        _, document = document_for(session, identifier, professional, ready=False)
        store_chunk(session, document, index, body)
    return {"recebida": index}


@router.post("/{identifier}/preparar")
def prepare_file(identifier: str, professional: Professional = Depends(writer)):
    with Session(get_engine()) as session, session.begin():
        batch, document = document_for(session, identifier, professional, ready=False)
        finalize_file(session, batch, document)
        audit(session, professional, "importacoes.preview", batch.id)
        return {**file_preview(batch, document), "producao": get_settings().production}


@router.get("/{identifier}")
def get_file(identifier: str, professional: Professional = Depends(current_professional)):
    with Session(get_engine()) as session, session.begin():
        batch, document = document_for(session, identifier, professional)
        audit(session, professional, "importacoes.read", batch.id)
        return {**file_preview(batch, document), "producao": get_settings().production}


@router.delete("/{identifier}", status_code=204)
def remove_file(identifier: str, professional: Professional = Depends(writer)):
    with Session(get_engine()) as session, session.begin():
        _, document = document_for(session, identifier, professional, ready=False)
        session.execute(delete(ImportChunk).where(ImportChunk.documento_id == document.id))
        session.delete(document)
        audit(session, professional, "importacoes.remove_file", identifier)
