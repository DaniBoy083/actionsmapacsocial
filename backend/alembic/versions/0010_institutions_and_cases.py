"""Instituições reutilizáveis e designação explícita dos atendimentos; sem novo login."""

from alembic import op
from app.infrastructure.operational_grants import OPERATIONAL_GRANTS

revision = "0010_institutions_and_cases"
down_revision = "0009_clinical_fields"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE actions_map.acoes_map_designacoes_clinicas (
      participacao_id varchar(36) PRIMARY KEY REFERENCES actions_map.acoes_map_participacoes(id),
      profissional_id varchar(36) NOT NULL REFERENCES actions_map.acoes_map_profissionais(id),
      identidade_id varchar(160) NOT NULL, versao integer NOT NULL CHECK(versao>=1),
      ativo boolean NOT NULL, atualizado_por varchar(160) NOT NULL, atualizado_em timestamptz NOT NULL
    )""")
    op.execute("""INSERT INTO actions_map.acoes_map_designacoes_clinicas
      (participacao_id,profissional_id,identidade_id,versao,ativo,atualizado_por,atualizado_em)
      SELECT participacao_id,autor_profissional_id,autor_identidade_id,1,true,autor_identidade_id,atualizado_em
      FROM actions_map.acoes_map_fichas_clinicas""")
    op.execute(
        "CREATE INDEX ix_designacao_profissional ON actions_map.acoes_map_designacoes_clinicas(profissional_id)"
    )
    op.execute("""CREATE TABLE actions_map.acoes_map_instituicoes (
      id varchar(36) PRIMARY KEY, nome varchar(160) NOT NULL, nome_normalizado varchar(160) NOT NULL,
      tipo varchar(30) NOT NULL, aliases json NOT NULL,
      CONSTRAINT uq_instituicao_nome_tipo UNIQUE(nome_normalizado,tipo)
    )""")
    op.execute(
        "CREATE INDEX ix_instituicao_nome ON actions_map.acoes_map_instituicoes(nome_normalizado)"
    )
    op.execute("""CREATE TABLE actions_map.acoes_map_instituicoes_marcas (
      id varchar(36) PRIMARY KEY, instituicao_id varchar(36) NOT NULL REFERENCES actions_map.acoes_map_instituicoes(id),
      conteudo_base64 text NOT NULL, sha256 varchar(64) NOT NULL, largura integer NOT NULL,
      altura integer NOT NULL, origem varchar(40) NOT NULL, registrado_por varchar(160) NOT NULL,
      criado_em timestamptz NOT NULL
    )""")
    op.execute(
        "CREATE INDEX ix_instituicao_marca ON actions_map.acoes_map_instituicoes_marcas(instituicao_id)"
    )
    op.execute("""CREATE TABLE actions_map.acoes_map_acao_instituicoes (
      id varchar(36) PRIMARY KEY, acao_id varchar(36) NOT NULL REFERENCES actions_map.acoes_map_acoes(id),
      instituicao_id varchar(36) NOT NULL REFERENCES actions_map.acoes_map_instituicoes(id),
      papel varchar(15) NOT NULL, modalidade varchar(10), ordem integer NOT NULL, snapshot json NOT NULL,
      CONSTRAINT uq_acao_instituicao_papel UNIQUE(acao_id,instituicao_id,papel),
      CONSTRAINT ck_instituicao_papel CHECK(papel IN ('CONTRATANTE','APOIADOR')),
      CONSTRAINT ck_instituicao_modalidade CHECK((papel='CONTRATANTE' AND modalidade IS NULL) OR
        (papel='APOIADOR' AND modalidade IS NOT NULL AND modalidade IN ('TOTAL','PARCIAL')))
    )""")
    op.execute(
        "CREATE INDEX ix_acao_instituicao_acao ON actions_map.acoes_map_acao_instituicoes(acao_id)"
    )
    op.execute(
        "CREATE INDEX ix_acao_instituicao_instituicao ON actions_map.acoes_map_acao_instituicoes(instituicao_id)"
    )
    op.execute(OPERATIONAL_GRANTS)


def downgrade():
    raise RuntimeError(
        "Rollback por versão de código; preserve instituições, fichas e designações."
    )
