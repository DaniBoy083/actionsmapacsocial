import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from fastapi import HTTPException

from app.config import ROOT, get_settings

SOURCE = ROOT / "docs/data/ilovepdf_merged.pdf"


def require_source() -> Path:
    if get_settings().production or not SOURCE.is_file():
        raise HTTPException(
            503, "Documento histórico indisponível. Storage privado aguarda configuração."
        )
    return SOURCE


def file_hash(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def worker(*args: str) -> str:
    environment = {
        key: value
        for key, value in os.environ.items()
        if key.upper()
        in {
            "SYSTEMROOT",
            "SYSTEMDRIVE",
            "WINDIR",
            "PATH",
            "TEMP",
            "TMP",
            "LANG",
        }
    }
    try:
        result = subprocess.run(
            [sys.executable, str(Path(__file__).with_name("pdf_worker.py")), *args],
            capture_output=True,
            timeout=20,
            env=environment,
            check=True,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        return result.stdout.decode()
    except (subprocess.SubprocessError, OSError):
        raise HTTPException(
            422, "Não foi possível analisar esta página. Solicite revisão do documento."
        ) from None


def metadata() -> tuple[str, int]:
    path = require_source()
    count = json.loads(worker(str(path)))["paginas"]
    return file_hash(path), count


def render_page(page: int) -> bytes:
    path = require_source()
    with tempfile.TemporaryDirectory(prefix="ac-actions-page-") as directory:
        output = Path(directory) / "page.png"
        worker(str(path), str(page), str(output))
        return output.read_bytes()
