"""Campos clínicos cifrados e versões privadas; ativação exige configuração e autorização."""

from alembic import op

from app.infrastructure.clinical_grants import CLINICAL_GRANTS

revision = "0009_clinical_fields"
down_revision = "0008_staff_assignments"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE actions_map.acoes_map_fichas_clinicas (
      id varchar(36) PRIMARY KEY,
      participacao_id varchar(36) NOT NULL UNIQUE REFERENCES actions_map.acoes_map_participacoes(id),
      autor_profissional_id varchar(36) NOT NULL REFERENCES actions_map.acoes_map_profissionais(id),
      autor_identidade_id varchar(160) NOT NULL,
      versao integer NOT NULL CHECK(versao>=1), dados_cifrados text NOT NULL, contexto json NOT NULL,
      criado_em timestamptz NOT NULL, atualizado_em timestamptz NOT NULL
    )""")
    op.execute(
        "CREATE INDEX ix_acoes_map_fichas_clinicas_autor_profissional_id ON actions_map.acoes_map_fichas_clinicas(autor_profissional_id)"
    )
    op.execute("""CREATE TABLE actions_map.acoes_map_fichas_clinicas_versoes (
      id varchar(36) PRIMARY KEY,
      ficha_id varchar(36) NOT NULL REFERENCES actions_map.acoes_map_fichas_clinicas(id),
      versao integer NOT NULL CHECK(versao>=1), dados_cifrados text NOT NULL,
      registrado_por varchar(160) NOT NULL, registrado_em timestamptz NOT NULL,
      CONSTRAINT uq_ficha_clinica_versao UNIQUE(ficha_id,versao)
    )""")
    op.execute(
        "CREATE INDEX ix_acoes_map_fichas_clinicas_versoes_ficha_id ON actions_map.acoes_map_fichas_clinicas_versoes(ficha_id)"
    )
    op.execute(CLINICAL_GRANTS)


def downgrade():
    raise RuntimeError(
        "Não apague registros de saúde ou versões no rollback; preserve dados e chave clínica."
    )
