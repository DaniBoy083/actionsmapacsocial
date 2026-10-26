"""Parser isolado: somente metadados ou PNG; não extrai/transmite dados pessoais."""

import re
import sys
from pathlib import Path

import pymupdf


def run() -> None:
    import json

    if sys.platform != "win32":
        import resource

        resource.setrlimit(resource.RLIMIT_AS, (1024 * 1024 * 1024, 1024 * 1024 * 1024))
        resource.setrlimit(resource.RLIMIT_CPU, (15, 15))

    with pymupdf.open(sys.argv[1]) as document:
        if document.is_encrypted or not 1 <= len(document) <= 200 or document.xref_length() > 20000:
            raise ValueError("PDF_INVALIDO")
        active = any(
            re.search(
                r"/(JavaScript|JS|OpenAction|AA|Launch|RichMedia|EmbeddedFiles)\b",
                document.xref_object(index),
            )
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
        rotation = int(sys.argv[4]) if len(sys.argv) > 4 else 0
        if rotation not in {0, 90, 180, 270}:
            raise ValueError("ROTACAO_INVALIDA")
        pix = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale).prerotate(rotation), alpha=False)
        output = "jpeg" if Path(sys.argv[3]).suffix == ".jpg" else "png"
        Path(sys.argv[3]).write_bytes(pix.tobytes(output, jpg_quality=80))


if __name__ == "__main__":
    try:
        run()
    except Exception:  # noqa: BLE001 -- fronteira do parser: nunca refletir dados da ficha.
        print("PDF_INVALIDO", file=sys.stderr)
        sys.exit(1)
