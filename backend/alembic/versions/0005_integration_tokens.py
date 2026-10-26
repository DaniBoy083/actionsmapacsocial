"""Tokens de leitura e exportações agregadas; nenhuma alteração nas identidades."""

from alembic import op

revision = "0005_integration_tokens"
down_revision = "0004_remove_drafts"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE actions_map.acoes_map_credenciais_integracao (
      id varchar(36) PRIMARY KEY, nome varchar(80) NOT NULL,
      prefixo varchar(16) NOT NULL, sufixo varchar(4) NOT NULL,
      token_hash varchar(64) NOT NULL UNIQUE,
      escopo varchar(40) NOT NULL CHECK(escopo='acoes.resumos.read'),
      criado_por varchar(160) NOT NULL, criado_em timestamptz NOT NULL,
      expira_em timestamptz NOT NULL, revogado_em timestamptz, ultimo_uso_em timestamptz,
      chamadas integer NOT NULL CHECK(chamadas>=0), janela_minuto integer NOT NULL,
      chamadas_janela integer NOT NULL CHECK(chamadas_janela>=0)
    )""")
    op.execute("""CREATE TABLE actions_map.acoes_map_exportacoes_integracao (
      id varchar(36) PRIMARY KEY,
      credencial_id varchar(36) NOT NULL REFERENCES actions_map.acoes_map_credenciais_integracao(id),
      criado_em timestamptz NOT NULL, expira_em timestamptz NOT NULL, payload json NOT NULL
    )""")
    op.execute("""CREATE INDEX ix_acoes_map_exportacoes_integracao_credencial_id
      ON actions_map.acoes_map_exportacoes_integracao(credencial_id)""")
    op.execute("""CREATE INDEX ix_acoes_map_exportacoes_integracao_expira_em
      ON actions_map.acoes_map_exportacoes_integracao(expira_em)""")
    op.execute("""DO $$ BEGIN
      IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='ac_actions_map_runtime') THEN
        GRANT SELECT,INSERT,UPDATE ON actions_map.acoes_map_credenciais_integracao TO ac_actions_map_runtime;
        GRANT SELECT,INSERT,DELETE ON actions_map.acoes_map_exportacoes_integracao TO ac_actions_map_runtime;
      END IF;
    END $$""")


def downgrade():
    raise RuntimeError(
        "Preserve recibos e credenciais revogadas; restauração exige revisão e backup."
    )
