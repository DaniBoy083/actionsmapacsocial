"""Cadastro administrativo e atribuições; nenhuma conta, senha ou campo de paciente."""

from alembic import op

from app.infrastructure.staff_grants import STAFF_GRANTS

revision = "0008_staff_assignments"
down_revision = "0007_institutional_metadata"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE actions_map.acoes_map_profissionais (
      id varchar(36) PRIMARY KEY, versao integer NOT NULL CHECK(versao>=1),
      nome varchar(160) NOT NULL, identidade_institucional_id varchar(160) UNIQUE,
      categoria varchar(20) NOT NULL CHECK(categoria IN ('MEDICO','OPTOMETRISTA','RECEPCAO')),
      registro_conselho varchar(40), registro_numero varchar(40), registro_uf varchar(2),
      rqe varchar(40), habilitacao_validada boolean NOT NULL,
      habilitacao_referencia varchar(200) NOT NULL, ativo boolean NOT NULL,
      registro_clinico_autorizado boolean NOT NULL, autorizacao_clinica_referencia varchar(200) NOT NULL,
      divulgacao_autorizada boolean NOT NULL, divulgacao_referencia varchar(200) NOT NULL,
      conferido_por varchar(160), conferido_em timestamptz,
      divulgacao_registrada_por varchar(160), divulgacao_registrada_em timestamptz,
      criado_por varchar(160) NOT NULL, criado_em timestamptz NOT NULL, atualizado_em timestamptz NOT NULL,
      CONSTRAINT uq_profissional_registro UNIQUE(registro_conselho,registro_numero,registro_uf)
    )""")
    op.execute(
        "CREATE INDEX ix_acoes_map_profissionais_ativo ON actions_map.acoes_map_profissionais(ativo)"
    )
    op.execute("""CREATE TABLE actions_map.acoes_map_atribuicoes (
      id varchar(36) PRIMARY KEY, versao integer NOT NULL CHECK(versao>=1),
      acao_id varchar(36) NOT NULL REFERENCES actions_map.acoes_map_acoes(id),
      profissional_id varchar(36) NOT NULL REFERENCES actions_map.acoes_map_profissionais(id),
      papel varchar(20) NOT NULL CHECK(papel IN ('PROFISSIONAL','RECEPCAO')),
      locais_indices json, locais_snapshot json, profissional_snapshot json NOT NULL,
      ativo boolean NOT NULL, criado_por varchar(160) NOT NULL,
      criado_em timestamptz NOT NULL, atualizado_em timestamptz NOT NULL,
      CONSTRAINT uq_atribuicao_acao_profissional UNIQUE(acao_id,profissional_id)
    )""")
    for column in ("acao_id", "profissional_id", "ativo"):
        op.execute(
            f"CREATE INDEX ix_acoes_map_atribuicoes_{column} ON actions_map.acoes_map_atribuicoes({column})"
        )
    op.execute("""CREATE TABLE actions_map.acoes_map_profissionais_historico (
      id varchar(36) PRIMARY KEY,
      tipo varchar(20) NOT NULL CHECK(tipo IN ('PROFISSIONAL','ATRIBUICAO')),
      entidade_id varchar(36) NOT NULL, versao integer NOT NULL,
      dados json NOT NULL, registrado_por varchar(160) NOT NULL, registrado_em timestamptz NOT NULL,
      CONSTRAINT uq_profissional_historico UNIQUE(tipo,entidade_id,versao)
    )""")
    op.execute(
        "CREATE INDEX ix_acoes_map_profissionais_historico_entidade_id ON actions_map.acoes_map_profissionais_historico(entidade_id)"
    )
    op.execute(STAFF_GRANTS)


def downgrade():
    raise RuntimeError(
        "Preserve cadastro, atribuições e histórico; rollback exige código compatível."
    )
