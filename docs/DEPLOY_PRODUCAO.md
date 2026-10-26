# Produção na Vercel — 26/10/2026

## Diagnóstico e correção

O domínio `https://actionsmapacsocial.vercel.app` respondia `404 NOT_FOUND`. O projeto estava com preset **Other**: o comando `next build` terminava, mas a Vercel distribuía a pasta pública sem montar as rotas Next.js. O código estava correto para execução local; o empacotamento da hospedagem estava incorreto.

Após a solicitação expressa para hospedar também o FastAPI na própria Vercel, `vercel.json` passou a declarar dois **Services** no mesmo projeto: frontend Next.js na raiz e backend FastAPI em `backend/`. Cada serviço é compilado separadamente. A comunicação usa binding privado `ACTIONS_BACKEND_URL`, injetado pela Vercel. Apenas `/api/v1/health` é exposto diretamente pelo backend; APIs privadas passam pelo BFF Next em `/api/backend/*`, com cookie, origem e CSRF.

O binding pode incluir um prefixo de caminho. `src/lib/backend.ts` preserva esse prefixo e bloqueia fallback para localhost dentro da Vercel. Localmente permanece `ACTIONS_API_URL=http://127.0.0.1:8000`.

Referências oficiais: [Vercel Services](https://vercel.com/docs/services), [FastAPI](https://vercel.com/docs/frameworks/backend/fastapi) e [runtime Python](https://vercel.com/docs/functions/runtimes/python). Services está em beta e já é o padrão usado no Portal Institucional do ecossistema.

## Persistência e migração

SQLite permanece exclusivo do desenvolvimento. A produção usa o PostgreSQL institucional existente, em schema isolado **`actions_map`**, com tradução de schema no SQLAlchemy. As credenciais institucionais continuam nas tabelas existentes `public.profissionais_cadastrados` e `public.equipes_profissionais`.

Migração Alembic `0001_actions_map`: oito tabelas vazias do módulo e controle de versão no mesmo schema. DDL congelado em `backend/alembic/versions/0001_actions_map.sql`, gerado/revisado offline e aplicado em transação com trava de migração, lock timeout e statement timeout. A estrutura das tabelas `public` e `portal` foi comparada antes/depois e preservada. Nenhum beneficiário, PDF ou registro operacional foi importado. A remoção automática pelo downgrade está bloqueada.

A credencial `ac_actions_map_runtime` tem uso do schema do módulo e permissões nas suas tabelas, somente leitura das colunas necessárias à autenticação institucional, nenhuma inserção de profissionais e nenhuma atualização/exclusão de auditoria. Foi verificada a conexão com essa própria credencial após o provisionamento. Conexões usam TLS e `NullPool`, adequado à conexão via pooler do Neon; `options` no startup foi removido por incompatibilidade comprovada com o pooler.

O startup não cria tabelas. Migrações são um comando administrativo separado. `scripts/provision_production.py` é um procedimento de provisionamento inicial explícito, com `--apply`; não deve ser usado para rotacionar credenciais nem recriar uma base em uso. Metadados anteriores e configuração de recuperação ficam em `artifacts/`, ignorado pelo Git e nunca enviado pelo deploy via Git. Isso não substitui backup/restauração integral homologados da base.

## Variáveis do backend

| Nome | Finalidade |
| --- | --- |
| `APP_ENV=production` | Exige persistência PostgreSQL/TLS |
| `ACTIONS_DATABASE_URL` | Credencial restrita do módulo, preferencial aos aliases do provedor |
| `SESSION_SECRET` | Sessões e CSRF, exclusivo deste módulo |
| `BENEFICIARIES_KEY` | Fernet autenticado para nomes; preservar em backup seguro |
| `FRONTEND_ORIGIN` | Origem HTTPS exata do domínio de produção |
| `AGENDA_WEB_URL` | Atalho institucional para a Agenda |
| `ACTIONS_BACKEND_URL` | Binding privado, gerado automaticamente pela Vercel |

Segredos foram provisionados como variáveis sensíveis sem impressão de valores. Não colocar essas chaves em `NEXT_PUBLIC_*`. As variáveis `POSTGRES_*` da integração Neon não bastavam para publicar a aplicação; o backend usa agora uma credencial própria.

O build do FastAPI executa `python -m app.check_deployment`, que valida produção, TLS, origem HTTPS, tamanho do segredo e formato da chave de cifragem. O gate não consulta registros nem imprime valores. Dependências de testes/PDF ficam em `requirements-dev.txt`, fora do runtime mínimo.

## Verificações e limitações

Validação local: 38 testes backend, 10 cenários de navegador em desktop/celular, lint, TypeScript e build. O Playwright usa `next start` do build compilado nas portas 3100/8100 para não interromper o `next dev` do usuário.

Verificação do deploy publicado: login e healthcheck HTTP 200, API sem sessão HTTP 401, credenciais deliberadamente inválidas HTTP 401 e navegação protegida redirecionando ao login. Nenhuma credencial real foi usada no teste de autenticação. O logotipo institucional de 4,8 KB é servido diretamente: sua URL estática responde 200, enquanto a otimização de imagens retornava 404 na configuração com Services.

O GitHub Actions não executou os jobs por bloqueio de faturamento da conta, conforme anotação do próprio GitHub. Essa pendência externa precisa ser regularizada no GitHub; não é falha do código nem foi resolvida alterando o workflow.

Importação histórica em produção, storage privado de uploads, integração receptora da Agenda, publicação no Portal, rotação operacional, testes de restauração e homologação institucional permanecem pendentes. A presença do frontend/API na Vercel não equivale ao aceite integral do MVP ou a certificação de privacidade.
