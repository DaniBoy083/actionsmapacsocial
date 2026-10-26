# Arquitetura da primeira entrega

**Atualização de produção em 26/10/2026:** a hospedagem conjunta Next.js/FastAPI, o binding privado e a persistência PostgreSQL do módulo foram preparados conforme [deploy de produção](DEPLOY_PRODUCAO.md). As referências abaixo ao SQLite e à ausência de migração descrevem a entrega inicial local; a produção usa agora `actions_map`, Alembic e credencial restrita, sem criação de tabelas no startup.

Next.js 16.4.3 / React 19.3 / TypeScript estrito / Tailwind 4. MUI 9 e Emotion com `AppRouterCacheProvider` da versão 16 e camadas CSS; React Icons, React Hot Toast, React Hook Form/Zod, Axios e TanStack Query. Sem React Router, credenciais no bundle ou fontes externas obrigatórias.

Frontend → BFF Next (`/api/backend/*`, allowlist de caminhos, origem, limite de corpo, timeout, respostas privadas) → FastAPI `/api/v1`. Cookies HttpOnly/SameSite Strict; CSRF derivado da sessão nas mutações. Em produção, Secure/HTTPS obrigatórios. Layout autenticado consulta a sessão atual sem cache compartilhado; todas as APIs revalidam a identidade institucional.

Camadas Python:

- `domain`: DTOs estritos, regras de transição, catálogo IBGE e portas de persistência.
- `application`: casos de uso de ações dependentes da porta `ActionRepository`.
- `infrastructure`: adaptadores SQLAlchemy, cifragem, leitura institucional, PDF e worker de outbox.
- `security`: sessão opaca (somente hash persistido), CSRF, rate limit persistente e autorização.
- `api`: composição, dependências e endpoints versionados. Fluxos de beneficiários/importação ainda são compostos nas rotas; a extração desses casos de uso para portas próprias integra o próximo incremento.

O SQLite em `backend/private/` serve exclusivamente ao desenvolvimento/testes. Não é fallback de falha do PostgreSQL. Em produção, PostgreSQL/TLS persiste as tabelas próprias no schema `actions_map`; a autenticação usa a consulta institucional delegada. Migrações Alembic e grants são operações administrativas separadas, sem criação de tabelas no startup. Nenhuma migração modifica as tabelas de profissionais ou Portal. Não há prontuário, `usuario_id` clínico ou criação de senha.

As mutações de ação gravam alteração, auditoria e snapshot de outbox na mesma transação. Edição/revisão/arquivamento exigem versão atual; edição invalida aprovação. Ações arquivadas saem das métricas ativas sem apagar beneficiários. Publicação é bloqueada com 503 enquanto o receptor e a governança não estiverem homologados.

Beneficiário mínimo: UUID próprio, nome cifrado com Fernet autenticado e vinculado ao ID no conteúdo, município de residência opcional. Participação aponta à ação e, quando informado, ao índice de um local. Enquanto houver participações localizadas, alteração da lista de locais é bloqueada para não remapear vínculos por acidente; substituição por entidades relacionais está prevista na migração PostgreSQL.

Importação por arquivos: `/importacoes` recebe PDF/CSV/JSON, transmite partes binárias pela BFF e armazena temporariamente o conteúdo cifrado no schema próprio. Migração `0003_private_file_import`, ownership por profissional, quotas, expiração, parser isolado e confirmação produtiva explícita. Revisão nominal com RHF/Zod; nenhum OCR externo. Confirmação transacional/idempotente por hash do documento/página ou registro/ação; mesma página em outro destino exige decisão do operador. Não há deduplicação automática entre fontes diferentes. [Detalhes e operação](IMPORTACAO_ARQUIVOS.md).

A Visão geral é a única página de métricas. A API privada `/api/v1/indicadores` continua fornecendo os totais; a antiga página homônima foi removida. `/dados-iniciais` redireciona para `/importacoes`. A carga assistida do acervo local fica em adaptador operacional de infraestrutura, sem dependência de SQLAlchemy nas entidades ou casos de uso de aplicação.

Worker: envio HTTPS com token servidor, DTO allowlist, chave idempotente, ACK do evento/versão, dez tentativas e backoff. Não roda automaticamente nem tem destinatário configurado por padrão. Uma instância por armazenamento local; leasing/locking distribuído são requisitos da versão institucional.

Horários de banco em UTC e apresentação em `America/Fortaleza`, conforme planejamento. Datas sem hora não são deslocadas pelo fuso. Formulários e respostas usam português brasileiro.

Referências técnicas verificadas: [MUI e App Router](https://mui.com/material-ui/integrations/nextjs/), [FastAPI e segurança](https://fastapi.tiangolo.com/tutorial/security/), [IBGE Localidades](https://servicodados.ibge.gov.br/api/docs/localidades). Os guias locais do pacote Next prevalecem para esta versão.
