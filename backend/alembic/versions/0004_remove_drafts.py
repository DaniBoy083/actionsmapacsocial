"""Remove o estado antigo, preservando registros e gerando nova revisão auditada."""

import json
from uuid import uuid4

from alembic import op
from sqlalchemy import text

revision = "0004_remove_drafts"
down_revision = "0003_private_file_import"
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()
    rows = (
        connection.execute(
            text("""UPDATE actions_map.acoes_map_acoes
      SET status='em_revisao',versao=versao+1,atualizado_em=now(),aprovado_por=NULL,publicado_por=NULL
      WHERE status='rascunho' RETURNING id,versao,categoria,inicio_em,fim_em,locais""")
        )
        .mappings()
        .all()
    )
    for row in rows:
        event_id = str(uuid4())
        count = (
            connection.execute(
                text("""SELECT count(*) participacoes,
          count(DISTINCT beneficiario_id) pessoas FROM actions_map.acoes_map_participacoes WHERE acao_id=:id"""),
                {"id": row["id"]},
            )
            .mappings()
            .one()
        )
        payload = {
            "schema_version": "1.1",
            "event_id": event_id,
            "source": "ac-actions-map",
            "acao_id": row["id"],
            "revisao": row["versao"],
            "operacao": "upsert",
            "categoria": row["categoria"],
            "inicio_em": row["inicio_em"],
            "fim_em": row["fim_em"],
            "municipios_ibge": sorted({place["municipio_ibge"] for place in row["locais"]}),
            "quantidade_acoes": 1,
            "quantidade_participacoes": count["participacoes"],
            "quantidade_pessoas_contempladas": count["pessoas"],
            "publicavel": False,
        }
        connection.execute(
            text("""INSERT INTO actions_map.acoes_map_integracoes_outbox
          (id,idempotency_key,payload,status,tentativas,proxima_tentativa)
          VALUES(:id,:key,CAST(:payload AS json),'pendente',0,now())"""),
            {
                "id": event_id,
                "key": f"acao:{row['id']}:v{row['versao']}",
                "payload": json.dumps(payload),
            },
        )
        connection.execute(
            text("""INSERT INTO actions_map.acoes_map_auditoria(id,profissional_id,operacao,entidade_id,criado_em)
          VALUES(:id,'system:migration','acoes.remove_draft',:action,now())"""),
            {"id": str(uuid4()), "action": row["id"]},
        )
    op.execute("""ALTER TABLE actions_map.acoes_map_acoes ADD CONSTRAINT ck_acoes_status
      CHECK(status IN ('em_revisao','validada','publicada','arquivada'))""")


def downgrade():
    raise RuntimeError("O estado removido não é reintroduzido automaticamente.")
