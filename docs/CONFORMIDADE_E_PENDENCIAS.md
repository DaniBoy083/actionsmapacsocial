# Verificação de conformidade e próximos incrementos

Esta é uma **primeira entrega de desenvolvimento**, não a conclusão do MVP institucional nem certificação de conformidade absoluta. A especificação específica do AC Actions Map prevalece sobre as decisões conflitantes do planejamento anterior.

**Atualização de produção:** após solicitação expressa de hospedagem do backend na própria Vercel, foram implementados Services, binding privado, schema PostgreSQL `actions_map`, migração Alembic e credencial restrita. O relato operacional atual está em [deploy de produção](DEPLOY_PRODUCAO.md); as pendências de integração com Agenda, importação produtiva e homologação continuam válidas.

| Requisito | Estado nesta entrega |
| --- | --- |
| Nome, identidade visual e referências | Implementados; logotipo existente, paleta, login, sidebar responsiva e footer único |
| Cadastro próprio, sem tracking clínico | Implementado; nenhum vínculo automático com pacientes |
| Login sem seleção de equipe/tipo | Implementado; credencial institucional scrypt e equipe/tipo consultados no backend |
| Acesso administrativo + Administração/Tecnologia | Implementado; revalidação por requisição e revogação local ao perder o vínculo |
| Tecnologia exclusiva, inclusive API direta | Implementado e testado; diagnóstico sanitizado sem exibição de tokens |
| CRUD de ações e N locais PB | Implementado localmente; busca, filtros, paginação, versão/409, modal, edição e arquivamento confirmado |
| Beneficiários gerais e auditoria | Cadastro/leitura local cifrados; edição, correção/remoção, associação de cadastro existente a outra ação e busca/deduplicação supervisionada ainda pendentes |
| Importação histórica | Fonte autorizada local, prévia privada, revisão manual, lote idempotente; upload genérico/storage privado e OCR local opcional ainda pendentes |
| PDF real | 50 páginas inspecionadas; nenhuma pessoa real importada ou transcrita nesta entrega |
| Persistência PostgreSQL institucional | Schema `actions_map`, oito tabelas, revisão Alembic e credencial restrita provisionados; sem importação de pessoas |
| Aprovação e preview editorial | Rascunho → revisão → validada; edição retira aprovação; publicação permanece bloqueada |
| Pipeline sem dados pessoais | DTO e outbox transacional implementados, envio/ACK/backoff testados com transporte simulado; receptor e fluxo externo pendentes |
| Tokens e rotação | Exibe somente alias/escopo/status; provisionamento/rotação reforçados no secret manager ainda precisam de integração |
| Indicadores | Ações distintas, participações, municípios e revisões; recorte municipal de ações sem duplicar total global; filtros analíticos avançados e pessoas únicas pendentes |
| Not found e error page | `not-found.tsx`, `error.tsx` e `global-error.tsx`, português e recuperação sem detalhes internos |
| LGPD / retenção / publicação | Minimização técnica inicial; decisões institucionais e validação independente ainda pendentes |
| Legado e escritor único | Inventário/documentação; nenhuma migração ou retirada de CRUD executada |
| Produção / backups / restauração | Hospedagem conjunta e persistência preparadas; restauração integral e homologação continuam pendentes |

## Verificações

Resultado final local em 26/10/2026: **34 testes pytest aprovados**, **10 cenários Playwright aprovados** (desktop/celular), incluindo varredura Axe do login, painel e modal sem violações nas regras WCAG A/AA selecionadas. ESLint, TypeScript, Ruff, build Next de produção e `pip check` aprovados. Inspeção visual das capturas confirmou a correção da altura dos campos, contraste e composição institucional. Não houve uso de dados reais nos testes.

Foram encontradas e corrigidas durante a validação: conflito de `box-sizing`/fonte com inputs MUI, herança de cor em links usados como botões, selects não controlados, contabilização indevida de logins bem-sucedidos no limite por conta e seletores ambíguos nos testes. A suíte final foi repetida integralmente após as correções. Há um aviso de depreciação do transporte httpx no TestClient da versão instalada de Starlette; não impede os testes e deve ser acompanhado em futura atualização das dependências.

Executar: `npm.cmd run lint`, `npm.cmd run typecheck`, `npm.cmd run build`, `npm.cmd run test:backend` e `npm.cmd run test:e2e`. Resultados finais e comandos completos constam no README. Testes usam identidades/fontes sintéticas e bancos temporários; não fazem gravações institucionais. A existência de testes aprovados não substitui homologação, avaliação de acessibilidade por pessoa usuária ou testes de infraestrutura.

## Próxima sequência

1. Revisar o modelo relacional final e os casos de uso restantes de beneficiários/importações; migrar a persistência local para schema institucional isolado com Alembic/grants aprovados.
2. Definir conta ativa/SSO e sessão distribuída; confirmar formatos adicionais de hash legados e recuperação de acesso pela Agenda.
3. Implementar upload privado, rotação de páginas, quotas, processamento limitado e correções/deduplicação supervisionadas. A primeira página e outras fichas do PDF estão giradas; a orientação do visualizador precisa ser ajustável.
4. Implementar o receptor e a integração externa descritos em `AGENDA_DIGITAL_IMPLEMENTACAO.md`; homologar a governança editorial e métricas municipais/temporais.
5. Testar backup/restauração, homologar privacidade/acessibilidade, conciliar legado e executar a virada com único escritor.
