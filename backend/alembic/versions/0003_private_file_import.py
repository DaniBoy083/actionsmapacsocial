"""Armazenamento temporário cifrado de importações, isolado no módulo."""

from alembic import op

revision = "0003_private_file_import"
down_revision = "0002_authentication_lookup"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
      CREATE TABLE actions_map.acoes_map_documentos_importacao (
        id varchar(36) PRIMARY KEY REFERENCES actions_map.acoes_map_importacoes(id),
        formato varchar(8) NOT NULL,
        tamanho integer NOT NULL CHECK (tamanho > 0 AND tamanho <= 8388608),
        estado varchar(20) NOT NULL,
        conteudo_cifrado text,
        expires_at timestamptz NOT NULL
      )
    """)
    op.execute("""
      CREATE INDEX ix_acoes_map_documentos_importacao_expires_at
      ON actions_map.acoes_map_documentos_importacao(expires_at)
    """)
    op.execute("""
      CREATE TABLE actions_map.acoes_map_partes_importacao (
        documento_id varchar(36) NOT NULL
          REFERENCES actions_map.acoes_map_documentos_importacao(id),
        indice integer NOT NULL CHECK (indice >= 0 AND indice < 16),
        conteudo_cifrado text NOT NULL,
        PRIMARY KEY (documento_id, indice)
      )
    """)


def downgrade():
    raise RuntimeError(
        "Remoção exige revisão de retenção e backup; downgrade automático bloqueado."
    )
