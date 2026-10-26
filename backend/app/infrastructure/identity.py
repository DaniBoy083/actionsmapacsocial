import hashlib
import hmac
import re

from sqlalchemy import text

from app.config import get_settings
from app.domain.contracts import Professional, normalize
from app.infrastructure.database import get_identity_engine


class IdentityRepository:
    """Contrato real da Agenda; somente leitura, revalidado por requisição."""

    def find(self, value: str, by_id: bool = False) -> tuple[Professional, str] | None:
        column = "p.id" if by_id else "lower(trim(p.email))"
        query = text(f"""
          SELECT p.id, p.display_name, p.password, p.user_type,
            coalesce(array_agg(e.name) FILTER (WHERE e.name IS NOT NULL), '{{}}') teams
          FROM public.profissionais_cadastrados p
          LEFT JOIN public.equipes_profissionais e
            ON e.professional_ids_json @> jsonb_build_array(p.id)
          WHERE {column} = :value GROUP BY p.id LIMIT 2
        """)
        params = {"value": value}
        if get_settings().production:
            # RLS do cadastro mestre permanece ativo. O runtime só recebe EXECUTE
            # em uma consulta vinculada a identificador, sem SELECT direto no cadastro.
            query = text("SELECT * FROM actions_map.authentication_identity(:value, :by_id)")
            params["by_id"] = by_id
        with get_identity_engine().connect() as conn, conn.begin():
            conn.execute(text("SET TRANSACTION READ ONLY"))
            conn.execute(text("SET LOCAL statement_timeout = '8s'"))
            rows = conn.execute(query, params).mappings().all()
        if len(rows) != 1:
            return None
        row = rows[0]
        teams = {normalize(team) for team in row["teams"]}
        team = (
            "tecnologia"
            if "tecnologia" in teams
            else ("administracao" if "administracao" in teams else "outro")
        )
        return Professional(
            profissional_id=row["id"],
            nome=row["display_name"],
            tipo_login=normalize(row["user_type"]),
            equipe=team,
        ), row["password"]


def verify_password(password: str, digest: str) -> bool:
    # Agenda: scryptSync(password, hexadecimal salt as UTF-8 text, 64).
    # Contas legadas devem ser atualizadas na Agenda; não há fallback plaintext.
    matched = bool(re.fullmatch(r"[0-9a-f]{32}:[0-9a-f]{128}", digest))
    salt, expected = digest.split(":") if matched else ("0" * 32, "0" * 128)
    actual = hashlib.scrypt(
        password.encode(), salt=salt.encode(), n=16384, r=8, p=1, dklen=64, maxmem=64 * 1024 * 1024
    ).hex()
    return hmac.compare_digest(actual, expected) and matched
