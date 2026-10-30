"""Refuse private sources in Git and known local secrets in staged changes."""

import argparse
import subprocess
import sys
from pathlib import Path

from dotenv import dotenv_values

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--tracked", action="store_true", help="Check every tracked path, also in CI.")
args = parser.parse_args()
command = (
    ["git", "ls-files", "-z"]
    if args.tracked
    else ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z"]
)
paths = (
    subprocess.check_output(command, cwd=root).decode("utf-8").rstrip("\0").split("\0")
)
bad_paths = [
    p
    for p in paths
    if (
        (Path(p).name.startswith(".env") and Path(p).name not in {".env.example", ".env.exemple"})
        or "/private/" in p
        or "/.venv/" in p
        or p.lower().endswith((".sqlite3", ".pdf", ".log", ".xlsx", ".xls", ".xlsm", ".ods"))
        or p.lower().startswith(("tmp/", "artifacts/", "docs/data/"))
        or (
            p.lower().startswith(("docs/reference/", "docs/references/"))
            and p.lower().endswith((".csv", ".tsv"))
        )
    )
]
if bad_paths:
    print("PRIVACY_ERRO: arquivo privado no Git. Preserve a fonte fora do versionamento.")
    sys.exit(1)
diff = subprocess.check_output(["git", "diff", "--cached", "--no-ext-diff"], cwd=root)
config = {
    **dotenv_values(root / ".env"),
    **dotenv_values(root / ".env.local"),
    **dotenv_values(root / "artifacts/production-config.env"),
}
secrets = [
    value.encode()
    for name, value in config.items()
    if value
    and len(value) >= 12
    and any(
        token in name
        for token in [
            "SECRET",
            "PASSWORD",
            "KEY",
            "TOKEN",
            "DATABASE_URL",
            "POSTGRES_URL",
        ]
    )
]
if any(value in diff for value in secrets):
    print("PRIVACY_ERRO: possível segredo local no staging.")
    sys.exit(1)
print("PRIVACY_OK: caminhos verificados e sem valores dos segredos locais no staging.")
