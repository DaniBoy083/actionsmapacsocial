"""Catálogo privado, imagens imutáveis e vínculos administrativos por ação."""

from difflib import SequenceMatcher
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import String, cast, delete, or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from app.domain.contracts import normalize
from app.domain.institutional import InstitutionLink
from app.domain.institutions import InstitutionInput
from app.infrastructure.models import ActionInstitution, Institution, InstitutionLogo


def key(value: str) -> str:
    return " ".join(normalize(value).split())


def register(session, data: InstitutionInput):
    normalized = key(data.nome)
    if len(normalized) < 2:
        raise HTTPException(422, "Informe o nome da instituição.")
    factory = pg_insert if session.bind.dialect.name == "postgresql" else sqlite_insert
    session.execute(
        factory(Institution)
        .values(
            id=str(uuid4()),
            nome=data.nome.strip(),
            nome_normalizado=normalized,
            tipo=data.tipo,
            aliases=sorted({key(alias) for alias in data.aliases}),
        )
        .on_conflict_do_nothing(index_elements=[Institution.nome_normalizado, Institution.tipo])
    )
    return session.scalar(
        select(Institution).where(
            Institution.nome_normalizado == normalized, Institution.tipo == data.tipo
        )
    )


def search(session, query: str):
    term = key(query)
    if len(term) < 2:
        return {"items": [], "fonte_externa_habilitada": False}
    # Busca parametrizada: aliases também são normalizados. Fuzzy é limitado e sinalizado.
    candidates = session.scalars(
        select(Institution)
        .where(
            or_(
                Institution.nome_normalizado.icontains(term, autoescape=True),
                cast(Institution.aliases, String).icontains(term, autoescape=True),
                Institution.nome_normalizado.startswith(term[:3], autoescape=True),
            )
        )
        .order_by(Institution.nome_normalizado, Institution.id)
        .limit(200)
    ).all()
    ranked = []
    for row in candidates:
        names = [row.nome_normalizado, *row.aliases]
        exact = term in names
        contains = any(term in name for name in names)
        score = max(SequenceMatcher(None, term, name).ratio() for name in names)
        if not contains and score < 0.65:
            continue
        ranked.append((not exact, not contains, -score, row))
    ranked.sort(key=lambda item: (*item[:3], item[3].nome_normalizado, item[3].id))
    selected = [item[3] for item in ranked[:20]]
    logos = {}
    if selected:
        for logo in session.scalars(
            select(InstitutionLogo)
            .where(InstitutionLogo.instituicao_id.in_([row.id for row in selected]))
            .order_by(InstitutionLogo.criado_em.desc(), InstitutionLogo.id)
        ):
            logos.setdefault(logo.instituicao_id, logo)
    return {
        "fonte_externa_habilitada": False,
        "items": [
            {
                "id": row.id,
                "nome": row.nome,
                "tipo": row.tipo,
                "correspondencia": "EXATA"
                if term in [row.nome_normalizado, *row.aliases]
                else "APROXIMADA",
                "logo_id": logos[row.id].id if row.id in logos else None,
                "origem": logos[row.id].origem if row.id in logos else "BASE_INTERNA",
                "verificacao": "CONFERENCIA_HUMANA_NECESSARIA",
            }
            for row in selected
        ],
    }


def persist_links(session, action_id, role, links, actor):
    from app.infrastructure.institutional import sanitize_logo

    result, ids = [], set()
    for order, link in enumerate(links):
        if link.instituicao_id:
            institution = session.get(Institution, str(link.instituicao_id))
            if (
                not institution
                or institution.tipo != link.tipo
                or key(link.nome) != institution.nome_normalizado
            ):
                raise HTTPException(
                    422, "Instituição selecionada não corresponde ao nome e tipo informados."
                )
        else:
            institution = register(session, InstitutionInput(nome=link.nome, tipo=link.tipo))
        if institution.id in ids:
            raise HTTPException(422, "Remova instituições repetidas no mesmo papel.")
        ids.add(institution.id)
        data = link.model_dump(mode="json", exclude={"conteudo_base64"})
        data.update(instituicao_id=institution.id, nome=institution.nome)
        if link.conteudo_base64 is not None:
            encoded, digest, width, height = sanitize_logo(link.conteudo_base64)
            logo = InstitutionLogo(
                instituicao_id=institution.id,
                conteudo_base64=encoded,
                sha256=digest,
                largura=width,
                altura=height,
                registrado_por=actor,
            )
            session.add(logo)
            session.flush()
            data["logo_id"] = logo.id
        elif link.logo_id:
            logo = session.get(InstitutionLogo, link.logo_id)
            if not logo or logo.instituicao_id != institution.id:
                raise HTTPException(422, "Logo não pertence à instituição selecionada.")
        result.append(InstitutionLink.model_validate(data).model_dump(mode="json"))
    session.execute(
        delete(ActionInstitution).where(
            ActionInstitution.acao_id == action_id, ActionInstitution.papel == role
        )
    )
    for order, data in enumerate(result):
        session.add(
            ActionInstitution(
                acao_id=action_id,
                instituicao_id=data["instituicao_id"],
                papel=role,
                modalidade=data["modalidade"],
                ordem=order,
                snapshot=data,
            )
        )
    return result
