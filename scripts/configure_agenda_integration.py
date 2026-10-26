"""Provisiona credencial exclusiva do resumo, sem imprimir segredo ou alterar contas."""

import hashlib
import json
import secrets
import shutil
import subprocess
from pathlib import Path

from dotenv import dotenv_values, set_key

ROOT = Path(__file__).resolve().parents[1]
AGENDA_PROJECT = "prj_lKBMccjvQAMWdWCfWArqOum8vbNc"
TEAM = "team_BZDIfdem8wKcHqtNm6ZawZme"
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
    source = ROOT / "artifacts/agenda-receiver-source"
    link = source / ".vercel/project.json"
    link.parent.mkdir(parents=True, exist_ok=True)
    link.write_text(json.dumps({"projectId": AGENDA_PROJECT, "orgId": TEAM}), encoding="utf-8")
    for cwd, key, value, sensitive in [
        (source, "ACTIONS_MAP_TOKEN_SHA256", hashlib.sha256(token.encode()).hexdigest(), True),
        (ROOT, "AGENDA_SUMMARIES_URL", AGENDA_URL, False),
        (ROOT, "AGENDA_SERVICE_TOKEN", token, True),
    ]:
        args = [cli, "env", "add", key, "production", "--non-interactive"]
        if sensitive:
            args.append("--sensitive")
        result = subprocess.run(
            args, check=False, input=value.encode(), capture_output=True, cwd=cwd, timeout=45
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
