# AC Actions Map — AC Social

Primeira entrega de desenvolvimento para gestão de ações institucionais e registros gerais de beneficiários. Não contém prontuários ou tracking clínico. A especificação específica em `docs/AC_ACTIONS_MAP_DOCUMENTACAO_AGENT.md` prevalece sobre o planejamento anterior.

Inclui login institucional, autorização no backend, Visão geral com indicadores, CRUD de ações com N locais da Paraíba, beneficiários cifrados, importação revisada por PDF/CSV/JSON, outbox e diagnóstico exclusivo de Tecnologia, páginas 404/erro e documentação de integração.

**28/10/2026 — Cadastro e segunda via:** formulários, importação, edição e consulta privada incluem os campos gerais da ficha de referência, com CPF, telefone, datas, responsável e declaração de recebimento; graus e dados oculares são excluídos. A segunda via permite impressão A4. A página `/mapa-acoes`, sua API, navegação e dependências foram removidas por decisão posterior do responsável. [Campos, operação e resultado da complementação](docs/CADASTRO_BENEFICIARIOS_E_SEGUNDA_VIA.md) e [auditoria atual dos princípios](docs/AUDITORIA_APLICACAO_E_PRINCIPIOS.md).

**Estado:** desenvolvimento com SQLite isolado; produção com Next.js + FastAPI na Vercel, PostgreSQL em schema próprio e credencial restrita. As 50 fichas da Melhor Visão foram importadas; a complementação autorizada preencheu 294 campos e a leitura posterior conferiu 294/294 valores. Campos ausentes/ilegíveis permanecem pendentes. Receptor e exportação agregada de ações estão implementados na Agenda. Este commit ainda precisa de deploy para disponibilizar os novos formulários e remover a página antiga no ambiente publicado. Homologação do fluxo institucional e demais pendências estão na [auditoria atual](docs/AUDITORIA_APLICACAO_E_PRINCIPIOS.md). Consulte também [deploy](docs/DEPLOY_PRODUCAO.md) e [conformidade](docs/CONFORMIDADE_E_PENDENCIAS.md).

## Rodar localmente no Windows

**Gestão de integrações:** criação, rotação e revogação de tokens de leitura para a Agenda, com validade por prazo ou **Nunca expirar**, confirmação da senha institucional, cópia de endpoints/cURL e exportação agregada consistente. Em PostgreSQL, aplicar as migrações até `0006_nonexpiring_tokens` antes do deploy desta funcionalidade. Para SQLite local existente, há atualização administrativa própria. Veja [gestão de tokens e instalação](docs/GESTAO_TOKENS_E_ENDPOINTS_AGENDA.md). Esta alteração foi preparada para commit; seu push/deploy e a migração produtiva ficam com o operador.

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

As ações são salvas diretamente **Em revisão**, depois validadas e publicadas. O estado anterior de rascunho foi removido. A publicação envia à Agenda número de pessoas contempladas, quantidade de ações e municípios, com ACK e sem dados pessoais. Consulte [fluxo de publicação e contrato 1.1](docs/PUBLICACAO_E_FLUXO_DE_ACOES.md).

## Verificação

Validação desta revisão: **105 testes backend e 20 cenários de navegador aprovados**; os quatro cenários específicos de beneficiários foram repetidos após o ajuste de impressão. Lint, TypeScript, Ruff, `pip check` e build aprovados; inspeção visual da segunda via em uma página A4. Evidências na [auditoria atual](docs/AUDITORIA_APLICACAO_E_PRINCIPIOS.md). A homologação institucional continua pendente. A contagem anterior incluía testes do mapa agora removido.

```powershell
npm.cmd run lint
npm.cmd run typecheck
npm.cmd run build
npm.cmd run test:backend
.\backend\.venv\Scripts\python.exe -m ruff check --config backend/pyproject.toml backend/app backend/tests scripts
npx.cmd playwright install chromium
npm.cmd run test:e2e
```

Playwright inicia frontend compilado/backend próprios nas portas **3310/8310**; execute `npm.cmd run build` antes. Usa identidades sintéticas, documento sintético e SQLite temporário. Nenhum cadastro real é necessário e não há gravação institucional. Essas portas devem estar livres; use `ACTIONS_E2E_FRONTEND_PORT` e `ACTIONS_E2E_BACKEND_PORT` para escolher outras portas de teste. O Chromium é baixado apenas na preparação do ambiente. Capturas/relatórios ficam ignorados em `artifacts/` e `test-results/`.

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
- [Cadastro completo, segunda via e complementação do PDF](docs/CADASTRO_BENEFICIARIOS_E_SEGUNDA_VIA.md)
- [Auditoria atual da aplicação e princípios](docs/AUDITORIA_APLICACAO_E_PRINCIPIOS.md)
- [O que implementar na Agenda Digital](docs/AGENDA_DIGITAL_IMPLEMENTACAO.md)
- [Publicação e fluxo das ações](docs/PUBLICACAO_E_FLUXO_DE_ACOES.md)
- [Privacidade, retenção e plano de migração](docs/PRIVACIDADE_E_MIGRACAO.md)
- [Conformidade e próximos incrementos](docs/CONFORMIDADE_E_PENDENCIAS.md)
- [OpenAPI privado](docs/contracts/actions-map.openapi.json) e [schema de resumo para Agenda](docs/contracts/agenda-summary.schema.json)

O backend usa `AGENDA_SUMMARIES_URL` e `AGENDA_SERVICE_TOKEN` para o receptor implementado na Agenda. Mutações tentam sincronizar em background; Tecnologia dispõe de sincronização manual auditada. O worker por CLI (`PYTHONPATH=backend`, `python -m app.infrastructure.outbox`) permite retentar sem tráfego. O fluxo segue Map → Agenda → Plataforma → Portal, sem dados pessoais. A Plataforma deve consumir a nova exportação antes de atualizar o mapa público.
