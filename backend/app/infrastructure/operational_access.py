"""Contas locais e escopos. Não consulta o cadastro mestre institucional."""

import hashlib
import secrets
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError

from app.config import get_settings
from app.domain.contracts import Professional
from app.infrastructure.actions import audit
from app.infrastructure.models import (
    Action,
    OperationalAccount,
    OperationalSession,
    Participation,
    StaffAssignment,
    StaffRecord,
)


def require_operational_enabled():
    if not get_settings().operational_access_enabled:
        raise HTTPException(503, "O acesso operacional aguarda liberação da equipe responsável.")


def local_subject(account: OperationalAccount) -> str:
    return "actions-local:" + account.id


def staff_identity(session, staff: StaffRecord) -> str | None:
    if not get_settings().operational_access_enabled:
        return staff.identidade_institucional_id
    account = session.scalar(
        select(OperationalAccount).where(
            OperationalAccount.profissional_id == staff.id,
            OperationalAccount.ativo.is_(True),
        )
    )
    if account and staff.identidade_institucional_id:
        return None  # Duas origens não são intercambiáveis.
    return local_subject(account) if account else staff.identidade_institucional_id


def operator_actor(account: OperationalAccount, staff: StaffRecord) -> Professional:
    if not account.ativo or not staff.ativo or staff.identidade_institucional_id:
        raise HTTPException(403, "Acesso operacional indisponível. Procure a Administração.")
    if staff.categoria != "RECEPCAO" and not (
        staff.habilitacao_validada and staff.registro_clinico_autorizado
    ):
        raise HTTPException(403, "Habilitação e autorização clínica precisam estar válidas.")
    return Professional(
        profissional_id=local_subject(account),
        nome=staff.nome,
        tipo_login="operacional",
        equipe="operacional",
        auth_source="LOCAL",
        staff_id=staff.id,
        conta_versao=account.versao,
        categoria=staff.categoria,
    )


def account_view(row):
    return {
        "usuario": row.usuario if row else "",
        "ativo": row.ativo if row else False,
        "versao": row.versao if row else 0,
    }


def save_account(session, staff_id, data, actor):
    require_operational_enabled()
    staff = session.scalar(select(StaffRecord).where(StaffRecord.id == staff_id).with_for_update())
    if not staff:
        raise HTTPException(404, "Profissional não encontrado.")
    if staff.identidade_institucional_id:
        raise HTTPException(
            409,
            "Profissional já possui vínculo institucional. Revise a origem antes de criar conta local.",
        )
    if not staff.ativo and data.ativo:
        raise HTTPException(409, "Ative o cadastro profissional antes de liberar o acesso.")
    row = session.scalar(
        select(OperationalAccount)
        .where(
            OperationalAccount.profissional_id == staff_id,
        )
        .with_for_update()
    )
    if data.versao != (row.versao if row else 0):
        raise HTTPException(409, "Acesso alterado. Recarregue antes de salvar.")
    if row is None and data.nova_senha is None:
        raise HTTPException(422, "Informe uma senha para criar o acesso.")
    if row is None:
        row = OperationalAccount(profissional_id=staff_id, versao=1)
        session.add(row)
    else:
        row.versao += 1
        session.execute(delete(OperationalSession).where(OperationalSession.conta_id == row.id))
    if data.nova_senha is not None:
        salt = secrets.token_hex(16)
        row.senha_hash = (
            salt
            + ":"
            + hashlib.scrypt(
                data.nova_senha.get_secret_value().encode(),
                salt=salt.encode(),
                n=16384,
                r=8,
                p=1,
                dklen=64,
            ).hex()
        )
    row.usuario, row.ativo = data.usuario, data.ativo
    row.atualizado_por, row.atualizado_em = actor.profissional_id, datetime.now(UTC)
    try:
        session.flush()
    except IntegrityError:
        raise HTTPException(409, "Usuário de acesso indisponível.") from None
    audit(session, actor, "operacional.conta.save", row.id)
    return account_view(row)


def action_scope(session, action_id, actor, *, reception=False):
    if not actor.operational_allowed or (reception and actor.categoria != "RECEPCAO"):
        raise HTTPException(403, "Operação não permitida para este perfil.")
    # Mesma ordem das atribuições: ação → profissional → conta → atribuição.
    action = session.get(Action, action_id, with_for_update=True, populate_existing=True)
    if not action or action.status == "arquivada":
        raise HTTPException(404, "Ação não encontrada no seu escopo.")
    staff = session.get(StaffRecord, actor.staff_id, with_for_update=True, populate_existing=True)
    account = session.scalar(
        select(OperationalAccount)
        .where(
            OperationalAccount.profissional_id == actor.staff_id,
        )
        .with_for_update()
    )
    if (
        not account
        or not staff
        or local_subject(account) != actor.profissional_id
        or account.versao != actor.conta_versao
        or staff.categoria != actor.categoria
    ):
        raise HTTPException(403, "Acesso operacional revogado.")
    operator_actor(account, staff)
    found = session.execute(
        select(Action, StaffAssignment)
        .join(
            StaffAssignment,
            StaffAssignment.acao_id == Action.id,
        )
        .where(
            Action.id == action_id,
            Action.status != "arquivada",
            StaffAssignment.profissional_id == actor.staff_id,
            StaffAssignment.ativo.is_(True),
            StaffAssignment.papel
            == ("RECEPCAO" if actor.categoria == "RECEPCAO" else "PROFISSIONAL"),
        )
        .with_for_update()
    ).first()
    if not found:
        raise HTTPException(404, "Ação não encontrada no seu escopo.")
    return found


def require_location(action, assignment, index):
    if (
        index is None
        or index >= len(action.locais)
        or (assignment.locais_indices is not None and index not in assignment.locais_indices)
    ):
        raise HTTPException(403, "Local não permitido para este profissional.")


def person_scope(session, action_id, person_id, actor, *, reception=False):
    action, assignment = action_scope(session, action_id, actor, reception=reception)
    row = session.scalar(
        select(Participation)
        .where(
            Participation.acao_id == action_id,
            Participation.beneficiario_id == person_id,
        )
        .with_for_update()
    )
    if not row or (
        assignment.locais_indices is not None and row.local_indice not in assignment.locais_indices
    ):
        raise HTTPException(404, "Atendimento não encontrado no seu escopo.")
    return action, assignment, row
