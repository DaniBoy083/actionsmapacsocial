# AC Actions Map — AC Social

Primeira entrega de desenvolvimento para gestão de ações institucionais e registros gerais de beneficiários. Não contém prontuários ou tracking clínico. A especificação específica em `docs/AC_ACTIONS_MAP_DOCUMENTACAO_AGENT.md` prevalece sobre o planejamento anterior.

Inclui login institucional, autorização no backend, Visão geral com indicadores, CRUD de ações com N locais da Paraíba, beneficiários cifrados, importação revisada por PDF/CSV/JSON, outbox e diagnóstico exclusivo de Tecnologia, páginas 404/erro e documentação de integração.

**Estado:** desenvolvimento com SQLite isolado; produção com Next.js + FastAPI no mesmo projeto Vercel, PostgreSQL institucional em schema próprio e credencial restrita. A ação Melhor Visão/Mamanguape e 32 registros nominais conferidos foram importados com autorização expressa; 18 páginas aguardam confirmação da grafia. Consulte [deploy de produção](docs/DEPLOY_PRODUCAO.md) e [conformidade e pendências](docs/CONFORMIDADE_E_PENDENCIAS.md). A integração receptora da Agenda permanece pendente.

## Rodar localmente no Windows

Requisitos: Node.js 22+, Python 3.12+, acesso de rede à base institucional para autenticação e as variáveis existentes de conexão fornecidas pela Tecnologia. Os comandos abaixo partem da raiz deste projeto e não exigem ativar scripts PowerShell.

Preparação inicial:

```powershell
npm.cmd ci
python -m venv backend/.venv
.\backend\.venv\Scripts\python.exe -m pip install -r backend/requirements-dev.txt
.\backend\.venv\Scripts\python.exe scripts/setup_local.py
```

`setup_local.py` acrescenta somente configurações locais ausentes em `.env.local`, preserva a conexão já configurada e gera segredos sem exibi-los. Se estiver montando um ambiente novo, use `.env.example` como referência e obtenha `DATABASE_URL` com a Tecnologia; não sobrescreva os arquivos de ambiente existentes. Não há senha de demonstração na aplicação.

No primeiro terminal, inicie o backend:

```powershell
.\backend\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload --no-access-log
```

No segundo terminal:

```powershell
npm.cmd run dev
```

Abra **http://localhost:3000**. Entre com o e-mail/senha institucionais de profissional com `user_type=administracao` e equipe Administração ou Tecnologia. Equipe/tipo não são escolhidos no formulário. Contas com senha legada sem hash precisam de atualização pela Agenda Digital. A página `/tecnologia/conexao` exige Tecnologia também no FastAPI.

Não troque `localhost` por `127.0.0.1` no navegador sem atualizar `FRONTEND_ORIGIN`. O host/origem exatos fazem parte da proteção CSRF. `ACTIONS_API_URL` é configuração privada do Next; `DATABASE_URL`, `SESSION_SECRET`, `BENEFICIARIES_KEY` e o token da Agenda nunca recebem prefixo `NEXT_PUBLIC_`.

Localmente, os cadastros ficam em `backend/private/actions.sqlite3`, ignorado pelo Git. Preserve o banco e `BENEFICIARIES_KEY` em backup controlado; perder/trocar a chave impede ler nomes já cifrados. A inicialização local não cria tabelas no PostgreSQL. Em produção, `APP_ENV=production` exige PostgreSQL/TLS e usa o schema `actions_map`; a migração administrativa não é executada no startup.

A página **Importar dados** (`/importacoes`) recebe PDF, CSV e JSON, com prévia, revisão por registro, ação de destino e confirmação. Até 8 MiB e 200 páginas/registros por arquivo; arquivos temporários cifrados, privados e com expiração técnica de 24 horas. `/dados-iniciais` redireciona para ela. A página `/indicadores` foi removida; os totais permanecem em Visão geral. Consulte [formatos, limites e operação](docs/IMPORTACAO_ARQUIVOS.md). O acervo original de aproximadamente 241 MB permanece local e usa carga assistida com revisão, sem upload público.

## Verificação

Validação da revisão de importações: **61 testes backend aprovados**; testes de navegador em desktop/celular, acessibilidade, lint, TypeScript, Ruff e build são registrados na [revisão dos princípios](docs/REVISAO_PRINCIPIOS_2026-10-26.md). A integração externa e a homologação institucional continuam pendentes.

```powershell
npm.cmd run lint
npm.cmd run typecheck
npm.cmd run build
npm.cmd run test:backend
.\backend\.venv\Scripts\python.exe -m ruff check --config backend/pyproject.toml backend/app backend/tests scripts
npx.cmd playwright install chromium
npm.cmd run test:e2e
```

Playwright inicia frontend compilado/backend próprios nas portas **3100/8100**; execute `npm.cmd run build` antes. Usa identidades sintéticas, documento sintético e SQLite temporário. Nenhum cadastro real é necessário e não há gravação institucional. Essas portas devem estar livres. O Chromium é baixado apenas na preparação do ambiente. Capturas/relatórios ficam ignorados em `artifacts/` e `test-results/`.

Para executar o frontend compilado, mantenha o backend aberto e use `npm.cmd run build`, depois `npm.cmd start`. Isso permite testar o build local; não significa que o sistema está homologado para produção.

Para regenerar os contratos sem acessar dados:

```powershell
.\backend\.venv\Scripts\python.exe scripts/export_contracts.py
```

A API local oferece documentação em **http://127.0.0.1:8000/docs**. O diagnóstico real somente leitura pode ser repetido com `python scripts/inspect_database.py` no ambiente virtual; ele imprime apenas resultado e metadados, sem segredos ou linhas pessoais.

## Documentação

- [Descoberta, fontes verificadas e inventário de campos](docs/DESCOBERTA_E_CAMPOS.md)
- [Arquitetura e limites desta entrega](docs/ARQUITETURA.md)
- [Deploy Next.js + FastAPI na mesma Vercel](docs/DEPLOY_PRODUCAO.md)
- [Importação de PDF, CSV e JSON](docs/IMPORTACAO_ARQUIVOS.md)
- [Revisão dos princípios e evidências](docs/REVISAO_PRINCIPIOS_2026-10-26.md)
- [O que implementar na Agenda Digital](docs/AGENDA_DIGITAL_IMPLEMENTACAO.md)
- [Privacidade, retenção e plano de migração](docs/PRIVACIDADE_E_MIGRACAO.md)
- [Conformidade e próximos incrementos](docs/CONFORMIDADE_E_PENDENCIAS.md)
- [OpenAPI privado](docs/contracts/actions-map.openapi.json) e [schema de resumo para Agenda](docs/contracts/agenda-summary.schema.json)

Somente após implementar/homologar o receptor, configurar `AGENDA_SUMMARIES_URL` e `AGENDA_SERVICE_TOKEN` no backend. O worker é explícito; não envia automaticamente. Com `PYTHONPATH=backend`, executar `python -m app.infrastructure.outbox`. O fluxo obrigatório permanece Map → Agenda → Plataforma → Portal, sem dados pessoais. A publicação no Portal permanece bloqueada até essa homologação.
