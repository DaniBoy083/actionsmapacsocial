"""Inicia frontend e backend descartáveis em loopback; Ctrl+C encerra ambos."""

import argparse
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frontend-port", type=int, default=3300)
    parser.add_argument("--backend-port", type=int, default=8300)
    args = parser.parse_args()
    ports = [args.frontend_port, args.backend_port]
    if len(set(ports)) != 2 or any(port < 1024 or port > 65535 for port in ports):
        parser.error("Escolha duas portas distintas entre 1024 e 65535.")
    if os.environ.get("APP_ENV", "").lower() == "production" or os.environ.get("VERCEL"):
        parser.error("Demonstração permitida somente localmente, fora de produção.")
    for port in ports:
        with socket.socket() as probe:
            try:
                probe.bind(("127.0.0.1", port))
            except OSError:
                parser.error(
                    f"Porta {port} ocupada. Escolha outra porta; nenhum processo foi encerrado."
                )
    node = shutil.which("node")
    next_cli = ROOT / "node_modules/next/dist/bin/next"
    if not node or not next_cli.is_file():
        parser.error("Instale Node.js e execute npm.cmd ci antes de iniciar.")
    # Não herdar credenciais, proxy, bindings ou opções de execução do ambiente do operador.
    environment = {
        key: value
        for key, value in os.environ.items()
        if key.upper()
        in {
            "PATH",
            "SYSTEMROOT",
            "SYSTEMDRIVE",
            "WINDIR",
            "COMSPEC",
            "PATHEXT",
            "USERPROFILE",
            "APPDATA",
            "LOCALAPPDATA",
            "TEMP",
            "TMP",
        }
    }
    environment.update(
        {
            "APP_ENV": "demo",
            "VERCEL": "",
            "ACTIONS_BACKEND_URL": "",
            "ACTIONS_API_URL": f"http://127.0.0.1:{args.backend_port}",
            "ACTIONS_LOCAL_DEMO": "1",
            "NEXT_TELEMETRY_DISABLED": "1",
            "PYTHONUTF8": "1",
            "ACTIONS_DATABASE_URL": "",
            "DATABASE_URL": "",
            "POSTGRES_DATABASE_URL": "",
            "POSTGRES_URL": "",
            "AGENDA_SERVICE_TOKEN": "",
            "AGENDA_SUMMARIES_URL": "",
        }
    )
    temporary = tempfile.TemporaryDirectory(prefix="actionsmap-demo-")
    commands = [
        [
            sys.executable,
            str(ROOT / "backend/demo.py"),
            "--port",
            str(args.backend_port),
            "--frontend-port",
            str(args.frontend_port),
            "--runtime-dir",
            temporary.name,
        ],
        [node, str(next_cli), "dev", "--hostname", "127.0.0.1", "--port", str(args.frontend_port)],
    ]
    print(f"\nDEMONSTRAÇÃO LOCAL: http://localhost:{args.frontend_port}", flush=True)
    print("Acessos fictícios: admin@demo.invalid ou tecnologia@demo.invalid", flush=True)
    print(f"Equipe da ação: http://localhost:{args.frontend_port}/acesso", flush=True)
    print("Acessos profissionais fictícios: oftalmo.demo, opto.demo e recepcao.demo", flush=True)
    print("Senha fictícia: Demonstracao-local-2026!", flush=True)
    print(
        "Use somente dados sintéticos. Ctrl+C encerra; reiniciar cria uma base limpa.\n", flush=True
    )
    children = []
    try:
        for command in commands:
            children.append(
                subprocess.Popen(
                    command,
                    cwd=ROOT,
                    env=environment,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                )
            )
        while all(child.poll() is None for child in children):
            time.sleep(0.25)
        print("Um servidor encerrou. Encerrando a demonstração.", flush=True)
        return next((child.returncode or 1 for child in children if child.poll() is not None), 1)
    except KeyboardInterrupt:
        return 0
    finally:
        for child in reversed(children):
            if child.poll() is None:
                if os.name == "nt":
                    subprocess.run(
                        ["taskkill", "/PID", str(child.pid), "/T", "/F"],
                        capture_output=True,
                        creationflags=subprocess.CREATE_NO_WINDOW,
                        check=False,
                    )
                else:
                    child.terminate()
                child.wait(timeout=10)
        temporary.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
