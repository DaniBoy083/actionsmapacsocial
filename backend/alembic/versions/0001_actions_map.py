"""Estrutura inicial isolada; nenhuma alteração nas tabelas institucionais."""

from pathlib import Path

from alembic import op

revision = "0001_actions_map"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    ddl = Path(__file__).with_suffix(".sql").read_text(encoding="utf-8")
    for statement in ddl.split(";"):
        if statement.strip():
            op.execute(statement)


def downgrade():
    raise RuntimeError(
        "Restauração exige backup revisado; remoção automática de dados está bloqueada."
    )
