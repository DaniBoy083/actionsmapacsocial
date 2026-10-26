# AC Actions Map — AC Social

Primeira entrega de desenvolvimento para gestão de ações institucionais e registros gerais de beneficiários. Não contém prontuários ou tracking clínico. A especificação específica em `docs/AC_ACTIONS_MAP_DOCUMENTACAO_AGENT.md` prevalece sobre o planejamento anterior.

Inclui login institucional, autorização no backend, dashboard, CRUD de ações com N locais da Paraíba, beneficiários cifrados, revisão manual/idempotente do documento histórico, indicadores, outbox e diagnóstico exclusivo de Tecnologia, páginas 404/erro e documentação de integração.

**Estado:** armazenamento operacional local isolado. PostgreSQL institucional usado somente para leitura da identidade; nenhuma migração, importação de pessoas reais, publicação externa ou deploy foi executado. Receptor da Agenda e persistência institucional do módulo ainda precisam de implementação/homologação. Consulte [conformidade e pendências](docs/CONFORMIDADE_E_PENDENCIAS.md).

## Rodar localmente no Windows

Requisitos: Node.js 22+, Python 3.12+, acesso de rede à base institucional para autenticação e as variáveis existentes de conexão fornecidas pela Tecnologia. Os comandos abaixo partem da raiz deste projeto e não exigem ativar scripts PowerShell.

Preparação inicial:

```powershell
npm.cmd ci
python -m venv backend/.venv
.\backend\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
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

Os cadastros ficam em `backend/private/actions.sqlite3`, ignorado pelo Git. Preserve o banco e `BENEFICIARIES_KEY` em backup controlado; perder/trocar a chave impede ler nomes já cifrados. Este banco é distinto da conexão institucional e a inicialização não cria tabelas no PostgreSQL. `APP_ENV=production` bloqueia o armazenamento SQLite até a implementação institucional homologada.

O assistente histórico lê a fonte privada já fornecida em `docs/data/ilovepdf_merged.pdf`; num novo clone esse arquivo não é distribuído. Sem a fonte, a interface informa indisponibilidade. Não colocar fichas em `/public` nem versionar transcrições. A revisão é manual, página a página, sem OCR externo. Upload genérico ainda está pendente.

## Verificação

Validação local desta entrega: **34 testes backend e 10 cenários de navegador aprovados**, incluindo acessibilidade automatizada em desktop/celular; lint, TypeScript, Ruff e build aprovados. Detalhes e limites estão no [registro de conformidade](docs/CONFORMIDADE_E_PENDENCIAS.md).

```powershell
npm.cmd run lint
npm.cmd run typecheck
npm.cmd run build
npm.cmd run test:backend
.\backend\.venv\Scripts\python.exe -m ruff check --config backend/pyproject.toml backend/app backend/tests scripts
npx.cmd playwright install chromium
npm.cmd run test:e2e
```

Playwright inicia frontend/backend próprios nas portas **3100/8100**, usa identidades sintéticas, documento sintético e SQLite temporário. Nenhum cadastro real é necessário e não há gravação institucional. Essas portas devem estar livres. O Chromium é baixado apenas na preparação do ambiente. Capturas/relatórios ficam ignorados em `artifacts/` e `test-results/`.

Para executar o frontend compilado, mantenha o backend aberto e use `npm.cmd run build`, depois `npm.cmd start`. Isso permite testar o build local; não significa que o sistema está homologado para produção.

Para regenerar os contratos sem acessar dados:

```powershell
.\backend\.venv\Scripts\python.exe scripts/export_contracts.py
```

A API local oferece documentação em **http://127.0.0.1:8000/docs**. O diagnóstico real somente leitura pode ser repetido com `python scripts/inspect_database.py` no ambiente virtual; ele imprime apenas resultado e metadados, sem segredos ou linhas pessoais.

## Documentação

- [Descoberta, fontes verificadas e inventário de campos](docs/DESCOBERTA_E_CAMPOS.md)
- [Arquitetura e limites desta entrega](docs/ARQUITETURA.md)
- [O que implementar na Agenda Digital](docs/AGENDA_DIGITAL_IMPLEMENTACAO.md)
- [Privacidade, retenção e plano de migração](docs/PRIVACIDADE_E_MIGRACAO.md)
- [Conformidade e próximos incrementos](docs/CONFORMIDADE_E_PENDENCIAS.md)
- [OpenAPI privado](docs/contracts/actions-map.openapi.json) e [schema de resumo para Agenda](docs/contracts/agenda-summary.schema.json)

Somente após implementar/homologar o receptor, configurar `AGENDA_SUMMARIES_URL` e `AGENDA_SERVICE_TOKEN` no backend. O worker é explícito; não envia automaticamente. Com `PYTHONPATH=backend`, executar `python -m app.infrastructure.outbox`. O fluxo obrigatório permanece Map → Agenda → Plataforma → Portal, sem dados pessoais. A publicação no Portal permanece bloqueada até essa homologação.
