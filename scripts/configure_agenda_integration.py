"""Provisiona credencial exclusiva do resumo, sem imprimir segredo ou alterar contas."""

import hashlib
import secrets
import shutil
import subprocess
from pathlib import Path

from dotenv import dotenv_values, set_key

ROOT = Path(__file__).resolve().parents[1]
AGENDA_PROJECT = "prj_lKBMccjvQAMWdWCfWArqOum8vbNc"
MAP_PROJECT = "prj_bgoJYESb2U7PtZWIsvh6yL6aUqDM"
AGENDA_URL = "https://agenda-digital-ac-social.vercel.app/api/integracoes/v1/acoes/resumos"


def main():
    cli = shutil.which("vercel.cmd") or shutil.which("vercel")
    if not cli:
        raise RuntimeError("CLI ausente.")
    config = ROOT / "artifacts/production-config.env"
    current = dotenv_values(config)
    token = current.get("AGENDA_SERVICE_TOKEN") or secrets.token_hex(32)
    set_key(config, "AGENDA_SUMMARIES_URL", AGENDA_URL)
    set_key(config, "AGENDA_SERVICE_TOKEN", token)
    for project, key, value, sensitive in [
        (
            AGENDA_PROJECT,
            "ACTIONS_MAP_TOKEN_SHA256",
            hashlib.sha256(token.encode()).hexdigest(),
            True,
        ),
        (MAP_PROJECT, "AGENDA_SUMMARIES_URL", AGENDA_URL, False),
        (MAP_PROJECT, "AGENDA_SERVICE_TOKEN", token, True),
    ]:
        args = [
            cli,
            "env",
            "add",
            key,
            "production",
            "--project",
            project,
            "--force",
            "--non-interactive",
        ]
        if sensitive:
            args.append("--sensitive")
        result = subprocess.run(
            args, check=False, input=value.encode(), capture_output=True, cwd=ROOT, timeout=45
        )
        if result.returncode:
            raise RuntimeError("Variável não provisionada: " + key)
        print("INTEGRATION_ENV_OK: " + key)


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001 -- fronteira operacional sem valores secretos.
        print("INTEGRATION_CONFIG_FAILED: detalhes privados omitidos.")
        raise SystemExit(1) from None
