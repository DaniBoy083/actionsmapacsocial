import json
from datetime import UTC, datetime
from uuid import uuid4

from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.config import get_settings
from app.domain.clinical import ClinicalDesignationInput, ClinicalFields, ClinicalInput
from app.domain.contracts import Professional
from app.domain.institutional import Institutional
from app.infrastructure.actions import audit
from app.infrastructure.models import (
    Action,
    ClinicalDesignation,
    ClinicalRecord,
    ClinicalRevision,
    Participation,
    StaffAssignment,
    StaffRecord,
)
from app.infrastructure.operational_access import action_scope, staff_identity


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
        if not (actor.allowed or actor.operational_allowed):
            raise HTTPException(403, "Identidade institucional não autorizada.")
        self.session = session
        self.actor = actor

    def scope(self, action_id: str):
        if self.actor.operational_allowed:
            if self.actor.categoria == "RECEPCAO":
                raise HTTPException(403, "Recepção não acessa campos clínicos.")
            action_scope(self.session, action_id, self.actor)
        cipher = clinical_cipher()
        action = self.session.scalar(select(Action).where(Action.id == action_id).with_for_update())
        if not action or action.status == "arquivada":
            raise HTTPException(403, "Ação indisponível para registro clínico.")
        staff = self.session.scalar(
            select(StaffRecord)
            .where(
                (
                    StaffRecord.id == self.actor.staff_id
                    if self.actor.operational_allowed
                    else StaffRecord.identidade_institucional_id == self.actor.profissional_id
                ),
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
        designation = self.session.get(ClinicalDesignation, participation.id)
        if not designation or not (
            designation.ativo
            and designation.profissional_id == staff.id
            and designation.identidade_id == self.actor.profissional_id
        ):
            raise HTTPException(403, "Atendimento não designado a este profissional.")
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

    def designation(
        self, action_id: str, person_id: str, data: ClinicalDesignationInput | None = None
    ):
        if self.actor.operational_allowed:
            action_scope(self.session, action_id, self.actor, reception=True)
        action = self.session.scalar(select(Action).where(Action.id == action_id).with_for_update())
        if not action or action.status == "arquivada":
            raise HTTPException(403, "Ação indisponível para designação clínica.")
        participation = self.session.scalar(
            select(Participation)
            .where(Participation.acao_id == action_id, Participation.beneficiario_id == person_id)
            .with_for_update()
        )
        if not participation:
            raise HTTPException(404, "Atendimento não encontrado nesta ação.")
        row = self.session.get(ClinicalDesignation, participation.id)
        if data is not None:
            if data.versao != (row.versao if row else 0):
                raise HTTPException(409, "Designação alterada. Recarregue antes de salvar.")
            if not data.ativo:
                if not row or row.profissional_id != str(data.profissional_id):
                    raise HTTPException(422, "Selecione a designação existente para revogar.")
                row.ativo = False
                row.versao += 1
                row.atualizado_por = self.actor.profissional_id
                row.atualizado_em = datetime.now(UTC)
                audit(self.session, self.actor, "clinica.revogar", participation.id)
                self.session.flush()
                return {
                    "versao": row.versao,
                    "profissional_id": row.profissional_id,
                    "ativo": False,
                }
            staff = self.session.scalar(
                select(StaffRecord)
                .where(StaffRecord.id == str(data.profissional_id))
                .with_for_update()
            )
            assignment = self.session.scalar(
                select(StaffAssignment)
                .where(
                    StaffAssignment.acao_id == action_id,
                    StaffAssignment.profissional_id == str(data.profissional_id),
                    StaffAssignment.ativo.is_(True),
                    StaffAssignment.papel == "PROFISSIONAL",
                )
                .with_for_update()
            )
            if data.ativo and not (
                staff
                and staff.ativo
                and staff.categoria in {"MEDICO", "OPTOMETRISTA"}
                and staff.habilitacao_validada
                and staff.registro_clinico_autorizado
                and staff_identity(self.session, staff)
                and assignment
                and (
                    assignment.locais_indices is None
                    or participation.local_indice in assignment.locais_indices
                )
            ):
                raise HTTPException(
                    422, "Selecione profissional autorizado para esta ação e local."
                )
            identity = staff_identity(self.session, staff) if staff else None
            if not staff or not identity:
                raise HTTPException(422, "Profissional sem vínculo individual válido.")
            record = self.session.scalar(
                select(ClinicalRecord).where(ClinicalRecord.participacao_id == participation.id)
            )
            if record and (
                record.autor_profissional_id != staff.id or record.autor_identidade_id != identity
            ):
                raise HTTPException(
                    409,
                    "Ficha existente conserva sua autoria; transferência exige revisão específica.",
                )
            if row is None:
                row = ClinicalDesignation(participacao_id=participation.id, versao=1)
                self.session.add(row)
            else:
                row.versao += 1
            row.profissional_id = staff.id
            row.identidade_id = identity
            row.ativo = data.ativo
            row.atualizado_por = self.actor.profissional_id
            row.atualizado_em = datetime.now(UTC)
            audit(
                self.session,
                self.actor,
                "clinica.designar" if data.ativo else "clinica.revogar",
                participation.id,
            )
            self.session.flush()
        else:
            audit(self.session, self.actor, "clinica.designacao.read", participation.id)
        return {
            "versao": row.versao if row else 0,
            "profissional_id": row.profissional_id if row else None,
            "ativo": row.ativo if row else False,
        }

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
