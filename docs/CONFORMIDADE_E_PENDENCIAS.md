# Verificação de conformidade e próximos incrementos

Esta é uma **primeira entrega de desenvolvimento**, não a conclusão do MVP institucional nem certificação de conformidade absoluta. A especificação específica do AC Actions Map prevalece sobre as decisões conflitantes do planejamento anterior.

**Atualização de produção:** após solicitação expressa de hospedagem do backend na própria Vercel, foram implementados Services, binding privado, schema PostgreSQL `actions_map`, migração Alembic e credencial restrita. O relato operacional atual está em [deploy de produção](DEPLOY_PRODUCAO.md); as pendências de integração com Agenda, importação produtiva e homologação continuam válidas.

**Revisão posterior — importações e navegação:** Visão geral concentra os indicadores; a página redundante foi removida. Dados iniciais foi substituída por importação PDF/CSV/JSON com storage temporário cifrado e autorização expressa de produção. A descrição abaixo registra a primeira entrega; o estado atualizado, as correções e os limites estão em [revisão dos princípios](REVISAO_PRINCIPIOS_2026-10-26.md) e [importação por arquivos](IMPORTACAO_ARQUIVOS.md).

| Requisito | Estado nesta entrega |
| --- | --- |
| Nome, identidade visual e referências | Implementados; logotipo existente, paleta, login, sidebar responsiva e footer único |
| Cadastro próprio, sem tracking clínico | Implementado; nenhum vínculo automático com pacientes |
| Login sem seleção de equipe/tipo | Implementado; credencial institucional scrypt e equipe/tipo consultados no backend |
| Acesso administrativo + Administração/Tecnologia | Implementado; revalidação por requisição e revogação local ao perder o vínculo |
| Tecnologia exclusiva, inclusive API direta | Implementado e testado; diagnóstico sanitizado sem exibição de tokens |
| CRUD de ações e N locais PB | Implementado localmente; busca, filtros, paginação, versão/409, modal, edição e arquivamento confirmado |
| Beneficiários gerais e auditoria | Cadastro/leitura local cifrados; edição, correção/remoção, associação de cadastro existente a outra ação e busca/deduplicação supervisionada ainda pendentes |
| Importação por arquivos | PDF/CSV/JSON, prévia privada, revisão manual, rotação, lote idempotente e storage temporário cifrado; OCR não é presumido, conciliação entre fontes continua pendente |
| PDF real | 50 fichas aprovadas pelo responsável e importadas; municípios ausentes preenchidos com Mamanguape por orientação expressa; nenhuma ficha pendente; prévia e transcrições privadas fora do Git |
| Persistência PostgreSQL institucional | Schema `actions_map`, dez tabelas, Alembic até `0003_private_file_import`, sessão distribuída e credencial restrita |
| Aprovação e preview editorial | Rascunho → revisão → validada; edição retira aprovação; publicação permanece bloqueada |
| Pipeline sem dados pessoais | DTO e outbox transacional implementados, envio/ACK/backoff testados com transporte simulado; receptor e fluxo externo pendentes |
| Tokens e rotação | Exibe somente alias/escopo/status; provisionamento/rotação reforçados no secret manager ainda precisam de integração |
| Visão geral e indicadores | Única página de métricas, ações distintas/participações/municípios/revisões; filtros analíticos avançados e pessoas únicas pendentes |
| Not found e error page | `not-found.tsx`, `error.tsx` e `global-error.tsx`, português e recuperação sem detalhes internos |
| LGPD / retenção / publicação | Minimização técnica inicial; decisões institucionais e validação independente ainda pendentes |
| Legado e escritor único | Inventário/documentação; nenhuma migração ou retirada de CRUD executada |
| Produção / backups / restauração | Hospedagem conjunta e persistência preparadas; restauração integral e homologação continuam pendentes |

## Verificações

Resultado final local em 26/10/2026: **34 testes pytest aprovados**, **10 cenários Playwright aprovados** (desktop/celular), incluindo varredura Axe do login, painel e modal sem violações nas regras WCAG A/AA selecionadas. ESLint, TypeScript, Ruff, build Next de produção e `pip check` aprovados. Inspeção visual das capturas confirmou a correção da altura dos campos, contraste e composição institucional. Não houve uso de dados reais nos testes.

Foram encontradas e corrigidas durante a validação: conflito de `box-sizing`/fonte com inputs MUI, herança de cor em links usados como botões, selects não controlados, contabilização indevida de logins bem-sucedidos no limite por conta e seletores ambíguos nos testes. A suíte final foi repetida integralmente após as correções. Há um aviso de depreciação do transporte httpx no TestClient da versão instalada de Starlette; não impede os testes e deve ser acompanhado em futura atualização das dependências.

Executar: `npm.cmd run lint`, `npm.cmd run typecheck`, `npm.cmd run build`, `npm.cmd run test:backend` e `npm.cmd run test:e2e`. Resultados finais e comandos completos constam no README. Testes usam identidades/fontes sintéticas e bancos temporários; não fazem gravações institucionais. A existência de testes aprovados não substitui homologação, avaliação de acessibilidade por pessoa usuária ou testes de infraestrutura.

## Próxima sequência

1. Completar casos de uso de correção/remoção e associação de beneficiários existentes, conciliação entre fontes e evolução relacional dos locais. Persistência institucional e Alembic/grants já foram implementados.
2. Homologar revogação institucional, recuperação de acesso pela Agenda e eventual SSO. A sessão PostgreSQL distribuída, scrypt e revalidação de equipe/tipo já estão implementados.
3. Agendar e monitorar o expurgo de arquivos e homologar retenção. As 50 fichas históricas já foram aprovadas pelo responsável e importadas. Upload privado, rotação, quotas e parser limitado estão implementados; OCR local continua opcional e não autoriza inferir nomes.
4. Implementar o receptor e a integração externa descritos em `AGENDA_DIGITAL_IMPLEMENTACAO.md`; homologar a governança editorial e métricas municipais/temporais.
5. Testar backup/restauração, homologar privacidade/acessibilidade, conciliar legado e executar a virada com único escritor.
