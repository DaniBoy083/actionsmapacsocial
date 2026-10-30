"""Exercise the Git privacy gate with disposable repositories and synthetic files."""

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/check_staged_privacy.py"


@pytest.mark.parametrize(
    ("relative_path", "blocked"),
    [
        ("docs/decisoes.md", False),
        (".env.example", False),
        ("docs/references/FICHA SINTÉTICA.xlsx", True),
        ("docs/references/SOURCE.XLSX", True),
        ("docs/references/ficha.csv", True),
        ("docs/data/nested/manifesto.json", True),
        ("backend/private/cadastro.json", True),
        (".env.local", True),
    ],
)
def test_privacy_gate_checks_staged_and_tracked_sources(tmp_path, relative_path, blocked):
    subprocess.run(["git", "init", "--quiet", str(tmp_path)], check=True, capture_output=True)
    (tmp_path / "scripts").mkdir()
    shutil.copyfile(SCRIPT, tmp_path / "scripts/check_staged_privacy.py")
    target = tmp_path / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("SYNTHETIC_FIXTURE=example\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "--", relative_path], cwd=tmp_path, check=True, capture_output=True
    )
    for flags in [[], ["--tracked"]]:
        result = subprocess.run(
            [sys.executable, "scripts/check_staged_privacy.py", *flags],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == int(blocked), result.stderr
        assert ("PRIVACY_ERRO" if blocked else "PRIVACY_OK") in result.stdout
        assert "SYNTHETIC_FIXTURE" not in result.stdout


def test_privacy_gate_blocks_secret_without_echoing_it(tmp_path):
    subprocess.run(["git", "init", "--quiet", str(tmp_path)], check=True, capture_output=True)
    (tmp_path / "scripts").mkdir()
    shutil.copyfile(SCRIPT, tmp_path / "scripts/check_staged_privacy.py")
    secret = "synthetic-secret-only-for-this-test"
    (tmp_path / ".env.local").write_text(f"SESSION_SECRET={secret}\n", encoding="utf-8")
    (tmp_path / "example.md").write_text(secret, encoding="utf-8")
    subprocess.run(["git", "add", "example.md"], cwd=tmp_path, check=True, capture_output=True)
    result = subprocess.run(
        [sys.executable, "scripts/check_staged_privacy.py"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert "PRIVACY_ERRO" in result.stdout
    assert secret not in result.stdout + result.stderr
