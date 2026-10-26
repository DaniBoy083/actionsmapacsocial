# Publicação e fluxo das ações

Decisão do responsável: remover o estado de rascunho e publicar o resumo da ação na Agenda com número de pessoas contempladas, número de ações e município.

## Estados ativos

1. Cadastro novo e edição ficam **Em revisão**.
2. Aprovar o resumo muda para **Validada**.
3. **Publicar na Agenda** muda para **Publicada** e grava o evento na outbox na mesma transação.
4. O recebimento só aparece como confirmado após o ACK da Agenda.
5. Alteração de dados ou inclusão de beneficiários retorna a ação para revisão e retira a aprovação anterior. Arquivamento preserva os beneficiários e retira os totais publicados.

O estado removido não integra a enumeração, filtros, opções ou formulários. A migração `0004_remove_drafts` converte registros antigos para revisão, incrementa sua versão, registra auditoria e enfileira um novo snapshot. A constraint SQL só permite `em_revisao`, `validada`, `publicada` e `arquivada`.

## Resumo enviado

Contrato **1.1**: `quantidade_pessoas_contempladas` é a contagem de IDs distintos de beneficiários dentro da ação; `quantidade_acoes` é 1 por ação ativa, 0 para arquivamento; `municipios_ibge` preserva os códigos dos locais da ação. `quantidade_participacoes` é mantido separadamente. Não há deduplicação de pessoas por nome ou entre ações.

Melhor Visão: **50 pessoas contempladas, 1 ação, Mamanguape (2508901)**. O payload inclui identificadores técnicos, revisão, operação, categoria e período opcional. Não contém nomes de beneficiários, CPF, contato, prontuário, ficha ou identificador individual.

Uma ação em vários municípios continua sendo uma ação no total global. Seu total de pessoas não deve ser distribuído ou repetido como total independente em cada município.

## Entrega e recebimento

- Map: `POST /api/v1/acoes/{id}/publicar`, com sessão autorizada, origem, CSRF e versão atual. Exige resumo aprovado e integração HTTPS configurada.
- Agenda: `POST /api/integracoes/v1/acoes/resumos`, credencial Bearer exclusiva, hash do segredo no receptor e `Idempotency-Key` correspondente à ação/revisão.
- Confirmação: ACK com versão 1.1 e o mesmo `event_id`; `accepted` ou `duplicate`. HTTP 2xx sem ACK não confirma entrega.
- Conferência independente: GET da mesma rota com `acao_id` e credencial de serviço.
- Plataforma: `GET /api/analytics/acoes?page=1`, chave de analytics existente, 100 snapshots por página e totais sobre revisões correntes publicadas. O consumidor da Plataforma deve ativar essa fonte antes de atualizar o Portal.

O receptor grava inbox e snapshot em schema isolado `agenda_actions`, via migração versionada `202610260001`. Reenvio idêntico não duplica; conteúdo divergente gera 409; eventos antigos não substituem revisões recentes. Não altera as tabelas clínicas ou de autenticação da Agenda.

Mutações do Map tentam entregar em background após o commit, conforme o [ciclo de BackgroundTasks do FastAPI](https://fastapi.tiangolo.com/tutorial/background-tasks/). A outbox usa `SKIP LOCKED` no PostgreSQL, retenta com backoff e limita tentativas. A operação pode usar **Sincronizar resumos com a Agenda**, exclusivo de Tecnologia e auditado, ou o worker por CLI. Para retentar sem tráfego, agendar o worker em executor institucional; ainda não existe agendamento permanente presumido.

Eventos de revisões superadas ficam `substituido`; eventos do contrato anterior sem substituto aguardam republicação. Edição ou arquivamento publicam um snapshot de retirada de elegibilidade, preservando auditoria.

## Operação e segurança

As configurações de serviço são privadas: `AGENDA_SUMMARIES_URL`, `AGENDA_SERVICE_TOKEN` no Map e `ACTIONS_MAP_TOKEN_SHA256` na Agenda. O provisionamento não reutiliza senhas de profissionais nem a chave de exportação clínica. Nunca copiar esses valores para `NEXT_PUBLIC_*`, logs ou documentação.

`scripts/migrate_publication.py --target agenda --apply` e `--target map --apply` aplicam somente as revisões respectivas após backup cifrado verificado, com lock e timeout. Preservam a contagem de beneficiários e as flags de RLS. O receptor foi preparado e testado numa cópia isolada antes de ser aplicado à Agenda.

Verificação: testes de contrato, autenticação, ACK, publicação/retirada, idempotência, ordenação, migrações e ausência do estado removido; checks de arquitetura/OpenAPI/documentação da Agenda, builds dos dois projetos e navegação desktop/celular. A recepção na Agenda e a atualização do Portal são etapas distintas do fluxo institucional.

## Resultado em produção — 26/10/2026

Migrações aplicadas, status antigos convertidos e nenhuma ação em rascunho. Melhor Visão está **Publicada**, revisão **9**, com entrega `entregue` confirmada por ACK 1.1. O GET autenticado da Agenda retornou o mesmo snapshot enviado: **50 pessoas contempladas, 1 ação, Mamanguape (2508901)**. Os 50 beneficiários cifrados foram preservados. O consumidor da Plataforma continua sendo a próxima etapa para alimentar o Portal.
