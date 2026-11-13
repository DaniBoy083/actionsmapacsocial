"""Processo descartável de demonstração. Nunca importado pelo runtime institucional."""

import argparse
import hashlib
import os
import secrets
import tempfile
from contextlib import nullcontext
from pathlib import Path

import pymupdf
import uvicorn
from cryptography.fernet import Fernet
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

DEMO_PASSWORD = "Demonstracao-local-2026!"
DEMO_ACCOUNTS = {
    "admin@demo.invalid": ("demo-admin", "administracao", "Administração de demonstração"),
    "tecnologia@demo.invalid": ("demo-tech", "tecnologia", "Tecnologia de demonstração"),
}


def refuse_hosted_environment() -> None:
    if os.environ.get("APP_ENV", "").lower() == "production" or os.environ.get("VERCEL"):
        raise RuntimeError("Demonstração permitida somente em processo local separado.")


def isolated_environment(directory: Path, frontend_port: int) -> dict[str, str]:
    """Sobrescreve todos os settings conhecidos, incluindo aliases de .env local."""
    return {
        "APP_ENV": "demo",
        "ACTIONS_DATABASE_URL": "",
        "DATABASE_URL": "",
        "POSTGRES_DATABASE_URL": "",
        "POSTGRES_URL": "",
        "ACTIONS_STORAGE_URL": "sqlite:///" + (directory / "demo.sqlite3").as_posix(),
        "SESSION_SECRET": secrets.token_urlsafe(48),
        "BENEFICIARIES_KEY": Fernet.generate_key().decode(),
        "CLINICAL_FIELDS_ENABLED": "true",
        "OPERATIONAL_ACCESS_ENABLED": "true",
        "CLINICAL_KEY": Fernet.generate_key().decode(),
        "FRONTEND_ORIGIN": f"http://localhost:{frontend_port}",
        "AGENDA_WEB_URL": "",
        "AGENDA_SUMMARIES_URL": "",
        "AGENDA_SERVICE_TOKEN": "",
    }


class DemoIdentities:
    def __init__(self):
        salt = secrets.token_hex(16)
        self.password_hash = (
            salt
            + ":"
            + hashlib.scrypt(
                DEMO_PASSWORD.encode(), salt=salt.encode(), n=16384, r=8, p=1, dklen=64
            ).hex()
        )

    def find(self, value: str, by_id: bool = False):
        from app.domain.contracts import Professional

        for email, (identifier, team, name) in DEMO_ACCOUNTS.items():
            if value == (identifier if by_id else email):
                return Professional(
                    profissional_id=identifier,
                    nome=name,
                    tipo_login="administracao",
                    equipe=team,
                ), self.password_hash
        return None


def seed_demo(app) -> None:
    """Usa os contratos/regras reais; sem importar fixtures de testes ou fontes privadas."""
    from app.config import get_settings

    with TestClient(app) as client:
        client.headers["Origin"] = get_settings().frontend_origin

        def call(method, path, data=None):
            response = client.request(method, "/api/v1" + path, json=data)
            if not response.is_success:
                raise RuntimeError(f"Preparação sintética recusada: {response.status_code}.")
            return response.json() if response.content else None

        call(
            "POST",
            "/auth/login",
            {
                "identifier": "tecnologia@demo.invalid",
                "password": DEMO_PASSWORD,
            },
        )
        client.headers["X-CSRF-Token"] = call("GET", "/auth/me")["csrf_token"]
        operators = []
        for category, name, username in [
            ("MEDICO", "Oftalmologista fictício DEMO", "oftalmo.demo"),
            ("OPTOMETRISTA", "Optometrista fictício DEMO", "opto.demo"),
            ("RECEPCAO", "Recepcionista fictício DEMO", "recepcao.demo"),
        ]:
            data = {"nome": name, "categoria": category}
            if category != "RECEPCAO":
                data.update(
                    registro_conselho="CRM" if category == "MEDICO" else "REGISTRO-DEMO",
                    registro_numero="DEMO-OP-" + category,
                    registro_uf="PB",
                    habilitacao_validada=True,
                    habilitacao_referencia="SIMULAÇÃO de demonstração, sem validade",
                    registro_clinico_autorizado=True,
                    autorizacao_clinica_referencia="SIMULAÇÃO descartável",
                )
            staff = call("POST", "/profissionais", data)
            call(
                "PUT",
                f"/profissionais/{staff['id']}/acesso",
                {
                    "usuario": username,
                    "nova_senha": DEMO_PASSWORD,
                    "senha_institucional": DEMO_PASSWORD,
                },
            )
            operators.append(staff)
        for index, (city, code) in enumerate(
            [
                ("João Pessoa", "2507507"),
                ("Campina Grande", "2504009"),
                ("Santa Rita", "2513703"),
            ]
        ):
            action = call(
                "POST",
                "/acoes",
                {
                    "nome": f"DEMO — Saúde ocular em {city}",
                    "categoria": "Saúde ocular",
                    "descricao": "Cenário fictício e descartável para apresentação da aplicação.",
                    "resumo_publico": "Demonstração com dados sintéticos, sem atendimento real.",
                    "inicio_em": "2026-11-10",
                    "fim_em": "2026-11-13",
                    "locais": [
                        {"municipio_ibge": code, "nome_local": "Unidade fictícia Centro"},
                        *(
                            [{"municipio_ibge": code, "nome_local": "Unidade fictícia Bairro"}]
                            if index == 0
                            else []
                        ),
                    ],
                    "institucional": {
                        "instrumento": {
                            "tipo": "EMENDA" if index == 0 else "CONVENIO",
                            "nome": "Instrumento fictício de demonstração",
                            "numero": f"DEMO-00{index + 1}/2026",
                            "autor": "Autor fictício" if index == 0 else "",
                        },
                        "contratantes": [{"nome": "Instituição fictícia DEMO", "tipo": "OUTRO"}],
                        "apoiadores": [
                            {
                                "nome": "Clínica fictícia DEMO",
                                "tipo": "CLINICA",
                                "modalidade": "TOTAL" if index == 0 else "PARCIAL",
                            }
                        ],
                    },
                },
            )
            url = "/acoes/" + action["id"]
            for number in range(1, 5):
                call(
                    "POST",
                    url + "/beneficiarios",
                    {
                        "nome": f"Pessoa fictícia DEMO {index * 4 + number:02}",
                        "local_indice": (number % 2) if index == 0 else 0,
                        "municipio_residencia_ibge": code,
                        "observacoes": "Exemplo sintético. Não representa pessoa real.",
                    },
                )
            action = call("GET", url)
            for staff in operators if index == 0 else []:
                call(
                    "POST",
                    url + "/atribuicoes",
                    {
                        "profissional_id": staff["id"],
                        "acao_versao": action["versao"],
                        "profissional_versao": staff["versao"],
                        **(
                            {"locais_indices": [1 if staff["categoria"] == "OPTOMETRISTA" else 0]}
                            if staff in operators
                            else {}
                        ),
                    },
                )
            if index == 0:
                people = sorted(
                    call("GET", url + "/beneficiarios")["items"], key=lambda item: item["nome"]
                )
                for target, staff in zip(people[1:3], operators[:2], strict=True):
                    call(
                        "PUT",
                        url + f"/beneficiarios/{target['id']}/designacao-clinica",
                        {
                            "profissional_id": staff["id"],
                        },
                    )
                example_clinical_url = (
                    "/operacao" + url + "/beneficiarios/" + people[1]["id"] + "/clinica"
                )
            if index < 2:
                action = call("POST", url + "/aprovar", {"versao": action["versao"]})
        call("POST", "/auth/logout", {})
        call(
            "POST",
            "/operacao/auth/login",
            {"identifier": "oftalmo.demo", "password": DEMO_PASSWORD},
        )
        client.headers["X-CSRF-Token"] = call("GET", "/operacao/auth/me")["csrf_token"]
        call(
            "PUT",
            example_clinical_url,
            {"versao": 0, "campos": {"lentes": "EXEMPLO FICTÍCIO — sem validade clínica"}},
        )
        call("POST", "/operacao/auth/logout", {})


def create_demo_app(directory: Path, frontend_port: int):
    refuse_hosted_environment()
    if not directory.is_dir() or any(directory.iterdir()):
        raise RuntimeError("A demonstração exige um diretório temporário novo e vazio.")
    os.environ.update(isolated_environment(directory.resolve(), frontend_port))

    from app.config import get_settings
    from app.infrastructure import imports
    from app.infrastructure.database import get_engine, get_identity_engine
    from app.main import app
    from app.security.session import identities

    if get_engine.cache_info().currsize or get_identity_engine.cache_info().currsize:
        raise RuntimeError("Execute a demonstração em um processo novo.")
    get_settings.cache_clear()
    app.state.demonstracao = True
    app.state.session_cookie = "ac_actions_demo_session"
    app.dependency_overrides[identities] = DemoIdentities
    imports.SOURCE = directory / "origem-sintetica.pdf"
    with pymupdf.open() as document:
        for number in range(1, 3):
            page = document.new_page()
            page.insert_text((50, 60), "DEMONSTRACAO - SEM DADOS REAIS OU VALIDADE CLINICA")
            page.insert_text((50, 100), f"Nome: Pessoa ficticia para importacao {number}")
        document.save(imports.SOURCE)

    @app.middleware("http")
    async def demo_boundaries(request, call_next):
        path = request.url.path
        if (
            path.startswith("/api/v1/integracoes/")
            or path == "/api/v1/tecnologia/sincronizar-agenda"
            or path == "/api/v1/importacoes/arquivos"
        ):
            return JSONResponse(
                {
                    "detail": "Demonstração: use apenas a fonte sintética; integração externa bloqueada."
                },
                status_code=403,
                headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
            )
        return await call_next(request)

    seed_demo(app)
    return app


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8300)
    parser.add_argument("--frontend-port", type=int, default=3300)
    parser.add_argument("--runtime-dir", type=Path)
    args = parser.parse_args()
    if any(port < 1024 or port > 65535 for port in [args.port, args.frontend_port]):
        parser.error("Use portas entre 1024 e 65535.")
    refuse_hosted_environment()
    if args.runtime_dir and (
        args.runtime_dir.resolve().parent != Path(tempfile.gettempdir()).resolve()
        or not args.runtime_dir.name.startswith("actionsmap-demo-")
        or args.runtime_dir.is_symlink()
    ):
        parser.error("Diretório de execução deve ser temporário e exclusivo da demonstração.")
    context = (
        nullcontext(str(args.runtime_dir.resolve()))
        if args.runtime_dir
        else tempfile.TemporaryDirectory(prefix="actionsmap-demo-")
    )
    with context as temporary:
        try:
            app = create_demo_app(Path(temporary), args.frontend_port)
            uvicorn.run(app, host="127.0.0.1", port=args.port, access_log=False)
        finally:
            from app.infrastructure.database import get_engine

            if get_engine.cache_info().currsize:
                get_engine().dispose()


if __name__ == "__main__":
    main()
