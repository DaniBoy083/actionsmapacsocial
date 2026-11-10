# Handoff — AC Actions Map

**Status:** VERIFICADO — inspeção estática local; integração administrativa futura PROPOSTA, aguardando homologação.
**Repositório:** `../actionsmap`, HEAD `e46b59ca9f4b6f201095bf9aeed8a663fea779af`, inspecionado em 03/11/2026 somente por leitura. Owner e aprovador: PENDENTES DE VERIFICAÇÃO.
**Projeto Vercel:** `actionsmapacsocial`, URL retornada pela CLI https://actionsmapacsocial.vercel.app — existência/configuração VERIFICADAS em 03/11/2026; não comprova saúde HTTP nem integração ativa.
**Referência Core:** docs/03, docs/04, docs/05, docs/09, docs/generated/database-inventory.md e infrastructure-inventory.md. API v1 é contrato local; produção/Preview do Core permanecem bloqueados até persistência/revisão aprovadas.

## 1. Objetivo da atualização

**Nenhuma mudança necessária nas APIs de negócio, outbox, importação, esquema clínico ou autenticação externa por causa desta entrega do Core.** Nenhum arquivo do consumidor foi alterado. Há uma dependência administrativa real do cadastro legado, a preservar até migração aprovada. O login local futuro de profissionais/recepção está em STANDBY no projeto; não declarar contas externas/SSO como implementados nem ativá-los neste handoff.

## 2. Estado real atual e evidências

Projeto/URL Vercel foram observados em inspeção CLI read-only; código foi inspecionado sem executar scripts e sem abrir `.env`, bases SQLite, fichas ou registros pessoais:

- `AGENTS.md` e `README.md` mantêm novo login local externo e assinatura em STANDBY. A ficha clínica nova não foi implementada nem examinada nesta tarefa, pois nenhuma mudança clínica é proposta.
- `backend/app/infrastructure/identity.py`: consulta legado `public.profissionais_cadastrados`/`equipes_profissionais`; em produção usa `actions_map.authentication_identity(:value,:by_id)`, função documentada em `backend/alembic/versions/0002_authentication_lookup.sql`. Acesso institucional exige `administracao` e equipe Administração/Tecnologia. Não migrar essa função ou ler/exportar hashes para IA.
- `backend/app/security/session.py`: cookie próprio `ac_actions_session`, sessão de oito horas com hash do token, origem exata, CSRF, limitação de tentativas e revalidação do perfil por request; `technologist` protege área técnica. Não existe SSO Core ativo nestes arquivos.
- `backend/app/api/routes.py`: `/api/v1/auth/login`, `/auth/me`, `/auth/logout`, `/acoes`, `/acoes/{identifier}/publicar` e `/tecnologia/sincronizar-agenda`. `backend/app/api/integrations.py`: GET `/api/v1/integracoes/health`, GET `/api/v1/integracoes/acoes/resumos`, gerenciamento técnico `/api/v1/tecnologia/tokens` e revogação.
- `backend/app/infrastructure/outbox.py`: entrega HTTPS autorizada para `AGENDA_SUMMARIES_URL`, Bearer `AGENDA_SERVICE_TOKEN`, idempotência e ACK `event_id`/`schema_version=1.1`; retenta sem expor payloads. Exportação por páginas está em `api/integrations.py`; manter contratos existentes, inclusive versões posteriores que forem homologadas pelo produtor.
- `backend/alembic/versions/0001_actions_map.sql` declara tabelas próprias `actions_map.acoes_map_*`; revisões até `0006_nonexpiring_tokens.py` tratam tokens de integração. Não executar migrações nesta tarefa.
- `vercel.json`: frontend Next e backend FastAPI com binding `ACTIONS_BACKEND_URL`; `/api/v1/health` no backend e catch-all no frontend. `next.config.ts` não declara `basePath`. Não concluir compatibilidade de subpath sem testar BFF/URLs/assets.

ENV existentes relevantes, nomes apenas: `APP_ENV`, `FRONTEND_ORIGIN`, `ACTIONS_API_URL`, `ACTIONS_BACKEND_URL`, `DATABASE_URL`, `SESSION_SECRET`, `BENEFICIARIES_KEY`, `AGENDA_SUMMARIES_URL`, `AGENDA_SERVICE_TOKEN`. Owners, banco efetivamente conectado, revisão aplicada, controles remotos e saúde HTTP permanecem PENDENTES DE VERIFICAÇÃO.

## 3. Contratos do AC Core

Nenhum contrato Core é imposto às APIs de negócio. A dependência administrativa de `infrastructure/identity.py` deve ganhar proposta separada antes de aposentar o cadastro da Agenda. Candidatos locais: `GET /api/v1/internal/people/{id}` com `internal:people:read` e `GET /api/v1/internal/teams` com `internal:teams:read`, token de serviço vinculado ao app e grant explícito. Não retornam senha/hash; OIDC exige adaptador de login próprio e homologação. Preservar IDs e semântica de equipe/tipo. Não há migração automática de contas externas.

401/403 exigem negar acesso; 404 pode representar projeção não autorizada. 503 exige política de indisponibilidade/cache homologada, sem ampliar privilégios. Respostas administrativas usam no-store; não assumir cache offline ou revogação imediata em outros apps. Cache futuro terá TTL/invalidação explícitos e dados mínimos, aprovados por recurso. Logout local Core não revoga sessão global IdP nesta entrega.

## 4. Passo a passo técnico do outro agente

1. Rever o commit e os arquivos acima; confirmar owner, revisão produtiva e alterações locais posteriores sem executar setup, migração ou importação. O script `scripts/setup_local.py` altera ENV e não pertence a esta inspeção.
2. Mapear contratos API → Agenda, auth externa, regras de serviço e eventual dependência administrativa. Não habilitar SSO interno automaticamente nem migrar usuários externos. Sem dependência comprovada, encerrar com nenhuma mudança necessária e sem PR de código.
3. Preparar matriz app/papel/ação e mapa de IDs com evidências. Inspecionar em ambiente autorizado sem exportar dados reais ou hashes para IA.
4. Se não houver dependência administrativa, registrar **nenhuma mudança necessária**, sem PR/release. Se houver, parar na proposta, preencher caminhos reais/diff/contratos, revisar escopos e preparar flag desligada antes de qualquer implementação externa.
5. Se integração for necessária, ENV propostas no consumidor: `CORE_API_URL`, `OIDC_ISSUER`, `OIDC_CLIENT_ID`, `OIDC_CLIENT_SECRET`, `OIDC_AUDIENCE`; adaptar ao runtime e contrato real. ENV do Core usam prefixo `AC_`; não copiar valores para repo/logs.
6. Preparar testes, PR/Preview e plano de rollback. Autorizar produção somente após evidências e revisão do diff.

## 5. Proteções e não regressão

Preservar Actions Map API → Agenda → Plataforma Consolidada/Analytics → Portal e auth de serviços não migrados. Core não recebe prontuários/beneficiários nem proxy de APIs de negócio. Contas externas futuras não herdam identidade/permissão interna; seu fluxo continua em STANDBY. SSO autentica; backend de cada app autoriza recurso/equipe. Não alterar DNS, domínios, schema compartilhado, credenciais ou dados legados sem proposta/aprovação específica. Logs somente request ID, tipo de operação e códigos/contagens minimizados, sem PII/segredos/payloads.

## 6. Plano de testes positivos e negativos

API e autenticação de serviço com mesmos status/payloads/latência tolerada; falha Core sem interromper o fluxo vigente; ingestão Agenda preservada. Contas externas futuras exigirão seus próprios testes de isolamento quando forem implementadas, sem SSO interno automático. Para qualquer integração institucional: usuário sem app grant, papel insuficiente, MFA ausente, usuário inativo, token expirado/issuer/audience incorretos, CSRF e acesso cruzado devem falhar. Testar callbacks, assets, cookies, logout local/global e limites reais de revogação. Homologar dois pilotos SSO e fluxo de rollback, sem declarar testes de mocks como integração real.

Gates existentes: `npm.cmd run lint`, `npm.cmd run typecheck`, `npm.cmd run build`, `npm.cmd run test:backend`, `npm.cmd run test:e2e` e `python scripts/check_staged_privacy.py --tracked` com o Python do ambiente isolado. Os E2E usam fixtures/portas próprias conforme README. Nenhum teste, diagnóstico com conexão ou script de privacidade foi executado nesta inspeção; não repetir o relato histórico de testes como evidência atual.

## 7. Deploy e rollback

Sem diff confirmado não há deploy deste consumidor. Para mudança futura: owner, janela e aprovador ainda pendentes; PR/Preview isolado antes de produção. Em regressão, desligar flag/reverter release; pausar escrita e reconciliar alterações administrativas antes de restaurar escritor legado. Não apagar cadastros/IDs antigos. Reverter código não reverte dados; ensaiar backup/restore e conciliação em homologação antes de cutover.

## 8. O que não será alterado

Regras de domínio, registros clínicos/beneficiários, APIs Actions Map/Analytics, pipeline, domínios e DNS permanecem fora do diff do Core. Nenhum deploy, cutover, transferência de domínio ou migração do consumidor ocorreu neste trabalho.

## 9. Evidências pendentes e checklist final

- [x] Existência do projeto/URL Vercel registrada por CLI read-only.
- [x] Inspecionar repo/commit, auth, função legada, migrations e pipeline no código.
- [x] Registrar zero alterações nas APIs de negócio e no fluxo externo nesta entrega.
- [ ] Confirmar owners/estado remoto e aprovar transição da leitura administrativa legada.
- [ ] Definir flags, writer único, TTL/revogação e proteção de dados.
- [ ] Testar auth/RBAC, jornadas, não regressão e rollback/restore.
- [ ] Revisar diff e obter autorização específica de produção, se necessária.
