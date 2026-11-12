import json
from datetime import UTC, datetime
from uuid import uuid4

from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.config import get_settings
from app.domain.clinical import ClinicalFields, ClinicalInput
from app.domain.contracts import Professional
from app.domain.institutional import Institutional
from app.infrastructure.actions import audit
from app.infrastructure.models import (
    Action,
    ClinicalRecord,
    ClinicalRevision,
    Participation,
    StaffAssignment,
    StaffRecord,
)


def clinical_cipher() -> Fernet:
    settings = get_settings()
    if not settings.clinical_fields_enabled:
        raise HTTPException(503, "O registro clínico aguarda liberação operacional.")
    key = settings.clinical_key.get_secret_value()
    if not key or key == settings.beneficiaries_key.get_secret_value():
        raise HTTPException(503, "Proteção específica dos campos clínicos não configurada.")
    try:
        return Fernet(key.encode())
    except (ValueError, TypeError):
        raise HTTPException(
            503, "Proteção específica dos campos clínicos não configurada."
        ) from None


class SqlClinicalRepository:
    def __init__(self, session: Session, actor: Professional):
        if not actor.allowed:
            raise HTTPException(403, "Identidade institucional não autorizada.")
        self.session = session
        self.actor = actor

    def scope(self, action_id: str):
        cipher = clinical_cipher()
        action = self.session.scalar(select(Action).where(Action.id == action_id).with_for_update())
        if not action or action.status == "arquivada":
            raise HTTPException(403, "Ação indisponível para registro clínico.")
        staff = self.session.scalar(
            select(StaffRecord)
            .where(
                StaffRecord.identidade_institucional_id == self.actor.profissional_id,
                StaffRecord.ativo.is_(True),
                StaffRecord.habilitacao_validada.is_(True),
                StaffRecord.registro_clinico_autorizado.is_(True),
                StaffRecord.categoria.in_(["MEDICO", "OPTOMETRISTA"]),
            )
            .with_for_update()
        )
        if not staff:
            raise HTTPException(
                403,
                "Registro clínico exige vínculo individual e autorização profissional específica.",
            )
        assignment = self.session.scalar(
            select(StaffAssignment)
            .where(
                StaffAssignment.acao_id == action_id,
                StaffAssignment.profissional_id == staff.id,
                StaffAssignment.ativo.is_(True),
                StaffAssignment.papel == "PROFISSIONAL",
            )
            .with_for_update()
        )
        if not assignment:
            raise HTTPException(403, "Profissional não está atribuído a esta ação.")
        return action, staff, assignment, cipher

    def find(self, action_id: str, person_id: str):
        action, staff, assignment, cipher = self.scope(action_id)
        participation = self.session.scalar(
            select(Participation)
            .where(
                Participation.acao_id == action_id,
                Participation.beneficiario_id == person_id,
            )
            .with_for_update()
        )
        if participation is None or (
            assignment.locais_indices is not None
            and participation.local_indice not in assignment.locais_indices
        ):
            raise HTTPException(404, "Cadastro não encontrado no escopo profissional.")
        row = self.session.scalar(
            select(ClinicalRecord)
            .where(ClinicalRecord.participacao_id == participation.id)
            .with_for_update()
        )
        if row is not None and (
            row.autor_profissional_id != staff.id
            or row.autor_identidade_id != self.actor.profissional_id
        ):
            raise HTTPException(404, "Registro não disponível para este profissional.")
        return action, staff, participation, row, cipher

    def context(self, action, staff) -> dict:
        return {
            "acao": {"id": action.id, "nome": action.nome, "versao": action.versao},
            "institucional": Institutional.model_validate(action.institucional).model_dump(
                mode="json"
            ),
            "profissional": {
                key: getattr(staff, key)
                for key in (
                    "id",
                    "nome",
                    "categoria",
                    "registro_conselho",
                    "registro_numero",
                    "registro_uf",
                    "rqe",
                )
            },
            "fonte_sha256": "74adf57b5d200d353dac5ae3626ce79a8b7c0a6a78cb8563c339785760f1f074",
        }

    def encode(self, row, fields: ClinicalFields, version: int, cipher: Fernet) -> str:
        envelope = {
            "formato": 1,
            "ficha_id": row.id,
            "participacao_id": row.participacao_id,
            "autor_profissional_id": row.autor_profissional_id,
            "autor_identidade_id": row.autor_identidade_id,
            "versao": version,
            "campos": fields.model_dump(mode="json"),
        }
        return cipher.encrypt(json.dumps(envelope, ensure_ascii=False).encode()).decode()

    def decode(self, row, encrypted: str, version: int, cipher: Fernet) -> ClinicalFields:
        try:
            envelope = json.loads(cipher.decrypt(encrypted.encode()))
            expected = {
                "formato": 1,
                "ficha_id": row.id,
                "participacao_id": row.participacao_id,
                "autor_profissional_id": row.autor_profissional_id,
                "autor_identidade_id": row.autor_identidade_id,
                "versao": version,
            }
            if any(envelope.get(key) != value for key, value in expected.items()):
                raise ValueError
            return ClinicalFields.model_validate(envelope["campos"])
        except (InvalidToken, ValueError, TypeError, KeyError):
            raise HTTPException(
                503, "Não foi possível abrir o registro clínico protegido."
            ) from None

    def read(self, action_id: str, person_id: str, version: int | None = None) -> dict:
        action, staff, _, row, cipher = self.find(action_id, person_id)
        if row is None:
            if version is not None:
                raise HTTPException(404, "Versão clínica não encontrada.")
            result = {
                "id": None,
                "versao": 0,
                "campos": ClinicalFields().model_dump(),
                "contexto": self.context(action, staff),
                "atualizado_em": None,
            }
        else:
            revision = None
            if version is not None:
                revision = self.session.scalar(
                    select(ClinicalRevision).where(
                        ClinicalRevision.ficha_id == row.id,
                        ClinicalRevision.versao == version,
                    )
                )
                if revision is None:
                    raise HTTPException(404, "Versão clínica não encontrada.")
            number = revision.versao if revision else row.versao
            fields = self.decode(
                row, revision.dados_cifrados if revision else row.dados_cifrados, number, cipher
            )
            result = {
                "id": row.id,
                "versao": number,
                "campos": fields.model_dump(),
                "contexto": row.contexto,
                "atualizado_em": revision.registrado_em if revision else row.atualizado_em,
            }
        audit(self.session, self.actor, "clinica.read", row.id if row else action.id)
        return result

    def save(self, action_id: str, person_id: str, data: ClinicalInput) -> dict:
        action, staff, participation, row, cipher = self.find(action_id, person_id)
        if data.versao != (row.versao if row else 0):
            raise HTTPException(409, "Registro clínico alterado. Reabra a ficha antes de salvar.")
        if row is None:
            row = ClinicalRecord(
                id=str(uuid4()),
                participacao_id=participation.id,
                autor_profissional_id=staff.id,
                autor_identidade_id=self.actor.profissional_id,
                contexto=self.context(action, staff),
            )
            row.dados_cifrados = self.encode(row, data.campos, 1, cipher)
            self.session.add(row)
        else:
            encrypted = self.encode(row, data.campos, data.versao + 1, cipher)
            changed = self.session.execute(
                update(ClinicalRecord)
                .where(
                    ClinicalRecord.id == row.id,
                    ClinicalRecord.versao == data.versao,
                )
                .values(
                    dados_cifrados=encrypted,
                    versao=data.versao + 1,
                    atualizado_em=datetime.now(UTC),
                )
            )
            if changed.rowcount != 1:
                raise HTTPException(
                    409, "Registro clínico alterado. Reabra a ficha antes de salvar."
                )
            self.session.refresh(row)
        self.session.flush()
        self.session.add(
            ClinicalRevision(
                ficha_id=row.id,
                versao=row.versao,
                dados_cifrados=row.dados_cifrados,
                registrado_por=self.actor.profissional_id,
            )
        )
        audit(self.session, self.actor, "clinica.save", row.id)
        self.session.flush()
        return {
            "id": row.id,
            "versao": row.versao,
            "campos": data.campos.model_dump(),
            "contexto": row.contexto,
            "atualizado_em": row.atualizado_em,
        }
