"""Contas e sessões exclusivas do Actions Map, sem alteração da identidade AC."""

from alembic import op
from app.infrastructure.account_grants import ACCOUNT_GRANTS

revision = "0011_operational_accounts"
down_revision = "0010_institutions_and_cases"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE actions_map.acoes_map_contas_operacionais (
      id varchar(36) PRIMARY KEY,
      profissional_id varchar(36) NOT NULL UNIQUE REFERENCES actions_map.acoes_map_profissionais(id),
      usuario varchar(80) NOT NULL UNIQUE, senha_hash varchar(161) NOT NULL,
      ativo boolean NOT NULL, versao integer NOT NULL CHECK(versao>=1),
      atualizado_por varchar(160) NOT NULL, atualizado_em timestamptz NOT NULL
    )""")
    op.execute("""CREATE TABLE actions_map.acoes_map_sessoes_operacionais (
      token_hash varchar(64) PRIMARY KEY,
      conta_id varchar(36) NOT NULL REFERENCES actions_map.acoes_map_contas_operacionais(id),
      expires_at timestamptz NOT NULL
    )""")
    op.execute(
        "CREATE INDEX ix_sessao_operacional_conta ON actions_map.acoes_map_sessoes_operacionais(conta_id)"
    )
    op.execute(ACCOUNT_GRANTS)


def downgrade():
    raise RuntimeError(
        "Preserve contas, históricos e autoria. Desabilite o acesso operacional para reverter a funcionalidade."
    )
