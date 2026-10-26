"""Parser isolado: somente metadados ou PNG; não extrai/transmite dados pessoais."""

import sys
from pathlib import Path

import pymupdf


def run() -> None:
    import json

    with pymupdf.open(sys.argv[1]) as document:
        if document.is_encrypted or not 1 <= len(document) <= 200:
            raise ValueError("PDF_INVALIDO")
        active = any(
            "/JavaScript" in document.xref_object(index)
            or "/OpenAction" in document.xref_object(index)
            for index in range(1, document.xref_length())
        )
        if document.embfile_count() or active:
            raise ValueError("PDF_ATIVO")
        if len(sys.argv) == 2:
            print(json.dumps({"paginas": len(document)}))
            return
        page = document[int(sys.argv[2]) - 1]
        if page.rect.width * page.rect.height > 40_000_000:
            raise ValueError("PAGINA_EXCESSIVA")
        scale = min(1, 1400 / max(page.rect.width, page.rect.height))
        pix = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), alpha=False)
        Path(sys.argv[3]).write_bytes(pix.tobytes("png"))


if __name__ == "__main__":
    try:
        run()
    except Exception:  # noqa: BLE001 -- fronteira do parser: nunca refletir dados da ficha.
        print("PDF_INVALIDO", file=sys.stderr)
        sys.exit(1)
