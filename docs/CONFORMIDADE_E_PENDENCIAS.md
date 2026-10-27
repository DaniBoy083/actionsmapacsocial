# Verificação de conformidade e próximos incrementos

**Revisão de 27/10/2026:** mapa consolidado interno implementado conforme adaptação autorizada do anexo. [Estado atual, evidências e pendências](AUDITORIA_APLICACAO_E_PRINCIPIOS.md); [contrato/configuração/operação](MAPA_CONSOLIDADO_ACTIONS_MAP.md). As contagens e descrições abaixo registram entregas anteriores. A nova consulta não está configurada com credencial própria e não comprova propagação real até o Portal.

Esta é uma **primeira entrega de desenvolvimento**, não a conclusão do MVP institucional nem certificação de conformidade absoluta. A especificação específica do AC Actions Map prevalece sobre as decisões conflitantes do planejamento anterior.

**Atualização de produção:** Services, binding privado, schema PostgreSQL `actions_map` e credencial restrita foram implementados. A carga das 50 fichas e o recebimento do resumo na Agenda foram conferidos; o relato está em [deploy de produção](DEPLOY_PRODUCAO.md). A gestão de tokens desta entrega exige aplicar até 0006 antes de seu deploy. Consumo pela Plataforma/Portal e homologações institucionais permanecem separados dessa entrega.

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
| Persistência PostgreSQL institucional | Produção registrada até 0004, dez tabelas próprias; revisão 0005 preparada acrescenta duas tabelas de integrações. Sessão distribuída e credencial restrita preservadas |
| Aprovação e preview editorial | Cadastro direto em revisão → validada → publicada; estado antigo removido da aplicação e bloqueado por constraint SQL; edição retira aprovação |
| Pipeline sem dados pessoais | Contrato 1.1, outbox/ACK/backoff e receptor na Agenda implementados; envia pessoas contempladas, quantidade de ações e municípios; consumo pela Plataforma/Portal pendente |
| Tokens e rotação | Tokens de leitura para a Agenda: criação/exibição única, confirmação da senha, hash, validade por prazo ou Nunca expirar, cota, rotação/revogação auditadas e cópia de endpoints/cURL. A credencial de envio existente permanece no secret manager. Migrações 0005/0006 preparadas, preservando prazos anteriores, sem alteração produtiva nesta entrega |
| Visão geral e indicadores | Única página de métricas, ações distintas/participações/municípios/revisões; filtros analíticos avançados e pessoas únicas pendentes |
| Not found e error page | `not-found.tsx`, `error.tsx` e `global-error.tsx`, português e recuperação sem detalhes internos |
| LGPD / retenção / publicação | Minimização técnica inicial; decisões institucionais e validação independente ainda pendentes |
| Legado e escritor único | Inventário/documentação; nenhuma migração ou retirada de CRUD executada |
| Produção / backups / restauração | Hospedagem conjunta e persistência preparadas; restauração integral e homologação continuam pendentes |

## Verificações

Resultado local atualizado em 26/10/2026: **77 testes pytest aprovados**, **16 cenários Playwright aprovados** (desktop/celular), incluindo varredura Axe do login, painel, modal e integrações sem violações nas regras WCAG A/AA selecionadas. ESLint, TypeScript, Ruff, build Next de produção e `pip check` aprovados. Inspeção visual das capturas confirmou a correção da altura dos campos, contraste e composição institucional. Não houve uso de dados reais nos testes. A migração/grants, exportação e revogação também foram verificadas em PostgreSQL descartável; a cota aceitou 60 de 70 chamadas com 12 trabalhadores concorrentes. Detalhes e instalação em [gestão de integrações](GESTAO_TOKENS_E_ENDPOINTS_AGENDA.md).

Foram encontradas e corrigidas durante a validação: conflito de `box-sizing`/fonte com inputs MUI, herança de cor em links usados como botões, selects não controlados, contabilização indevida de logins bem-sucedidos no limite por conta e seletores ambíguos nos testes. A suíte final foi repetida integralmente após as correções. Há um aviso de depreciação do transporte httpx no TestClient da versão instalada de Starlette; não impede os testes e deve ser acompanhado em futura atualização das dependências.

Executar: `npm.cmd run lint`, `npm.cmd run typecheck`, `npm.cmd run build`, `npm.cmd run test:backend` e `npm.cmd run test:e2e`. Resultados finais e comandos completos constam no README. Testes usam identidades/fontes sintéticas e bancos temporários; não fazem gravações institucionais. A existência de testes aprovados não substitui homologação, avaliação de acessibilidade por pessoa usuária ou testes de infraestrutura.

## Próxima sequência

1. Completar casos de uso de correção/remoção e associação de beneficiários existentes, conciliação entre fontes e evolução relacional dos locais. Persistência institucional e Alembic/grants já foram implementados.
2. Homologar revogação institucional, recuperação de acesso pela Agenda e eventual SSO. A sessão PostgreSQL distribuída, scrypt e revalidação de equipe/tipo já estão implementados.
3. Agendar e monitorar o expurgo de arquivos e homologar retenção. As 50 fichas históricas já foram aprovadas pelo responsável e importadas. Upload privado, rotação, quotas e parser limitado estão implementados; OCR local continua opcional e não autoriza inferir nomes.
4. Ativar o consumidor da Plataforma para a exportação já implementada na Agenda, conforme `AGENDA_DIGITAL_IMPLEMENTACAO.md`; homologar a governança editorial e métricas municipais/temporais.
5. Testar backup/restauração, homologar privacidade/acessibilidade, conciliar legado e executar a virada com único escritor.
