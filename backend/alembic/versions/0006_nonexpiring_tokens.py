"""Permite tokens sem prazo, preservando validade e revogação dos já existentes."""

from alembic import op

revision = "0006_nonexpiring_tokens"
down_revision = "0005_integration_tokens"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""ALTER TABLE actions_map.acoes_map_credenciais_integracao
      ALTER COLUMN expira_em DROP NOT NULL""")


def downgrade():
    raise RuntimeError("Não atribuir prazo ou revogar automaticamente tokens sem expiração.")
