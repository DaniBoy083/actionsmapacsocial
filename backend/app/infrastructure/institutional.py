"""Marcas privadas e versões administrativas imutáveis, sem URLs de upload externas."""

import base64
import binascii
import hashlib
import io
import warnings

from fastapi import HTTPException
from PIL import Image, UnidentifiedImageError
from sqlalchemy.orm import Session

from app.domain.institutional import Institutional, InstitutionalInput
from app.infrastructure.models import ActionLogo, InstitutionalRevision

MAX_IMAGE_BYTES = 262144


def sanitize_logo(encoded: str) -> tuple[str, str, int, int]:
    try:
        raw = base64.b64decode(encoded, validate=True)
        if not raw or len(raw) > MAX_IMAGE_BYTES:
            raise ValueError
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(raw), formats=("PNG", "JPEG")) as image:
                width, height = image.size
                if not (64 <= width <= 2048 and 64 <= height <= 2048):
                    raise ValueError
                if getattr(image, "n_frames", 1) != 1:
                    raise ValueError
                image.load()
                # Nova imagem remove EXIF, comentários, perfis e conteúdo após o arquivo.
                clean = Image.new("RGBA", image.size)
                clean.paste(image.convert("RGBA"))
                output = io.BytesIO()
                clean.save(output, format="PNG")
        content = output.getvalue()
        if len(content) > MAX_IMAGE_BYTES:
            raise ValueError
    except (
        ValueError,
        OSError,
        SyntaxError,
        binascii.Error,
        UnidentifiedImageError,
        Image.DecompressionBombWarning,
        Image.DecompressionBombError,
    ):
        raise HTTPException(
            422, "Use PNG/JPEG estático de 64 a 2048 pixels por lado e até 256 KiB."
        ) from None
    return base64.b64encode(content).decode(), hashlib.sha256(content).hexdigest(), width, height


def persist_institutional(session: Session, action_id: str, data: InstitutionalInput) -> dict:
    result = data.model_dump(
        exclude={"governo": {"conteudo_base64"}, "clinica": {"conteudo_base64"}}
    )
    for slot in ("governo", "clinica"):
        brand = getattr(data, slot)
        if brand.conteudo_base64 is not None:
            encoded, digest, width, height = sanitize_logo(brand.conteudo_base64)
            logo = ActionLogo(
                acao_id=action_id,
                slot=slot,
                conteudo_base64=encoded,
                sha256=digest,
                largura=width,
                altura=height,
            )
            session.add(logo)
            session.flush()
            result[slot]["logo_id"] = logo.id
        elif brand.logo_id:
            logo = session.get(ActionLogo, brand.logo_id)
            if not logo or logo.acao_id != action_id or logo.slot != slot:
                raise HTTPException(422, "Marca não pertence a esta ação e posição.")
    return Institutional.model_validate(result).model_dump(mode="json")


def remember(session: Session, action_id: str, version: int, data: dict, actor: str) -> None:
    if session.get(InstitutionalRevision, (action_id, version)) is None:
        session.add(
            InstitutionalRevision(
                acao_id=action_id,
                versao=version,
                dados=Institutional.model_validate(data).model_dump(mode="json"),
                criado_por=actor,
            )
        )
