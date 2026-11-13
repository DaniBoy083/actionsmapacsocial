# AC Actions Map — AC Social

Aplicação para gestão de ações institucionais, beneficiários e registro clínico segregado
com liberação controlada. O fluxo completo de exame/documentos/etiqueta ainda não está concluído.

**13/11/2026 — Demonstração local:** `npm.cmd run demo` inicia frontend e backend
com banco descartável, três ações e 12 pessoas fictícias, sem credenciais
institucionais. Sessão própria, avisos de demonstração e impressos identificados;
fonte histórica substituída por PDF sintético e integrações externas bloqueadas.
[Comandos, auditoria de princípios, limites e reversão](docs/DEMONSTRACAO_LOCAL_2026-11-13.md).
Conformidade global continua **parcial**; o demo não libera uso clínico real.

**12/11/2026 — Plano consolidado, API interna 0.3.0:** N contratantes e N apoiadores
separados, modalidade por apoiador, catálogo interno reutilizável, busca de nomes/
aliases e logos com escolha explícita, designação individual de atendimentos,
Oftalmologista e registro de optometrista, filtros e paginação SQL sem N+1.
**Exige a migração aditiva `0010_institutions_and_cases` antes de servir esta versão.**
Nenhuma migração, configuração ou publicação de produção foi executada nesta
entrega. Autenticação operacional, emissão clínica/etiqueta homologada, logos
externas e contrato público novo continuam com gates próprios. Conformidade
global **parcial**. [Implementação, auditoria, testes e reversão](docs/IMPLEMENTACAO_PLANO_2026-11-12.md).

**11/11/2026 — Ativação em produção autorizada:** migrações `0007`–`0009` aplicadas,
chave clínica sensível própria e `CLINICAL_FIELDS_ENABLED=true` configuradas somente
em produção. O commit `7a9aadf` foi republicado e o domínio público está no deployment
validado. Backup cifrado restaurado em ambiente descartável, registros anteriores,
RLS e permissões conferidos; testes externos de acesso negado aprovados.
[Evidências, limites e reversão da ativação](docs/ATIVACAO_PRODUCAO_2026-11-11.md).
O uso clínico ainda exige vínculo individual, habilitação e atribuição válidos.

**11/11/2026 — Profissionais e campos clínicos:** cadastro de médico/optometrista/recepção,
atribuições por ação/local, conferência de habilitação, autorização clínica específica,
revogação e históricos privados. Incluídos os 13 campos da ficha original, cifrados
separadamente, com controle por identidade/profissional/ação/local/caso e versões.
Permanecem **em preenchimento**; não geram prescrição, conclusão de exame ou etiqueta.
`CLINICAL_FIELDS_ENABLED=false` continua sendo o padrão do código; a ativação exige
`CLINICAL_KEY` própria e aprovação operacional. A entrega de código manteve o recurso
desligado; a ativação posterior em produção está registrada acima.
[Implementação, matriz de campos, operação e rollback](docs/PROFISSIONAIS_E_CAMPOS_CLINICOS_2026-11-11.md).

**11/11/2026 — Etapa administrativa implementada:** cadastro de apoio e emenda/convênio
(nome, número textual e autor), órgão/clínica com duas logos opcionais e permissões
separadas de uso/divulgação, histórico privado, cabeçalho com três marcas na
segunda via geral, snapshot administrativo e filtros internos. Main foi conferida
com `origin/main` antes das edições. **AC Auth e AC Core não foram alterados.**
[Implementação, testes, limites e rollback](docs/IMPLEMENTACAO_ADMINISTRATIVA_2026-11-11.md).
O banco existente precisa das migrações aditivas até **0009 antes de servir esta versão**;
a sequência foi aplicada em produção na ativação autorizada de 11/11, após backup
cifrado, restauração e ensaio em base descartável.
Para SQLite local, há prévia/atualização controlada em
`scripts/migrate_institutional_metadata.py`; não é migração automática de startup.
Conclusão clínica, etiqueta, identidade operacional exclusiva e contrato 1.2 continuam pendentes.
Não há declaração de conformidade absoluta nem liberação do piloto clínico.

**03/11/2026 — AC-Core:** [diagnóstico, contratos pendentes e handoff técnico](docs/AC_CORE_PENDING_IMPLEMENTATIONS.md).
O handoff disponível mantém a transição administrativa em proposta. Esta entrega
documenta as dependências; não implementa nem ativa SSO, Management, Gateway ou
Vault. O login institucional vigente e o pipeline com a Agenda permanecem ativos
no código. Contratos reais e homologação são necessários antes de substituí-los.

Os requisitos vigentes são `AGENTS.md`, `PROMPT_INICIAL_SOL.md` e o adendo de 30/10
de [PLANO_ACTIONS_MAP_GPT61_SOL.md](docs/PLANO_ACTIONS_MAP_GPT61_SOL.md), que prevalecem
sobre as especificações históricas.

**30/10/2026 — Fase 0:** [ficha real, campos, código/schema e permissões](docs/FASE_0_DESCOBERTA_2026-10-30.md)
inventariados; [modelo proposto, backlog e testes de aceite](docs/PLANO_MVP_E_ACEITE_2026-10-30.md)
documentados. A fonte XLSX preenchida foi retirada do índice Git, preservada no
disco e protegida pelo gate de privacidade. Em novos clones, obtenha esse anexo por
canal privado. **O novo MVP não está homologado nem integralmente implementado**;
[auditoria atual e evidências](docs/AUDITORIA_APLICACAO_E_PRINCIPIOS.md).

Inclui login institucional, autorização no backend, Visão geral com indicadores, CRUD de ações com N locais da Paraíba, beneficiários cifrados, importação revisada por PDF/CSV/JSON, outbox e diagnóstico exclusivo de Tecnologia, páginas 404/erro e documentação de integração.

**28/10/2026 — Cadastro e segunda via:** formulários, importação, edição e consulta privada incluem os campos gerais da ficha de referência, com CPF, telefone, datas, responsável e declaração de recebimento; graus e dados oculares são excluídos. A segunda via permite impressão A4. A página `/mapa-acoes`, sua API, navegação e dependências foram removidas por decisão posterior do responsável. [Campos, operação e resultado da complementação](docs/CADASTRO_BENEFICIARIOS_E_SEGUNDA_VIA.md) e [auditoria atual dos princípios](docs/AUDITORIA_APLICACAO_E_PRINCIPIOS.md).

**Estado do código:** desenvolvimento com SQLite isolado; adaptador produtivo
Next.js + FastAPI/PostgreSQL em schema próprio. Os relatos de carga das 50 fichas,
complemento de 294 campos e recebimento na Agenda são evidências históricas de
26–28/10; o recebimento na Agenda não foi reexecutado nesta ativação. Em 11/11,
o deployment e a revisão `0009` foram conferidos, preservando 1 ação, 50 cadastros
e 50 participações. Campos ausentes/ilegíveis permanecem pendentes.
Consulte [ativação atual](docs/ATIVACAO_PRODUCAO_2026-11-11.md),
[deploy histórico](docs/DEPLOY_PRODUCAO.md),
[conformidade](docs/CONFORMIDADE_E_PENDENCIAS.md) e a auditoria atual.

## Rodar localmente no Windows

### Demonstração para apresentações

Requisitos: Node.js 22+ e **Python 3.12**. Na raiz do projeto, prepare uma vez:

```powershell
npm.cmd ci
python --version
python -m venv backend/.venv
.\backend\.venv\Scripts\python.exe -m pip install -r backend/requirements-dev.txt
```

Confira que `python --version` informa **3.12.x**. O comando `py -3.12` pode
falhar quando o Python 3.12 está instalado, mas não está registrado no launcher
do Windows. Se `backend/.venv` já existe e funciona, não precisa recriá-lo ou
reinstalar as dependências para iniciar o demo.

Para iniciar os dois servidores em um terminal:

```powershell
npm.cmd run demo
```

Abra **http://localhost:3300**. Na tela de acesso, use **Preencher acesso de
Administração** ou **Preencher acesso de Tecnologia** e clique em **Acessar
plataforma**. Acessos fictícios: `admin@demo.invalid` e `tecnologia@demo.invalid`;
senha exclusiva dos exemplos: `Demonstracao-local-2026!`. Essas credenciais não
funcionam no runtime normal.

Não precisa criar `.env`, rodar `setup_local.py`, conectar à base institucional
ou aplicar migrações para usar o demo. Use somente dados sintéticos. `Ctrl+C`
encerra os dois servidores; iniciar novamente cria uma base limpa. Portas
ocupadas podem ser alteradas, por exemplo:

```powershell
npm.cmd run demo -- --frontend-port 3301 --backend-port 8301
```

Nesse caso, abra `http://localhost:3301`. O demo não aceita publicação ou
sincronização externa; não é ambiente de atendimento. Campos clínicos existentes
aparecem apenas para o exemplo designado e para o acesso fictício de Tecnologia.

Se aparecer **Porta 8300 ocupada** ou **Porta 3300 ocupada**, use o comando com
portas alternativas acima. Se o Next informar que outro demo já está usando
`.next-demo/dev/lock`, encerre o demo anterior com `Ctrl+C` no terminal dele antes
de iniciar outro. Não apague o lock de um processo em execução.

### Desenvolvimento com identidade institucional

**Gestão de integrações:** criação, rotação e revogação de tokens de leitura para a Agenda, com validade por prazo ou **Nunca expirar**, confirmação da senha institucional, cópia de endpoints/cURL e exportação agregada consistente. Em PostgreSQL, aplicar as migrações até `0006_nonexpiring_tokens` antes do deploy desta funcionalidade. Para SQLite local existente, há atualização administrativa própria. Veja [gestão de tokens e instalação](docs/GESTAO_TOKENS_E_ENDPOINTS_AGENDA.md). Esta alteração foi preparada para commit; seu push/deploy e a migração produtiva ficam com o operador.

Requisitos: Node.js 22+, Python 3.12, acesso de rede à base institucional para autenticação e as variáveis existentes de conexão fornecidas pela Tecnologia. Os comandos abaixo partem da raiz deste projeto e não exigem ativar scripts PowerShell.

Preparação inicial:

```powershell
npm.cmd ci
python -m venv backend/.venv
.\backend\.venv\Scripts\python.exe -m pip install -r backend/requirements-dev.txt
.\backend\.venv\Scripts\python.exe scripts/setup_local.py
```

`setup_local.py` acrescenta somente configurações locais ausentes em `.env.local`, preserva a conexão já configurada e gera segredos sem exibi-los. Se estiver montando um ambiente novo, use `.env.example` como referência e obtenha `DATABASE_URL` com a Tecnologia; não sobrescreva os arquivos de ambiente existentes. O runtime institucional não aceita os acessos fictícios do modo demo.

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

Validação de 30/10: **114 testes backend e 20 cenários de navegador aprovados**,
incluindo nove casos de privacidade Git. Lint, TypeScript, Ruff, `pip check` e build
aprovados. Esses testes cobrem o fluxo existente; ficha clínica, etiqueta, novos
papéis e impressão física continuam pendentes. Evidências na
[auditoria atual](docs/AUDITORIA_APLICACAO_E_PRINCIPIOS.md).

```powershell
npm.cmd run lint
npm.cmd run typecheck
npm.cmd run build
npm.cmd run test:backend
.\backend\.venv\Scripts\python.exe -m ruff check --config backend/pyproject.toml backend/app backend/tests scripts
npx.cmd playwright install chromium
npm.cmd run test:e2e
.\backend\.venv\Scripts\python.exe scripts/check_staged_privacy.py --tracked
```

Antes do commit, execute também `python scripts/check_staged_privacy.py` com o
Python do ambiente virtual. A checagem recusa fontes privadas/tabulares e segredos
locais conhecidos no staging; `--tracked` verifica caminhos de todo o índice,
inclusive no CI. Não substitui revisão de conteúdo nem remove histórico antigo.

Playwright inicia frontend compilado/backend próprios nas portas **3310/8310**; execute `npm.cmd run build` antes. Usa identidades sintéticas, documento sintético e SQLite temporário. Nenhum cadastro real é necessário e não há gravação institucional. Essas portas devem estar livres; use `ACTIONS_E2E_FRONTEND_PORT` e `ACTIONS_E2E_BACKEND_PORT` para escolher outras portas de teste. O Chromium é baixado apenas na preparação do ambiente. Capturas/relatórios ficam ignorados em `artifacts/` e `test-results/`.

Para executar o frontend compilado, mantenha o backend aberto e use `npm.cmd run build`, depois `npm.cmd start`. Isso permite testar o build local; não significa que o sistema está homologado para produção.

Para regenerar os contratos sem acessar dados:

```powershell
.\backend\.venv\Scripts\python.exe scripts/export_contracts.py
```

A API local oferece documentação em **http://127.0.0.1:8000/docs**. O diagnóstico real somente leitura pode ser repetido com `python scripts/inspect_database.py` no ambiente virtual; ele imprime apenas resultado e metadados, sem segredos ou linhas pessoais.

## Documentação

- [AC-Core: diagnóstico, dependências, aceite e rollback](docs/AC_CORE_PENDING_IMPLEMENTATIONS.md)
- [Novos metadados: tarefas nas consumidoras, contratos e implantação das APIs](docs/INTEGRACAO_NOVOS_METADADOS_E_CONSUMIDORES.md)
- [Descoberta da ficha e auditoria da Fase 0 — 30/10](docs/FASE_0_DESCOBERTA_2026-10-30.md)
- [Proposta de MVP, backlog, impressão e migração reversível](docs/PLANO_MVP_E_ACEITE_2026-10-30.md)
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
