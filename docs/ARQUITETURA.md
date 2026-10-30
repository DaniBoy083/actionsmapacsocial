# Arquitetura da primeira entrega

> **Estado em 30/10/2026:** este texto descreve a implementação geral existente.
> O MVP ocular do plano v2.1 é a evolução vigente e ainda não está implementado.
> [Inventário real, fontes e fronteiras](FASE_0_DESCOBERTA_2026-10-30.md);
> [modelo futuro e gates](PLANO_MVP_E_ACEITE_2026-10-30.md). Novo login local
> avançado e assinatura eletrônica permanecem em standby. Schema isolado atual
> não comprova a independência lógica do banco operacional exigida para a evolução.

**Revisão de 28/10/2026:** página, API e dependências do mapa consolidado removidas por decisão do responsável. Cadastro geral ampliado, edição versionada e segunda via seguem `BeneficiaryData/BeneficiaryRepository` → `BeneficiaryService` → adaptador SQL/cifragem/auditoria → API/BFF → componentes MUI com RHF/Zod compartilhados. [Campos, operação e limites](CADASTRO_BENEFICIARIOS_E_SEGUNDA_VIA.md).

**Atualização de produção em 26/10/2026:** a hospedagem conjunta Next.js/FastAPI, o binding privado e a persistência PostgreSQL do módulo foram preparados conforme [deploy de produção](DEPLOY_PRODUCAO.md). As referências abaixo ao SQLite e à ausência de migração descrevem a entrega inicial local; a produção usa agora `actions_map`, Alembic e credencial restrita, sem criação de tabelas no startup.

Next.js 16.4.3 / React 19.3 / TypeScript estrito / Tailwind 4. MUI 9 e Emotion com `AppRouterCacheProvider` da versão 16 e camadas CSS; React Icons, React Hot Toast, React Hook Form/Zod, Axios e TanStack Query. Sem React Router, credenciais no bundle ou fontes externas obrigatórias.

Frontend → BFF Next (`/api/backend/*`, allowlist de caminhos, origem, limite de corpo, timeout, respostas privadas) → FastAPI `/api/v1`. Cookies HttpOnly/SameSite Strict; CSRF derivado da sessão nas mutações. Em produção, Secure/HTTPS obrigatórios. Layout autenticado consulta a sessão atual sem cache compartilhado; todas as APIs revalidam a identidade institucional.

Camadas Python:

- `domain`: DTOs estritos, regras de transição, catálogo IBGE e portas de persistência.
- `application`: casos de uso dependentes das portas `ActionRepository` e `BeneficiaryRepository`.
- `infrastructure`: adaptadores SQLAlchemy, cifragem, leitura institucional, PDF e worker de outbox.
- `security`: sessão opaca (somente hash persistido), CSRF, rate limit persistente e autorização.
- `api`: composição, dependências e endpoints versionados. Consulta individual/edição/segunda via de beneficiários usam serviço e porta próprios. Cadastro inicial e parte dos fluxos anteriores de importação ainda compõem adaptadores nas rotas; sua extração adicional permanece melhoria arquitetural.

O SQLite em `backend/private/` serve exclusivamente ao desenvolvimento/testes. Não é fallback de falha do PostgreSQL. Em produção, PostgreSQL/TLS persiste as tabelas próprias no schema `actions_map`; a autenticação usa a consulta institucional delegada. Migrações Alembic e grants são operações administrativas separadas, sem criação de tabelas no startup. Nenhuma migração modifica as tabelas de profissionais ou Portal. Não há prontuário, `usuario_id` clínico ou criação de senha.

As mutações gravam alteração, auditoria e snapshot de outbox na mesma transação. Ações novas e editadas ficam em revisão; o estado de rascunho foi removido por decisão posterior do responsável. Aprovação, publicação e arquivamento exigem versão atual. Publicação exige integração HTTPS autenticada configurada e resumo validado; a entrega só é confirmada por ACK da Agenda. Arquivamento preserva beneficiários e retira os totais publicados.

Beneficiário: UUID próprio, dados gerais autorizados cifrados com Fernet autenticado e vinculados ao ID/versão no envelope existente. CPF validado e CPF documental pendente são distintos. Não há campos oculares, índice nominal, correlação clínica ou alteração estrutural do banco. Envelopes antigos ID/nome continuam legíveis. Compare-and-swap impede perda silenciosa de alterações concorrentes; consulta e edição são auditadas. Município de residência, município escrito na ficha e local da participação têm semânticas distintas. Participação aponta à ação e, quando informado, ao índice de um local. Enquanto houver participações localizadas, alteração da lista de locais é bloqueada para não remapear vínculos por acidente; substituição por entidades relacionais permanece evolução futura.

Importação por arquivos: `/importacoes` recebe PDF/CSV/JSON, transmite partes binárias pela BFF e armazena temporariamente o conteúdo cifrado no schema próprio. Migração `0003_private_file_import`, ownership por profissional, quotas, expiração, parser isolado e confirmação produtiva explícita. Revisão nominal com RHF/Zod; nenhum OCR externo. Confirmação transacional/idempotente por hash do documento/página ou registro/ação; mesma página em outro destino exige decisão do operador. Não há deduplicação automática entre fontes diferentes. [Detalhes e operação](IMPORTACAO_ARQUIVOS.md).

A Visão geral é a única página de métricas. A API privada `/api/v1/indicadores` continua fornecendo os totais; a antiga página homônima foi removida. `/dados-iniciais` redireciona para `/importacoes`. A carga assistida do acervo local fica em adaptador operacional de infraestrutura, sem dependência de SQLAlchemy nas entidades ou casos de uso de aplicação.

Worker: HTTPS com token servidor, DTO allowlist 1.1, pessoas contempladas distintas dentro da ação, chave idempotente, ACK, dez tentativas e backoff. Mutações tentam enviar em background; PostgreSQL coordena workers com SKIP LOCKED. Tecnologia pode sincronizar manualmente, com CSRF e auditoria. A operação deve agendar retentativas em períodos sem tráfego. Receptor e exportação de ações foram implementados na Agenda em schema próprio.

Horários de banco em UTC e apresentação em `America/Fortaleza`, conforme planejamento. Datas sem hora não são deslocadas pelo fuso. Formulários e respostas usam português brasileiro.

Referências técnicas verificadas: [MUI e App Router](https://mui.com/material-ui/integrations/nextjs/), [FastAPI e segurança](https://fastapi.tiangolo.com/tutorial/security/), [IBGE Localidades](https://servicodados.ibge.gov.br/api/docs/localidades). Os guias locais do pacote Next prevalecem para esta versão.
