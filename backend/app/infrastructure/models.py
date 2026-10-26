from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def now() -> datetime:
    return datetime.now(UTC)


def uid() -> str:
    return str(uuid4())


class Base(DeclarativeBase):
    pass


class Action(Base):
    __tablename__ = "acoes_map_acoes"
    __table_args__ = (
        CheckConstraint(
            "status IN ('em_revisao','validada','publicada','arquivada')", name="ck_acoes_status"
        ),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    versao: Mapped[int] = mapped_column(Integer, default=1)
    nome: Mapped[str] = mapped_column(String(160))
    categoria: Mapped[str] = mapped_column(String(80), default="")
    descricao: Mapped[str] = mapped_column(Text, default="")
    resumo_publico: Mapped[str] = mapped_column(Text, default="")
    inicio_em: Mapped[str | None] = mapped_column(String(10))
    fim_em: Mapped[str | None] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(20), default="em_revisao", index=True)
    locais: Mapped[list] = mapped_column(JSON)
    criado_por: Mapped[str] = mapped_column(String(160))
    aprovado_por: Mapped[str | None] = mapped_column(String(160))
    publicado_por: Mapped[str | None] = mapped_column(String(160))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Beneficiary(Base):
    __tablename__ = "acoes_map_beneficiarios"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    dados_cifrados: Mapped[str] = mapped_column(Text)
    municipio_residencia_ibge: Mapped[str | None] = mapped_column(String(7))


class Participation(Base):
    __tablename__ = "acoes_map_participacoes"
    __table_args__ = (UniqueConstraint("acao_id", "beneficiario_id"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    acao_id: Mapped[str] = mapped_column(ForeignKey(Action.id), index=True)
    beneficiario_id: Mapped[str] = mapped_column(ForeignKey(Beneficiary.id), index=True)
    local_indice: Mapped[int | None] = mapped_column(Integer)
    origem: Mapped[str | None] = mapped_column(String(64), unique=True)


class Audit(Base):
    __tablename__ = "acoes_map_auditoria"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    profissional_id: Mapped[str] = mapped_column(String(160))
    operacao: Mapped[str] = mapped_column(String(60))
    entidade_id: Mapped[str] = mapped_column(String(160))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class SessionRecord(Base):
    __tablename__ = "acoes_map_sessoes"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    profissional_id: Mapped[str] = mapped_column(String(160))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class LoginLimit(Base):
    __tablename__ = "acoes_map_login_limites"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    attempts: Mapped[int] = mapped_column(Integer)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ImportBatch(Base):
    __tablename__ = "acoes_map_importacoes"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    hash_arquivo: Mapped[str] = mapped_column(String(64))
    paginas: Mapped[int] = mapped_column(Integer)
    autor_id: Mapped[str] = mapped_column(String(160))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class ImportDocument(Base):
    __tablename__ = "acoes_map_documentos_importacao"
    id: Mapped[str] = mapped_column(ForeignKey(ImportBatch.id), primary_key=True)
    formato: Mapped[str] = mapped_column(String(8))
    tamanho: Mapped[int] = mapped_column(Integer)
    estado: Mapped[str] = mapped_column(String(20), default="recebendo")
    conteudo_cifrado: Mapped[str | None] = mapped_column(Text)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class ImportChunk(Base):
    __tablename__ = "acoes_map_partes_importacao"
    documento_id: Mapped[str] = mapped_column(ForeignKey(ImportDocument.id), primary_key=True)
    indice: Mapped[int] = mapped_column(Integer, primary_key=True)
    conteudo_cifrado: Mapped[str] = mapped_column(Text)


class Outbox(Base):
    __tablename__ = "acoes_map_integracoes_outbox"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    idempotency_key: Mapped[str] = mapped_column(String(160), unique=True)
    payload: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(20), default="pendente")
    tentativas: Mapped[int] = mapped_column(Integer, default=0)
    proxima_tentativa: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    erro: Mapped[str | None] = mapped_column(String(80))
    enviado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class IntegrationCredential(Base):
    __tablename__ = "acoes_map_credenciais_integracao"
    __table_args__ = (
        CheckConstraint("escopo = 'acoes.resumos.read'", name="ck_credencial_escopo"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    nome: Mapped[str] = mapped_column(String(80))
    prefixo: Mapped[str] = mapped_column(String(16))
    sufixo: Mapped[str] = mapped_column(String(4))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    escopo: Mapped[str] = mapped_column(String(40), default="acoes.resumos.read")
    criado_por: Mapped[str] = mapped_column(String(160))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    expira_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revogado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ultimo_uso_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    chamadas: Mapped[int] = mapped_column(Integer, default=0)
    janela_minuto: Mapped[int] = mapped_column(Integer, default=0)
    chamadas_janela: Mapped[int] = mapped_column(Integer, default=0)


class IntegrationExport(Base):
    __tablename__ = "acoes_map_exportacoes_integracao"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    credencial_id: Mapped[str] = mapped_column(ForeignKey(IntegrationCredential.id), index=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    expira_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    payload: Mapped[dict] = mapped_column(JSON)
