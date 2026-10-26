"""Consulta delegada de autenticação; preserva RLS e os dados institucionais."""

from pathlib import Path

from alembic import op

revision = "0002_authentication_lookup"
down_revision = "0001_actions_map"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(Path(__file__).with_suffix(".sql").read_text(encoding="utf-8"))
    op.execute(
        "REVOKE ALL ON FUNCTION actions_map.authentication_identity(text, boolean) FROM PUBLIC"
    )


def downgrade():
    op.execute("DROP FUNCTION actions_map.authentication_identity(text, boolean)")
