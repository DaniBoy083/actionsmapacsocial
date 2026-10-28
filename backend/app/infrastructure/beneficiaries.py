from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.domain.contracts import MUNICIPALITIES, BeneficiaryUpdate, Professional
from app.infrastructure.actions import action_or_404, audit, cipher
from app.infrastructure.beneficiary_data import decode_beneficiary, encode_beneficiary
from app.infrastructure.models import Beneficiary, Participation


class SqlBeneficiariesRepository:
    def __init__(self, session: Session):
        self.session = session

    def find(self, action_id: str, person_id: str):
        action = action_or_404(self.session, action_id)
        found = self.session.execute(
            select(Beneficiary, Participation)
            .join(Participation)
            .where(
                Participation.acao_id == action_id,
                Beneficiary.id == person_id,
            )
        ).first()
        if not found:
            raise HTTPException(404, "Beneficiário não encontrado nesta ação.")
        return action, *found

    def sheet(self, action_id: str, person_id: str, second_copy: bool) -> dict:
        action, person, participation = self.find(action_id, person_id)
        data, version = decode_beneficiary(person, cipher())
        return {
            "id": person.id,
            "versao": version,
            **data.model_dump(mode="json"),
            "local_indice": participation.local_indice,
            "acao": {"id": action.id, "nome": action.nome},
            "municipio_ficha_nome": MUNICIPALITIES.get(data.municipio_ficha_ibge or ""),
            "municipio_residencia_nome": MUNICIPALITIES.get(data.municipio_residencia_ibge or ""),
            "segunda_via": second_copy,
            "emitido_em": datetime.now(UTC).isoformat() if second_copy else None,
        }

    def read(
        self, action_id: str, person_id: str, professional: Professional, second_copy: bool
    ) -> dict:
        result = self.sheet(action_id, person_id, second_copy)
        audit(
            self.session,
            professional,
            "beneficiarios.segunda_via" if second_copy else "beneficiarios.ficha.read",
            person_id,
        )
        return result

    def update(
        self, action_id: str, person_id: str, data: BeneficiaryUpdate, professional: Professional
    ) -> dict:
        action, person, participation = self.find(action_id, person_id)
        _, version = decode_beneficiary(person, cipher())
        if version != data.versao:
            raise HTTPException(409, "Este cadastro foi alterado. Reabra a ficha antes de salvar.")
        if data.local_indice is not None and data.local_indice >= len(action.locais):
            raise HTTPException(422, "Local não pertence à ação.")
        previous = person.dados_cifrados
        result = self.session.execute(
            update(Beneficiary)
            .where(
                Beneficiary.id == person_id,
                Beneficiary.dados_cifrados == previous,
            )
            .values(
                dados_cifrados=encode_beneficiary(person_id, data, version + 1, cipher()),
                municipio_residencia_ibge=data.municipio_residencia_ibge,
            )
        )
        if result.rowcount != 1:
            raise HTTPException(409, "Este cadastro foi alterado. Reabra a ficha antes de salvar.")
        participation.local_indice = data.local_indice
        audit(self.session, professional, "beneficiarios.update", person_id)
        self.session.flush()
        self.session.expire_all()
        return self.sheet(action_id, person_id, False)
