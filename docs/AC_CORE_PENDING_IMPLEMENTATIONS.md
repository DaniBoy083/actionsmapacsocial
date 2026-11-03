# AC-Core — diagnóstico e handoff do AC Actions Map

Data: **03/11/2026**. Aplicação: **AC Actions Map**. Branch analisada: `main`.
Referência: `e46b59ca9f4b6f201095bf9aeed8a663fea779af`.

**Estado: diagnóstico concluído; integração de runtime com o Core não implementada
nem homologada.** O handoff disponível determina preservar o funcionamento atual
e preparar a transição administrativa antes de implementá-la. As pendências abaixo
são requisitos de contrato e evidência para essa transição. Não demonstram, por si
só, defeitos ou ausência de funcionalidades no código do AC-Core, que não foi
inspecionado nesta tarefa.

## 1. Objetivo, escopo e Git

Preparar a integração institucional de identidade, autorização e gestão sem
transferir dados de beneficiários ao Core e sem alterar o fluxo
**Actions Map → Agenda Digital → Plataforma Consolidada de Análise de Dados →
Portal Institucional**. Contas locais operacionais e assinatura digital continuam
em standby. Não há substituição compatível de autenticação validada nesta entrega.

Antes de qualquer edição:

- `main`, `HEAD` e `origin/main` apontavam para a referência acima.
- `git fetch origin` foi executado com sucesso após a retomada. A tentativa
  anterior falhou por permissão e a primeira revisão automática de aprovação
  não pôde ser concluída por limite de uso; nenhuma atualização ocorreu nessas
  tentativas. O fetch posterior confirmou o alinhamento com o remoto.
- `git rev-list --left-right --count HEAD...main` e a comparação com
  `origin/main` retornaram `0 0`: nenhum commit exclusivo ou pendente.
- Não havia alteração em arquivo rastreado. `docs/actions-map.md` já existia
  como arquivo não rastreado; foi lido, preservado e excluído do commit da tarefa.
- Não foram necessários merge, rebase, descarte ou alteração de histórico.

Histórico relevante preservado:

| Commit | Conteúdo e implicação |
| --- | --- |
| `e46b59c` | Planejamento dos novos metadados e consumidoras; não comprova implementação do contrato futuro. |
| `c5fe90f` | Fase 0 e proteção de fontes privadas; manter gates de privacidade. |
| `b9bb43e` | Cadastro geral, segunda via e remoção do mapa; não reintroduzir o mapa ou modificar a ficha nesta integração. |
| `0c95124`, `e0eec0c` | Gestão de tokens da Agenda, inclusive sem expiração; preservar escopo, confirmação institucional e revogação. |
| `6e639c6`, `9ce2af1`, `985c2db` | Publicação/outbox, consulta delegada com RLS e adaptador produtivo; preservar esses contratos durante a transição. |

## 2. Fontes disponíveis e limites da evidência

Leitura integral do handoff Core disponível: **`docs/actions-map.md`**, nove
seções, inspeção estática declarada de 03/11/2026. Ele afirma que a integração
administrativa é proposta, que não houve mudança necessária nas APIs de negócio
por essa entrega e que os endpoints administrativos são candidatos locais.
As verificações remotas relatadas por esse arquivo são evidência de seu autor;
não foram repetidas aqui.
SHA-256 do handoff local preservado:
`d4f51427b1fe4ccb8a1c6132c568adec69b1b88e7ec7d81a08843a0319487a68`.

Também foram lidos `AGENTS.md`, `README.md`, `docs/ARQUITETURA.md`,
`docs/CORRECAO_LOGIN_RLS.md`, `docs/GESTAO_TOKENS_E_ENDPOINTS_AGENDA.md`,
`docs/PUBLICACAO_E_FLUXO_DE_ACOES.md`, `docs/branding-guidelines.md` e as seções
vinculantes/transversais do plano v2.1 `docs/PLANO_ACTIONS_MAP_GPT61_SOL.md`.
Contratos existentes do Map: `backend/app/domain/contracts.py`,
`backend/app/domain/integrations.py` e `docs/contracts/`.

Busca por arquivos e referências, incluindo ignorados pelo Git, na raiz,
`docs/`, `docs/contracts/`, `docs/references/`, `docs/data/` e documentos dos
artefatos locais: a única fonte encontrada sobre AC-Core foi
`docs/actions-map.md`. Os documentos **01–12**, os documentos 03/04/05/09 e os
inventários `docs/generated/database-inventory.md` e
`infrastructure-inventory.md` citados nele não foram encontrados no repositório.
`docs/agenda-digital.md`, mostrado como aba no IDE, também não foi encontrado
no disco durante a análise. Três diretórios temporários de clusters PostgreSQL
em `tmp/integration-pg-*` recusaram enumeração; não se afirma ter lido seu conteúdo.
Nenhuma pesquisa foi feita em repositórios vizinhos.

Não foram abertos arquivos de ambiente privados, bases, backups, fichas
preenchidas ou cadastros reais para o diagnóstico. O gate de privacidade existente
lê configurações localmente para comparar segredos com o diff, sem exibi-los.
A ficha XLSX em `docs/references/` foi apenas localizada: esta tarefa não modela
campos, banco, triagem, ficha, PDF ou etiqueta e não declara uma nova leitura da
ficha original. A evidência clínica histórica permanece no documento da Fase 0.

## 3. Diagnóstico da implementação atual

| Área | Evidência no repositório | Estado constatado |
| --- | --- | --- |
| Stack | `package.json`, `backend/requirements*.txt` | Next.js 16.4.3, React 19.3, TypeScript estrito, MUI, FastAPI, SQLAlchemy, Pydantic e Alembic. Sem SDK Core/OIDC configurado. |
| Camadas | `backend/app/{domain,application,infrastructure,security,api}` | Domínio/casos de uso separados de SQL, identidade, cifragem, importação e HTTP. Parte dos fluxos legados ainda é composta nas rotas. |
| Identidade | `backend/app/infrastructure/identity.py` | Cadastro institucional legado; SQL somente leitura, com parâmetros vinculados. Produção usa `actions_map.authentication_identity(:value, :by_id)`; senha scrypt verificada no backend. Nenhum hash deve migrar para uma API Core. |
| Autorização | `backend/app/domain/contracts.py`, `security/session.py` | `Professional.allowed`: tipo `administracao` e equipe Administração/Tecnologia. `technologist` exige Tecnologia. Não existe grant Core por aplicativo nem mapeamento OIDC. |
| Sessão | `security/session.py`, `api/routes.py` | Cookie `ac_actions_session`, HttpOnly, SameSite Strict, Secure em produção; token aleatório, somente hash persistido, oito horas. Reconsulta institucional por request, origem exata, CSRF, rate limit e logout local. |
| Operações técnicas | `backend/app/api/integrations.py` | Criar, rotacionar e revogar tokens exige sessão, Tecnologia, origem, CSRF e nova verificação da senha institucional. Depende do legado além do login. |
| Dados | `infrastructure/database.py`, `models.py`, `backend/alembic/versions/` | SQLite local; produção PostgreSQL/TLS no schema `actions_map`, sem DDL no startup. Identidade e armazenamento produtivo usam a configuração de conexão institucional; não há prova de bancos lógicos independentes. Migrações existentes até 0006, sem executar nenhuma. |
| Frontend/BFF | `src/app/(app)/layout.tsx`, `src/app/api/backend/[...path]/route.ts` | Sessão consultada no servidor, proxy com allowlist e limites, no-store e origem. Não há callback Core nem aceitação de Bearer para substituir sessão de usuário no BFF. |
| Serviços | `api/integrations.py`, `infrastructure/integrations.py`, `src/lib/integration-proxy.ts` | Tokens próprios de leitura de resumos agregados, hash, escopo, validade/revogação, quotas e exportação consistente. Não equivalem a login institucional. |
| Outbox | `infrastructure/outbox.py`, DTO `Summary` | Contrato 1.1 com Agenda, HTTPS, Bearer servidor, chave idempotente, ACK validado, backoff e até dez tentativas. Core não é intermediário desse fluxo. |
| Infraestrutura | `vercel.json`, `next.config.ts`, `src/lib/backend.ts` | Next/FastAPI com binding privado `ACTIONS_BACKEND_URL`; `ACTIONS_API_URL` local. Não há `basePath` nem integração Gateway. URL/saúde/DNS produtivos não verificados nesta tarefa. |
| Segredos | `backend/app/config.py`, `.env.example` | Configuração privada de runtime; não há adaptador AC Vault. Não foram criadas credenciais ou novas variáveis para serviços hipotéticos. |
| Auditoria | `models.py`, `security/session.py`, `api/integrations.py`, `main.py` | Eventos locais de ator/operação/recurso e erros sanitizados. Não há exportador Core de auditoria nem promessa de revogação global. |
| Qualidade | `backend/tests/`, `tests/e2e/`, `.github/workflows/ci.yml` | Testes existentes isolam identidades/dados; contratos, segurança, idempotência e jornadas do sistema atual. Não são testes de integração real com Core. |

Configurações vigentes, **nomes somente**: `APP_ENV`, `FRONTEND_ORIGIN`,
`ACTIONS_API_URL`, `ACTIONS_BACKEND_URL`, `ACTIONS_DATABASE_URL` e aliases
institucionais de banco, `ACTIONS_STORAGE_URL`, `SESSION_SECRET`,
`BENEFICIARIES_KEY`, `AGENDA_WEB_URL`, `AGENDA_SUMMARIES_URL`,
`AGENDA_SERVICE_TOKEN`. `CORE_API_URL` e `OIDC_*` citados no handoff de origem são
propostas, não configurações reconhecidas pelo runtime atual.

## 4. Entrega e distribuição de responsabilidades

Esta entrega é documental: cria este handoff e atualiza `README.md` e
`docs/ARQUITETURA.md`. Não modifica código, dependências, OpenAPI, schemas,
ambiente, dados, credenciais, autenticação ou infraestrutura. Os componentes
Core efetivamente integrados nesta entrega são **nenhum**.

Actions Map continua responsável por ações, locais, beneficiários privados,
permissão de recurso no backend, documentos existentes, outbox e contratos com
Agenda. Core poderá prover identidade institucional, grants e cadastros
compartilhados após contrato e migração aprovados. Dados clínicos, beneficiários
e autenticação local futura não são transferidos por essa transição.

## 5. Pendências para o agente do AC-Core

**Classificação de evidência:** confirmado significa verificável no consumidor
ou na documentação fornecida; pendente de validação significa que o Core pode
já oferecer o recurso, mas sua disponibilidade/compatibilidade não foi provada.
Bloqueante refere-se à **migração para Core**, não ao funcionamento vigente.

### CORE-01 — Publicar pacote de contratos e disponibilidade

1. **Componente:** arquitetura/API e operação do AC-Core.
2. **Prioridade:** bloqueante.
3. **Evidência:** confirmado que o consumidor recebeu apenas o handoff; implementação e disponibilidade do Core pendentes de validação.
4. **Problema técnico:** referências 01–12/inventários não estão presentes; não há OpenAPI Core, schemas administrativos nem configuração OIDC verificável.
5. **Justificativa:** exemplos de caminhos não permitem implementar um cliente compatível e seguro.
6. **Comportamento esperado:** pacote versionado distingue contrato proposto, implementado, implantado e homologado por ambiente.
7. **Contratos envolvidos:** API v1 e documentos 03/04/05/09 citados pelo handoff; caminhos exatos a confirmar no Core.
8. **Alterações necessárias:** disponibilizar documentos, especificações, versão/commit, exemplos sintéticos, códigos de erro e matriz de disponibilidade sem segredos.
9. **Dependências:** owners e ambiente de homologação autorizados.
10. **Impacto no Map:** impede qualquer ativação do novo provedor; não justifica alterar o legado.
11. **Aceite:** arquivos acessíveis ao consumidor, contratos validáveis e evidência de chamadas em homologação com identidades sintéticas.
12. **Recomendação:** exportar contratos do código do Core e registrar divergências antes de atualizar clientes.
13. **Testes:** validação de schema/compatibilidade, erros e disponibilidade real por ambiente.
14. **Ação no Map após aceite:** selecionar contratos aplicáveis e preparar diff pequeno com flag inicialmente desligada.

### CORE-02 — Autenticação institucional e vínculo estável de identidade

1. **Componente:** AC Auth/IdP e cadastro de aplicações.
2. **Prioridade:** bloqueante.
3. **Evidência:** confirmado login por senha/digest e IDs legados no Map; suporte Core a SSO pendente de validação.
4. **Problema técnico:** não há issuer, discovery, cliente registrado, audiência, callbacks ou regra `sub` → `profissional_id` fornecidos ao consumidor.
5. **Justificativa:** IDs de ator vinculam sessões, auditoria e ownership de importações; autenticação válida não concede permissão automaticamente.
6. **Comportamento esperado:** autenticação institucional central sem expor senha/hash ao Map, com sujeito estável e vínculo explícito aos IDs existentes.
7. **Contratos envolvidos:** contrato OIDC real do IdP; o handoff apenas propõe `OIDC_ISSUER`, `OIDC_CLIENT_ID`, `OIDC_CLIENT_SECRET` e `OIDC_AUDIENCE`.
8. **Alterações necessárias:** fornecer perfil de autenticação, registro do cliente, URLs autorizadas, validação de tokens e procedimento de vínculo/migração.
9. **Dependências:** CORE-01, CORE-03 e ambiente de homologação.
10. **Impacto no Map:** afeta `identity.py`, `session.py`, `/auth/*`, layout e tela de login; não migrar profissionais/recepção locais.
11. **Aceite:** sujeito vinculado sem colisões; issuer/audiência/assinatura/prazo validados; estado e proteção do callback verificados; zero digest transmitido.
12. **Recomendação:** definir fluxo de autorização compatível com backend confidencial, proteção contra replay e PKCE conforme o contrato homologado; não usar API de pessoas como verificador de senha.
13. **Testes:** token adulterado/expirado, issuer/audiência errados, callback não autorizado, replay, identidade não vinculada e colisão de e-mail.
14. **Ação no Map após aceite:** implementar adaptador e vinculação auditada preservando IDs; desligar o login legado somente no cutover validado.

### CORE-03 — Grants, equipes e projeção administrativa mínima

1. **Componente:** AC Management e autorização do AC Auth.
2. **Prioridade:** bloqueante.
3. **Evidência:** confirmado que o Map autoriza por tipo/equipe legados; campos, grants e disponibilidade das APIs Core pendentes de validação.
4. **Problema técnico:** não há semântica aprovada entre identidade Core, ativo/inativo, tipo administrativo, Administração/Tecnologia e acesso ao aplicativo.
5. **Justificativa:** aceitar qualquer usuário autenticado ou inferir papel por e-mail ampliaria privilégios.
6. **Comportamento esperado:** grant explícito para o app e projeção mínima permitem ao Map manter Administração/Tecnologia, com rotas técnicas exclusivas de Tecnologia.
7. **Contratos envolvidos:** candidatos do handoff `GET /api/v1/internal/people/{id}` (`internal:people:read`) e `GET /api/v1/internal/teams` (`internal:teams:read`), ainda não homologados no consumidor.
8. **Alterações necessárias:** publicar schemas, IDs, paginação se aplicável, status de inatividade, política de projeção/404 e token de serviço restrito ao app; excluir senha/hash.
9. **Dependências:** CORE-01/02 e matriz app/papel/recurso aprovada institucionalmente.
10. **Impacto no Map:** substituição futura da leitura delegada; não criar cópia mestre de usuários/equipes nem alterar tabelas da Agenda nesta entrega.
11. **Aceite:** sem grant, inativo ou papel inadequado recebe negação; Administração não obtém operações técnicas; IDs históricos conservados.
12. **Recomendação:** negar por padrão; manter autorização de recurso no backend consumidor e documentar semântica de 401/403/404/503 antes do cliente.
13. **Testes:** app grant ausente, escopo insuficiente, equipe removida, usuário inativo, projeção não autorizada e token de outro app.
14. **Ação no Map após aceite:** traduzir contrato para papéis atuais por mapeamento explícito, sem habilitar os papéis clínicos futuros.

### CORE-04 — Reautenticação para gestão dos tokens da Agenda

1. **Componente:** AC Auth/IdP, em conjunto com o consumidor.
2. **Prioridade:** alta; bloqueia retirar o legado dessa jornada.
3. **Evidência:** confirmado em `api/integrations.py::reauthorize`; mecanismo equivalente do Core pendente de validação.
4. **Problema técnico:** criar, rotacionar e revogar tokens exige confirmação da senha institucional, mesmo depois do login.
5. **Justificativa:** substituir somente `IdentityRepository` deixaria essas operações quebradas ou removeria um controle existente.
6. **Comportamento esperado:** confirmação recente e verificável pelo provedor central, vinculada ao usuário e à operação, sem enviar senha/hash por API administrativa.
7. **Contratos envolvidos:** step-up/reautenticação do IdP a confirmar; sem endpoint proposto neste documento.
8. **Alterações necessárias:** especificar evidência de reautenticação, validade, MFA quando exigido, proteção contra replay, retorno/erros e vínculo com a sessão.
9. **Dependências:** CORE-02/03; política institucional de operações privilegiadas.
10. **Impacto no Map:** `CredentialAuthorization`, API, BFF e `credential-manager.tsx` precisarão de mudança coordenada.
11. **Aceite:** sessão comum sozinha não substitui a confirmação; evidência antiga, ausente, reutilizada ou de outro usuário é recusada; Administração permanece bloqueada.
12. **Recomendação:** verificar `auth_time`, `acr` e `amr` somente se definidos e garantidos pelo contrato real; não confiar em flags do navegador.
13. **Testes:** cancelar/expirar a confirmação, replay, troca de sessão, privilégio insuficiente e preservação da rotação atômica/revogação.
14. **Ação no Map após aceite:** substituir a jornada completa; conservar quotas, CSRF, exibição única, hash e auditoria dos tokens próprios.

### CORE-05 — Sessões, revogação e indisponibilidade

1. **Componente:** AC Auth/Management e operação do Core.
2. **Prioridade:** alta.
3. **Evidência:** confirmado logout local e reconsulta legada por request no Map; propagação/revogação Core pendente de validação.
4. **Problema técnico:** o handoff não garante logout global, revogação imediata ou cache offline e exige política homologada para 503.
5. **Justificativa:** remover equipe/grant deve ter prazo conhecido para cessar acesso; falha do Core não pode ampliar autorização.
6. **Comportamento esperado:** contrato separa expiração, logout local, sessão IdP, revogação de grants e falha de serviço, com latências e cache explícitos.
7. **Contratos envolvidos:** sessão/token do IdP, projeções administrativas e semântica de 401/403/404/503; URLs específicas a confirmar.
8. **Alterações necessárias:** definir invalidação/TTL, possibilidade de introspecção/eventos se disponível, timeout, limites, retentativa e regras de logout.
9. **Dependências:** CORE-01/02/03; decisão de segurança para cache e contingência.
10. **Impacto no Map:** revalidação por request e tratamento de indisponibilidade; nenhum fallback automático que restaure privilégios do legado.
11. **Aceite:** desativação/grant removido bloqueia no prazo documentado; timeout/503 não autoriza acesso; logout tem efeito exato demonstrado.
12. **Recomendação:** documentar limites reais de revogação; não anunciar logout global se apenas a sessão local for encerrada.
13. **Testes:** expiração, revogação durante sessão, perda de equipe, timeout, 503, cache vencido e logout nos ambientes autorizados.
14. **Ação no Map após aceite:** implementar a política com testes negativos e rollback, mantendo o fluxo Agenda independente do Core.

### CORE-06 — Gateway, domínio e roteamento homologados

1. **Componente:** AC Gateway e infraestrutura do Core.
2. **Prioridade:** média; pode bloquear rollout se exigir mudança de origem/caminho.
3. **Evidência:** confirmado runtime Vercel/binding e ausência de `basePath`; destino institucional do app pendente de validação.
4. **Problema técnico:** não há rota aprovada em `acsocial.org`, regras de headers/proxy ou definição entre subdomínio e subpath nesta cópia.
5. **Justificativa:** origem, cookies, CSRF, callback e assets dependem dessas decisões.
6. **Comportamento esperado:** destino e fronteiras de confiança documentados, preservando autonomia do Map e seu pipeline com Agenda.
7. **Contratos envolvidos:** política de rotas/domínio do Gateway a fornecer; não inventar hosts ou prefixos.
8. **Alterações necessárias:** especificar origem canônica, TLS, encaminhamento, paths/redirects, cookies e contingência/recuperação independente da Vercel.
9. **Dependências:** owner de infraestrutura, registro do cliente Core e homologação isolada.
10. **Impacto no Map:** configuração privada, BFF, links, assets e callbacks futuros; não comprova suporte a subpath hoje.
11. **Aceite:** login/logout, deep links, assets e APIs funcionam na origem aprovada; origem/host indevidos não burlam controles; sem mudança DNS nesta tarefa.
12. **Recomendação:** ensaiar roteamento em Preview/homologação e produzir plano revisável antes de mudar infraestrutura.
13. **Testes:** caminhos diretos, redirects, headers de proxy, cookies/CSRF, assets e indisponibilidade do Gateway.
14. **Ação no Map após aceite:** adaptar somente o necessário ao destino efetivo e solicitar autorização específica de produção.

### CORE-07 — Vault e procedimento de entrega de segredos

1. **Componente:** AC Vault e operação/segurança do Core.
2. **Prioridade:** média; alta se a política exigir Vault antes do cutover.
3. **Evidência:** confirmado uso de configuração privada no Map; contrato Vault e disponibilidade pendentes de validação.
4. **Problema técnico:** não foi fornecido protocolo de bootstrap, leitura/entrega de segredo, escopos por aplicação/ambiente, rotação ou contingência.
5. **Justificativa:** criar um cliente hipotético ou mover segredos de produção impediria verificar menor privilégio e recuperação.
6. **Comportamento esperado:** fluxo autorizado e auditável fornece apenas segredos necessários ao backend de cada ambiente, sem exposição em browser/Git/logs.
7. **Contratos envolvidos:** contrato real do Vault a fornecer; decidir se entrega ocorre no deploy ou em runtime antes de criar adaptador.
8. **Alterações necessárias:** publicar contrato/runbook com identidades de serviço, escopos, bootstrap, versionamento, falha, rotação e rollback; valores por canal privado.
9. **Dependências:** CORE-01, infraestrutura e autorização específica para qualquer migração produtiva de credenciais.
10. **Impacto no Map:** banco, sessão, cifragem e token Agenda têm ciclos distintos; perder `BENEFICIARIES_KEY` impede ler dados existentes.
11. **Aceite:** ambiente/app indevidos são negados; nenhum segredo aparece em respostas/logs/Git; recuperação da versão válida demonstrada sem corromper dados.
12. **Recomendação:** preservar configuração vigente até substituição validada; se houver scripts sensíveis temporários, executá-los só no procedimento autorizado e removê-los após uso.
13. **Testes:** privilégio mínimo, ambiente errado, expiração/revogação de acesso, Vault indisponível e rotação/recuperação com segredos sintéticos.
14. **Ação no Map após aceite:** preparar adaptação conforme o contrato efetivo; não rotacionar chave de cifragem, sessão ou serviço implicitamente.

## 6. Incompatibilidades e decisões

| Evidência | Divergência/limite | Decisão desta entrega |
| --- | --- | --- |
| Pedido de integração × handoff Core disponível | Handoff condiciona transição a proposta e homologação; exemplos não são contratos disponibilizados. | Concluir diagnóstico/documentação; não fabricar endpoints ou ativar SSO. |
| APIs administrativas de pessoas/equipes × verificação de senha | Projeções não substituem login nem confirmação técnica por senha. | Migrar login, autorização e step-up como jornadas coordenadas quando os contratos existirem. |
| Centralização futura × leitura institucional vigente | Remover a dependência antes da substituição validada impediria acesso/revalidação. | Preservar dependência explicitamente documentada até cutover aprovado; sem novo mecanismo paralelo. |
| Revalidação atual × revogação Core | Remoção de perfil no legado é reconsultada; não prova grants/revogação no IdP. | Especificar limites antes de mudar o provedor; negar falhas sem ampliar acesso. |
| Domínio institucional × configuração atual | Configuração local descreve Vercel e caminhos absolutos; não comprova suporte a subpath. | Nenhuma alteração DNS/domínio; homologar o roteamento efetivo. |
| Metadados futuros × exportação existente | Nome/número/autor e novos parceiros estão planejados; emissor atual permanece 1.1. | Preservar contrato e separar essa evolução da integração institucional. |

## 7. Validação desta entrega

Execuções desta tarefa, em 03/11/2026, sobre o código de referência preservado:

| Comando | Resultado |
| --- | --- |
| `npm.cmd run lint` | Aprovado, exit 0. |
| `npm.cmd run typecheck` | Geração de tipos e TypeScript aprovados, exit 0. |
| `npm.cmd run build` | Build otimizado e geração das 13 páginas concluídos, exit 0; sem deploy. |
| `backend/.venv/Scripts/python.exe -m pytest backend/tests -q` | **114 aprovados**, exit 0; um aviso de depreciação Starlette/httpx. |
| `backend/.venv/Scripts/python.exe -m ruff check --config backend/pyproject.toml backend/app backend/tests scripts` | Aprovado, exit 0. |
| `backend/.venv/Scripts/python.exe -m pip check` | Nenhuma dependência incompatível, exit 0. |
| `npm.cmd run test:e2e` | **20 aprovados**, desktop e mobile, exit 0; 5,2 minutos incluindo encerramento dos servidores. |
| `backend/.venv/Scripts/python.exe scripts/check_staged_privacy.py --tracked` | `PRIVACY_OK`, exit 0. |
| `backend/.venv/Scripts/python.exe scripts/check_staged_privacy.py` | Staging dos três documentos: `PRIVACY_OK`, exit 0. |
| `git diff --check` e `git diff --cached --check` | Aprovados; diff revisado, somente os três documentos da tarefa no staging. |

O Playwright concluiu os 20 cenários, mas aguardou o encerramento dos servidores
Windows. Foram encerrados explicitamente apenas os dois servidores de teste
iniciados por esta execução (Next/Uvicorn); depois o runner finalizou com exit 0
e relatório `artifacts/e2e-results.json`. Não foi alterado o harness ou o código
da aplicação. Avisos adicionais de `NO_COLOR`/`FORCE_COLOR` não falharam os testes.
O aviso Starlette/httpx foi preservado; atualizar dependências está fora desta
entrega documental. As contagens acima não são testes com o AC-Core.

Os testes existentes verificam login/perfis, acesso técnico negado à Administração,
origem/CSRF, sessão/logout/expiração, revalidação de equipe, tokens de serviço,
revogação, contratos sem PII, idempotência/ACK e jornadas de cadastro/importação/
segunda via com fixtures sintéticas. Não homologam o MVP clínico, impressão física
ou serviços Core indisponíveis nesta análise.

Não foram executados diagnóstico remoto de banco, migrações, importações reais,
rotação de credenciais, alterações no Core, deploy, PR ou push. A disponibilidade
real de Auth/Management/Gateway/Vault e a integração com a Agenda produtiva não
foram testadas. Isso permanece gate para uma futura ativação.

## 8. Sequência para continuidade, liberação e rollback

1. No Core, conferir código/versão e ambiente dos contratos de CORE-01; fechar
   cada item como implementado/comprovado ou defeito real, com evidências sintéticas.
2. Obter owners/aprovadores de Core/Map e aprovar matriz de permissões, vínculo de
   IDs, writer único de cadastros compartilhados e política de sessão/contingência.
3. No Map, preparar adaptadores conforme contratos reais, com flag desligada,
   mantendo dados e integrações de negócio sob sua responsabilidade. Não alterar
   o AC-Core ou outras aplicações a partir deste repositório.
4. Homologar login, callbacks, grants, step-up técnico, revogação, cache/erros e
   jornadas em dois pilotos SSO conforme o handoff de origem. Registrar diferenças
   entre testes de mocks, contrato e integração real.
5. Revalidar pipeline/ACK sem PII e ausência de dependência Core nas APIs de
   negócio. Preservar tokens/outbox existentes durante toda a transição.
6. Ensaiar backup/restore e rollback em ambiente isolado; depois apresentar diff,
   configuração e plano para autorização específica de cutover/produção.

Rollback desta entrega documental: reverter apenas o commit da tarefa por novo
commit, preservando `docs/actions-map.md` e qualquer trabalho posterior; não há
dados, migração ou ambiente a restaurar. Rollback futuro de integração exige
desligar a flag/reverter release conforme plano homologado. Restaurar o legado
não pode ignorar desativações/grants revogados no Core; pausar escrita e reconciliar
cadastros antes de reativar escritor anterior. Reverter código não restaura dados.

## 9. Estado final

- **Concluído:** Git atualizado e auditado; leitura do handoff disponível;
  diagnóstico do consumidor; documentação de dependências e plano de validação.
- **Preservado:** login institucional atual, permissões no backend, gestão de
  tokens, cadastro geral, segunda via, importação e pipeline agregado 1.1.
- **Parcial:** preparação da migração institucional, ainda documental.
- **Bloqueado para implementação/ativação:** cliente Core sem contratos reais
  disponibilizados/homologados, vínculo de IDs, grants, reautenticação e política
  de sessões. Gateway/Vault dependem de contrato e decisão de operação.
- **Sem afirmação de defeitos Core confirmados:** não foi disponibilizado código
  ou serviço Core para a verificação nesta tarefa. As lacunas confirmadas são de
  evidência/contrato no consumidor; a lista deve ser reclassificada pelo agente Core.

O hash do commit local de entrega e o estado final do diretório são informados no
relatório ao responsável. Nenhum push é parte deste procedimento.
