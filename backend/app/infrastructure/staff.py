from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.domain.contracts import Professional
from app.domain.staff import AssignmentInput, AssignmentUpdate, StaffData, StaffInput, StaffView
from app.infrastructure.actions import audit
from app.infrastructure.models import (
    Action,
    OperationalAccount,
    OperationalSession,
    StaffAssignment,
    StaffRecord,
    StaffRevision,
)

QUALIFICATION_FIELDS = (
    "registro_clinico_autorizado",
    "autorizacao_clinica_referencia",
    "identidade_institucional_id",
    "categoria",
    "registro_conselho",
    "registro_numero",
    "registro_uf",
    "rqe",
    "habilitacao_validada",
    "habilitacao_referencia",
)


def staff_view(row: StaffRecord) -> dict:
    return StaffView(
        **{key: getattr(row, key) for key in StaffData.model_fields},
        id=row.id,
        versao=row.versao,
        atualizado_em=row.atualizado_em,
        conferido_por=row.conferido_por,
        conferido_em=row.conferido_em,
        divulgacao_registrada_por=row.divulgacao_registrada_por,
        divulgacao_registrada_em=row.divulgacao_registrada_em,
    ).model_dump(mode="json")


def assignment_snapshot(row: StaffAssignment) -> dict:
    return {
        "id": row.id,
        "versao": row.versao,
        "acao_id": row.acao_id,
        "profissional_id": row.profissional_id,
        "papel": row.papel,
        "ativo": row.ativo,
        "locais_indices": row.locais_indices,
        "locais_snapshot": row.locais_snapshot,
        "profissional_snapshot": row.profissional_snapshot,
        "atualizado_em": row.atualizado_em.isoformat(),
    }


def remember(
    session: Session, kind: str, identifier: str, version: int, data: dict, actor: Professional
):
    session.add(
        StaffRevision(
            tipo=kind,
            entidade_id=identifier,
            versao=version,
            dados=data,
            registrado_por=actor.profissional_id,
        )
    )


def revoke_assignments(session: Session, rows: list[StaffAssignment], actor: Professional) -> int:
    for row in rows:
        changed = session.execute(
            update(StaffAssignment)
            .where(
                StaffAssignment.id == row.id,
                StaffAssignment.versao == row.versao,
                StaffAssignment.ativo.is_(True),
            )
            .values(ativo=False, versao=row.versao + 1, atualizado_em=datetime.now(UTC))
        )
        if changed.rowcount != 1:
            raise HTTPException(409, "Atribuição alterada. Recarregue antes de continuar.")
        session.refresh(row)
        remember(session, "ATRIBUICAO", row.id, row.versao, assignment_snapshot(row), actor)
        audit(session, actor, "atribuicoes.revogar", row.id)
    return len(rows)


def revoke_action_assignments(session: Session, action_id: str, actor: Professional) -> None:
    rows = session.scalars(
        select(StaffAssignment)
        .where(
            StaffAssignment.acao_id == action_id,
            StaffAssignment.ativo.is_(True),
        )
        .with_for_update()
    ).all()
    revoke_assignments(session, rows, actor)


class SqlStaffRepository:
    def __init__(self, session: Session):
        self.session = session

    def staff(self, identifier: str, *, lock=False) -> StaffRecord:
        query = select(StaffRecord).where(StaffRecord.id == identifier)
        row = self.session.scalar(query.with_for_update() if lock else query)
        if not row:
            raise HTTPException(404, "Profissional não encontrado.")
        return row

    def action(self, identifier: str) -> Action:
        row = self.session.scalar(select(Action).where(Action.id == identifier).with_for_update())
        if not row:
            raise HTTPException(404, "Ação não encontrada.")
        return row

    def flush_unique(self):
        try:
            self.session.flush()
        except IntegrityError:
            raise HTTPException(
                409, "Registro ou atribuição já cadastrados. Recarregue a lista."
            ) from None

    def list_staff(
        self, actor: Professional, *, search: str, active: bool | None, page: int, size: int
    ):
        query = select(StaffRecord)
        if search:
            query = query.where(StaffRecord.nome.icontains(search, autoescape=True))
        if active is not None:
            query = query.where(StaffRecord.ativo == active)
        total = self.session.scalar(select(func.count()).select_from(query.subquery()))
        rows = self.session.scalars(
            query.order_by(StaffRecord.nome, StaffRecord.id).offset((page - 1) * size).limit(size)
        ).all()
        audit(self.session, actor, "profissionais.list", "profissionais")
        return {
            "items": [staff_view(row) for row in rows],
            "total": total,
            "pagina": page,
            "tamanho": size,
        }

    def read(self, identifier: str, actor: Professional):
        row = self.staff(identifier)
        audit(self.session, actor, "profissionais.read", row.id)
        return staff_view(row)

    def history(self, identifier: str, actor: Professional, *, page: int, size: int):
        self.staff(identifier)
        return self.events("PROFISSIONAL", identifier, actor, page=page, size=size)

    def assignment_history(
        self, action_id: str, identifier: str, actor: Professional, *, page: int, size: int
    ):
        row = self.session.scalar(
            select(StaffAssignment).where(
                StaffAssignment.id == identifier,
                StaffAssignment.acao_id == action_id,
            )
        )
        if row is None:
            raise HTTPException(404, "Atribuição não encontrada nesta ação.")
        return self.events("ATRIBUICAO", identifier, actor, page=page, size=size)

    def events(self, kind: str, identifier: str, actor: Professional, *, page: int, size: int):
        query = select(StaffRevision).where(
            StaffRevision.tipo == kind,
            StaffRevision.entidade_id == identifier,
        )
        total = self.session.scalar(select(func.count()).select_from(query.subquery()))
        rows = self.session.scalars(
            query.order_by(StaffRevision.versao.desc()).offset((page - 1) * size).limit(size)
        ).all()
        audit(
            self.session,
            actor,
            "profissionais.historico.read"
            if kind == "PROFISSIONAL"
            else "atribuicoes.historico.read",
            identifier,
        )
        return {
            "items": [
                {"versao": row.versao, "dados": row.dados, "registrado_em": row.registrado_em}
                for row in rows
            ],
            "total": total,
            "pagina": page,
            "tamanho": size,
        }

    def save(self, data: StaffInput, actor: Professional, identifier: str | None = None):
        row = self.staff(identifier, lock=True) if identifier else None
        if data.versao != (row.versao if row else 0):
            raise HTTPException(409, "Profissional alterado. Reabra o cadastro antes de salvar.")
        values = data.model_dump(exclude={"versao"})
        if (
            data.identidade_institucional_id
            and (row is None or data.identidade_institucional_id != row.identidade_institucional_id)
            and data.identidade_institucional_id != actor.profissional_id
        ):
            raise HTTPException(
                403, "Vincule somente a identidade institucional da sua sessão validada."
            )
        qualification_changed = row is None or any(
            getattr(row, key) != values[key] for key in QUALIFICATION_FIELDS
        )
        publicity_changed = row is None or any(
            getattr(row, key) != values[key]
            for key in ("divulgacao_autorizada", "divulgacao_referencia")
        )
        now = datetime.now(UTC)
        if qualification_changed:
            values.update(
                conferido_por=actor.profissional_id if data.habilitacao_validada else None,
                conferido_em=now if data.habilitacao_validada else None,
            )
        if publicity_changed:
            values.update(
                divulgacao_registrada_por=actor.profissional_id
                if data.divulgacao_autorizada
                else None,
                divulgacao_registrada_em=now if data.divulgacao_autorizada else None,
            )
        if row:
            # Mantém o mesmo lock do cadastro usado ao criar/reativar uma atribuição.
            revoked = []
            if not data.ativo or qualification_changed:
                revoked = self.session.scalars(
                    select(StaffAssignment)
                    .where(
                        StaffAssignment.profissional_id == row.id,
                        StaffAssignment.ativo.is_(True),
                    )
                    .with_for_update()
                ).all()
            changed = self.session.execute(
                update(StaffRecord)
                .where(
                    StaffRecord.id == row.id,
                    StaffRecord.versao == data.versao,
                )
                .values(**values, versao=data.versao + 1, atualizado_em=now)
            )
            if changed.rowcount != 1:
                raise HTTPException(
                    409, "Profissional alterado. Reabra o cadastro antes de salvar."
                )
            self.session.refresh(row)
            revoke_assignments(self.session, revoked, actor)
            if get_settings().operational_access_enabled and (
                not data.ativo or qualification_changed
            ):
                self.session.execute(
                    delete(OperationalSession).where(
                        OperationalSession.conta_id.in_(
                            select(OperationalAccount.id).where(
                                OperationalAccount.profissional_id == row.id,
                            )
                        )
                    )
                )
        else:
            row = StaffRecord(**values, criado_por=actor.profissional_id)
            self.session.add(row)
        self.flush_unique()
        result = staff_view(row)
        remember(self.session, "PROFISSIONAL", row.id, row.versao, result, actor)
        audit(
            self.session,
            actor,
            "profissionais.update" if identifier else "profissionais.create",
            row.id,
        )
        self.flush_unique()
        return result

    def active_local_accounts(self, staff_ids):
        if not get_settings().operational_access_enabled or not staff_ids:
            return set()
        return set(
            self.session.scalars(
                select(OperationalAccount.profissional_id)
                .join(StaffRecord)
                .where(
                    OperationalAccount.profissional_id.in_(staff_ids),
                    OperationalAccount.ativo.is_(True),
                    StaffRecord.identidade_institucional_id.is_(None),
                )
            )
        )

    def assignment_view(self, row: StaffAssignment, account_active=None):
        return {
            **assignment_snapshot(row),
            "profissional": staff_view(self.staff(row.profissional_id)),
            "conta_operacional_ativa": (
                row.profissional_id in self.active_local_accounts([row.profissional_id])
                if account_active is None
                else account_active
            ),
        }

    def list_assignments(self, action_id: str, actor: Professional, *, page: int, size: int):
        self.action(action_id)
        query = select(StaffAssignment).where(StaffAssignment.acao_id == action_id)
        total = self.session.scalar(select(func.count()).select_from(query.subquery()))
        rows = self.session.scalars(
            query.order_by(StaffAssignment.criado_em, StaffAssignment.id)
            .offset((page - 1) * size)
            .limit(size)
        ).all()
        audit(self.session, actor, "atribuicoes.list", action_id)
        local_accounts = self.active_local_accounts([row.profissional_id for row in rows])
        return {
            "items": [
                self.assignment_view(row, row.profissional_id in local_accounts) for row in rows
            ],
            "total": total,
            "pagina": page,
            "tamanho": size,
        }

    def assign(
        self,
        action_id: str,
        data: AssignmentInput | AssignmentUpdate,
        actor: Professional,
        identifier: str | None = None,
    ):
        action = self.action(action_id)
        row = None
        staff_id = (
            str(data.profissional_id)
            if identifier is None
            else self.session.scalar(
                select(StaffAssignment.profissional_id).where(
                    StaffAssignment.id == identifier,
                    StaffAssignment.acao_id == action_id,
                )
            )
        )
        if not staff_id:
            raise HTTPException(404, "Atribuição não encontrada nesta ação.")
        # Ordem consistente: ação → profissional → atribuição. Evita inversão com inativação.
        staff = self.staff(staff_id, lock=True)
        if identifier:
            row = self.session.scalar(
                select(StaffAssignment)
                .where(
                    StaffAssignment.id == identifier,
                    StaffAssignment.acao_id == action_id,
                )
                .with_for_update()
            )
            if not row:
                raise HTTPException(404, "Atribuição não encontrada nesta ação.")
            if row.versao != data.versao:
                raise HTTPException(409, "Atribuição alterada. Recarregue antes de salvar.")
        if action.versao != data.acao_versao or staff.versao != data.profissional_versao:
            raise HTTPException(409, "Ação ou profissional alterado. Recarregue os dados.")
        active = data.ativo if row else True
        if active and (action.status == "arquivada" or not staff.ativo):
            raise HTTPException(
                409, "Ação arquivada ou profissional inativo não recebe atribuição ativa."
            )
        if active and staff.categoria != "RECEPCAO" and not staff.habilitacao_validada:
            raise HTTPException(
                422, "Registre a conferência da habilitação antes de atribuir o profissional."
            )
        if data.locais_indices is not None and any(
            index >= len(action.locais) for index in data.locais_indices
        ):
            raise HTTPException(422, "Local não pertence à ação.")
        if row and not active:
            if row.ativo:
                revoke_assignments(self.session, [row], actor)
            return self.assignment_view(row)
        values = {
            "locais_indices": data.locais_indices,
            "locais_snapshot": [
                {"indice": index, **action.locais[index]} for index in data.locais_indices
            ]
            if data.locais_indices is not None
            else None,
            "profissional_snapshot": staff_view(staff),
            "ativo": active,
            "papel": "RECEPCAO" if staff.categoria == "RECEPCAO" else "PROFISSIONAL",
        }
        if row:
            changed = self.session.execute(
                update(StaffAssignment)
                .where(
                    StaffAssignment.id == row.id,
                    StaffAssignment.versao == data.versao,
                )
                .values(**values, versao=data.versao + 1, atualizado_em=datetime.now(UTC))
            )
            if changed.rowcount != 1:
                raise HTTPException(409, "Atribuição alterada. Recarregue antes de salvar.")
            self.session.refresh(row)
        else:
            row = StaffAssignment(
                **values,
                acao_id=action_id,
                profissional_id=staff.id,
                criado_por=actor.profissional_id,
            )
            self.session.add(row)
        self.flush_unique()
        remember(self.session, "ATRIBUICAO", row.id, row.versao, assignment_snapshot(row), actor)
        audit(
            self.session,
            actor,
            "atribuicoes.update" if identifier else "atribuicoes.create",
            row.id,
        )
        self.flush_unique()
        return self.assignment_view(row)
