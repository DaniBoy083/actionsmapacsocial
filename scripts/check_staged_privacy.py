"""Refuse sensitive source files or known local secrets in the staged changes."""

import subprocess
import sys
from pathlib import Path

from dotenv import dotenv_values

root = Path(__file__).resolve().parents[1]
paths = (
    subprocess.check_output(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"], cwd=root
    )
    .decode()
    .splitlines()
)
bad_paths = [
    p
    for p in paths
    if (
        (Path(p).name.startswith(".env") and Path(p).name not in {".env.example", ".env.exemple"})
        or "/private/" in p
        or "/.venv/" in p
        or p.endswith((".sqlite3", ".pdf"))
        or p.startswith(("tmp/", "artifacts/"))
    )
]
if bad_paths:
    print("PRIVACY_ERRO: arquivo privado no staging.")
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
print("PRIVACY_OK: sem fontes privadas ou valores dos segredos locais no staging.")
