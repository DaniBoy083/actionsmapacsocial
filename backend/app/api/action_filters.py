from typing import Literal

from fastapi import Query
from sqlalchemy import and_, or_, select

from app.infrastructure.models import Action, ActionInstitution, Institution


def institutional_filters(
    instrumento: str = Query("", max_length=160),
    numero_instrumento: str = Query("", max_length=80),
    autor: str = Query("", max_length=160),
    orgao: str = Query("", max_length=160),
    clinica: str = Query("", max_length=160),
    apoio: Literal["", "TOTAL", "PARCIAL"] = "",
    contratante: str = Query("", max_length=160),
    apoiador: str = Query("", max_length=160),
) -> dict:
    return {
        "instrumento": instrumento,
        "numero_instrumento": numero_instrumento,
        "autor": autor,
        "orgao": orgao,
        "clinica": clinica,
        "apoio": apoio,
        "contratante": contratante,
        "apoiador": apoiador,
    }


def filter_institutional(query, filters: dict):
    paths = {
        "instrumento": ("instrumento", "nome"),
        "numero_instrumento": ("instrumento", "numero"),
        "autor": ("instrumento", "autor"),
        "orgao": ("governo", "nome"),
        "clinica": ("clinica", "nome"),
    }
    for key, (section, field) in paths.items():
        if filters[key].strip():
            legacy = (
                Action.institucional[section][field]
                .as_string()
                .icontains(
                    filters[key].strip(),
                    autoescape=True,
                )
            )
            if key in {"orgao", "clinica"}:
                typed = (
                    select(1)
                    .select_from(ActionInstitution)
                    .join(Institution)
                    .where(
                        ActionInstitution.acao_id == Action.id,
                        Institution.tipo
                        == ("CLINICA" if key == "clinica" else "ORGAO_GOVERNAMENTAL"),
                        Institution.nome.icontains(filters[key].strip(), autoescape=True),
                    )
                    .correlate(Action)
                    .exists()
                )
                query = query.where(or_(legacy, typed))
            else:
                query = query.where(legacy)
    if filters["apoio"]:
        has_supporters = (
            select(1)
            .where(ActionInstitution.acao_id == Action.id, ActionInstitution.papel == "APOIADOR")
            .correlate(Action)
            .exists()
        )
        supporters = (
            select(1)
            .where(
                ActionInstitution.acao_id == Action.id,
                ActionInstitution.papel == "APOIADOR",
                ActionInstitution.modalidade == filters["apoio"],
            )
            .correlate(Action)
            .exists()
        )
        query = query.where(
            or_(
                supporters,
                and_(
                    ~has_supporters, Action.institucional["apoio"].as_string() == filters["apoio"]
                ),
            )
        )
    for field, role in (("contratante", "CONTRATANTE"), ("apoiador", "APOIADOR")):
        if filters.get(field, "").strip():
            query = query.where(
                select(1)
                .select_from(ActionInstitution)
                .join(Institution)
                .where(
                    ActionInstitution.acao_id == Action.id,
                    ActionInstitution.papel == role,
                    Institution.nome.icontains(filters[field].strip(), autoescape=True),
                )
                .correlate(Action)
                .exists()
            )
    return query
