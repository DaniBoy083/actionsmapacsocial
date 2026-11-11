from typing import Literal

from fastapi import Query

from app.infrastructure.models import Action


def institutional_filters(
    instrumento: str = Query("", max_length=160),
    numero_instrumento: str = Query("", max_length=80),
    autor: str = Query("", max_length=160),
    orgao: str = Query("", max_length=160),
    clinica: str = Query("", max_length=160),
    apoio: Literal["", "TOTAL", "PARCIAL"] = "",
) -> dict:
    return {
        "instrumento": instrumento,
        "numero_instrumento": numero_instrumento,
        "autor": autor,
        "orgao": orgao,
        "clinica": clinica,
        "apoio": apoio,
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
            query = query.where(
                Action.institucional[section][field]
                .as_string()
                .icontains(
                    filters[key].strip(),
                    autoescape=True,
                )
            )
    if filters["apoio"]:
        query = query.where(Action.institucional["apoio"].as_string() == filters["apoio"])
    return query
