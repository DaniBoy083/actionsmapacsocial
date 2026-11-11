"""Metadados e marcas privados; revisão aditiva, sem alterar autenticação."""

from alembic import op
import sqlalchemy as sa

from app.infrastructure.institutional_grants import IMMUTABLE_INSTITUTIONAL_GRANTS

revision = "0007_institutional_metadata"
down_revision = "0006_nonexpiring_tokens"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "acoes_map_acoes",
        sa.Column(
            "institucional",
            sa.JSON(),
            nullable=False,
            server_default="{}",
        ),
        schema="actions_map",
    )
    op.add_column(
        "acoes_map_participacoes",
        sa.Column(
            "documento_institucional",
            sa.JSON(),
            nullable=True,
        ),
        schema="actions_map",
    )
    op.create_table(
        "acoes_map_marcas",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "acao_id",
            sa.String(36),
            sa.ForeignKey("actions_map.acoes_map_acoes.id"),
            nullable=False,
        ),
        sa.Column("slot", sa.String(10), nullable=False),
        sa.Column("conteudo_base64", sa.Text(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("largura", sa.Integer(), nullable=False),
        sa.Column("altura", sa.Integer(), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("slot IN ('governo','clinica')", name="ck_marca_slot"),
        schema="actions_map",
    )
    op.create_index(
        "ix_acoes_map_marcas_acao_id", "acoes_map_marcas", ["acao_id"], schema="actions_map"
    )
    op.create_table(
        "acoes_map_revisoes_institucionais",
        sa.Column(
            "acao_id",
            sa.String(36),
            sa.ForeignKey("actions_map.acoes_map_acoes.id"),
            primary_key=True,
        ),
        sa.Column("versao", sa.Integer(), primary_key=True),
        sa.Column("dados", sa.JSON(), nullable=False),
        sa.Column("criado_por", sa.String(160), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        schema="actions_map",
    )
    op.execute(IMMUTABLE_INSTITUTIONAL_GRANTS)


def downgrade():
    raise RuntimeError(
        "Preserve marcas, revisões e comprovantes. Use rollback de código compatível."
    )
