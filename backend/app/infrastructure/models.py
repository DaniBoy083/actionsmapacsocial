from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
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
    institucional: Mapped[dict] = mapped_column(JSON, default=dict, server_default="{}")
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


class ActionLogo(Base):
    __tablename__ = "acoes_map_marcas"
    __table_args__ = (CheckConstraint("slot IN ('governo','clinica')", name="ck_marca_slot"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    acao_id: Mapped[str] = mapped_column(ForeignKey(Action.id), index=True)
    slot: Mapped[str] = mapped_column(String(10))
    conteudo_base64: Mapped[str] = mapped_column(Text)
    sha256: Mapped[str] = mapped_column(String(64))
    largura: Mapped[int] = mapped_column(Integer)
    altura: Mapped[int] = mapped_column(Integer)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class InstitutionalRevision(Base):
    __tablename__ = "acoes_map_revisoes_institucionais"
    acao_id: Mapped[str] = mapped_column(ForeignKey(Action.id), primary_key=True)
    versao: Mapped[int] = mapped_column(Integer, primary_key=True)
    dados: Mapped[dict] = mapped_column(JSON)
    criado_por: Mapped[str] = mapped_column(String(160))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Participation(Base):
    __tablename__ = "acoes_map_participacoes"
    __table_args__ = (UniqueConstraint("acao_id", "beneficiario_id"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    acao_id: Mapped[str] = mapped_column(ForeignKey(Action.id), index=True)
    beneficiario_id: Mapped[str] = mapped_column(ForeignKey(Beneficiary.id), index=True)
    local_indice: Mapped[int | None] = mapped_column(Integer)
    origem: Mapped[str | None] = mapped_column(String(64), unique=True)
    documento_institucional: Mapped[dict | None] = mapped_column(
        JSON(none_as_null=True), nullable=True
    )


class Audit(Base):
    __tablename__ = "acoes_map_auditoria"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    profissional_id: Mapped[str] = mapped_column(String(160))
    operacao: Mapped[str] = mapped_column(String(60))
    entidade_id: Mapped[str] = mapped_column(String(160))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class StaffRecord(Base):
    __tablename__ = "acoes_map_profissionais"
    __table_args__ = (
        CheckConstraint(
            "categoria IN ('MEDICO','OPTOMETRISTA','RECEPCAO')", name="ck_profissional_categoria"
        ),
        CheckConstraint("versao >= 1", name="ck_profissional_versao"),
        UniqueConstraint(
            "registro_conselho", "registro_numero", "registro_uf", name="uq_profissional_registro"
        ),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    versao: Mapped[int] = mapped_column(Integer, default=1)
    nome: Mapped[str] = mapped_column(String(160))
    categoria: Mapped[str] = mapped_column(String(20))
    identidade_institucional_id: Mapped[str | None] = mapped_column(String(160), unique=True)
    registro_conselho: Mapped[str | None] = mapped_column(String(40))
    registro_numero: Mapped[str | None] = mapped_column(String(40))
    registro_uf: Mapped[str | None] = mapped_column(String(2))
    rqe: Mapped[str | None] = mapped_column(String(40))
    habilitacao_validada: Mapped[bool] = mapped_column(Boolean, default=False)
    habilitacao_referencia: Mapped[str] = mapped_column(String(200), default="")
    registro_clinico_autorizado: Mapped[bool] = mapped_column(Boolean, default=False)
    autorizacao_clinica_referencia: Mapped[str] = mapped_column(String(200), default="")
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    divulgacao_autorizada: Mapped[bool] = mapped_column(Boolean, default=False)
    divulgacao_referencia: Mapped[str] = mapped_column(String(200), default="")
    conferido_por: Mapped[str | None] = mapped_column(String(160))
    conferido_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    divulgacao_registrada_por: Mapped[str | None] = mapped_column(String(160))
    divulgacao_registrada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    criado_por: Mapped[str] = mapped_column(String(160))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class StaffAssignment(Base):
    __tablename__ = "acoes_map_atribuicoes"
    __table_args__ = (
        UniqueConstraint("acao_id", "profissional_id", name="uq_atribuicao_acao_profissional"),
        CheckConstraint("papel IN ('PROFISSIONAL','RECEPCAO')", name="ck_atribuicao_papel"),
        CheckConstraint("versao >= 1", name="ck_atribuicao_versao"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    versao: Mapped[int] = mapped_column(Integer, default=1)
    acao_id: Mapped[str] = mapped_column(ForeignKey(Action.id), index=True)
    profissional_id: Mapped[str] = mapped_column(ForeignKey(StaffRecord.id), index=True)
    papel: Mapped[str] = mapped_column(String(20))
    locais_indices: Mapped[list | None] = mapped_column(JSON(none_as_null=True), nullable=True)
    locais_snapshot: Mapped[list | None] = mapped_column(JSON(none_as_null=True), nullable=True)
    profissional_snapshot: Mapped[dict] = mapped_column(JSON)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    criado_por: Mapped[str] = mapped_column(String(160))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class StaffRevision(Base):
    __tablename__ = "acoes_map_profissionais_historico"
    __table_args__ = (
        UniqueConstraint("tipo", "entidade_id", "versao", name="uq_profissional_historico"),
        CheckConstraint(
            "tipo IN ('PROFISSIONAL','ATRIBUICAO')", name="ck_profissional_historico_tipo"
        ),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    tipo: Mapped[str] = mapped_column(String(20))
    entidade_id: Mapped[str] = mapped_column(String(36), index=True)
    versao: Mapped[int] = mapped_column(Integer)
    dados: Mapped[dict] = mapped_column(JSON)
    registrado_por: Mapped[str] = mapped_column(String(160))
    registrado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class ClinicalRecord(Base):
    __tablename__ = "acoes_map_fichas_clinicas"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    participacao_id: Mapped[str] = mapped_column(ForeignKey(Participation.id), unique=True)
    autor_profissional_id: Mapped[str] = mapped_column(ForeignKey(StaffRecord.id), index=True)
    autor_identidade_id: Mapped[str] = mapped_column(String(160))
    versao: Mapped[int] = mapped_column(Integer, default=1)
    dados_cifrados: Mapped[str] = mapped_column(Text)
    contexto: Mapped[dict] = mapped_column(JSON)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class ClinicalRevision(Base):
    __tablename__ = "acoes_map_fichas_clinicas_versoes"
    __table_args__ = (UniqueConstraint("ficha_id", "versao", name="uq_ficha_clinica_versao"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    ficha_id: Mapped[str] = mapped_column(ForeignKey(ClinicalRecord.id), index=True)
    versao: Mapped[int] = mapped_column(Integer)
    dados_cifrados: Mapped[str] = mapped_column(Text)
    registrado_por: Mapped[str] = mapped_column(String(160))
    registrado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


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
