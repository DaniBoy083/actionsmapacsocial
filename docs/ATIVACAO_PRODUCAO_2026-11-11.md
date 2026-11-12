# Ativação em produção — 11/11/2026

O responsável solicitou expressamente **“ative a prod”**, após autorizar os campos
clínicos e as migrações. Esta operação ativa o registro clínico em preenchimento
implementado em `7a9aadf`; não amplia o escopo para conclusão de exame, prescrição,
etiqueta ou novas contas. A descrição funcional e a matriz literal da ficha estão em
[profissionais e campos clínicos](PROFISSIONAIS_E_CAMPOS_CLINICOS_2026-11-11.md).
As afirmações de ausência de ativação naquele documento descrevem a entrega anterior
de código; este registro documenta a operação posterior autorizada.

## Ambiente e resultado

| Item | Evidência |
| --- | --- |
| Projeto Vercel | `actionsmapacsocial` |
| Domínio | <https://actionsmapacsocial.vercel.app> |
| Commit publicado | `7a9aadf6cc35399d55cb0c0a0cf7b57c60f4ee31` |
| Novo deployment | `dpl_A2kLbRZG21VpXisYVfhTtLKZzr6F`, `READY`, associado ao domínio |
| Deployment anterior | `dpl_7itGPue2QXR1h1p7otgTZt1fWEwv`, mesmo commit, configuração clínica anterior desligada |
| PostgreSQL | Schema `actions_map`, revisão `0006_nonexpiring_tokens` → `0009_clinical_fields` |
| Configuração | `CLINICAL_FIELDS_ENABLED=true`; `CLINICAL_KEY` nova, sensível, distinta de `BENEFICIARIES_KEY`, somente em `production` |
| Preservação | 1 ação, 50 cadastros de beneficiários, 50 participações; valores anteriores conferidos por hashes calculados localmente |
| Registros clínicos/profissionais | Zero no encerramento da verificação; nenhum usuário, profissional, atribuição ou paciente de teste foi criado |

A API da Vercel confirmou o SHA do deployment anterior. Foi feito redeploy dessa
mesma origem, incorporando a configuração nova, sem upload dos arquivos do workspace.
AC Auth, AC Core, credenciais institucionais e contratos de integração não foram alterados.
O SQLite e a configuração de desenvolvimento não foram ativados por esta operação.

## Backup, migrações e permissões

Foi criado um dump consistente **somente do schema `actions_map`**, usando snapshot
exportado pelo PostgreSQL. O conteúdo foi cifrado em memória com a chave geral
existente antes de ser gravado. A descriptografia e a leitura do arquivo foram
conferidas; o backup foi restaurado em PostgreSQL 18 local descartável e todas as
linhas anteriores foram comparadas por hashes, sem imprimir seu conteúdo.

Nesse ambiente restaurado, `0007_institutional_metadata`, `0008_staff_assignments`
e `0009_clinical_fields` foram executadas, seguidas de nova execução até `0009`
para conferir idempotência. As linhas anteriores e os grants foram preservados.
A instância temporária foi encerrada e seu diretório descartável removido.
Uma primeira inicialização local reteve pipes no Windows; ela foi encerrada antes
da repetição bem-sucedida. Essa falha ocorreu antes de qualquer alteração produtiva.

A aplicação real ocorreu em transação, com trava administrativa de migração,
timeouts e bloqueio temporário de escrita nas tabelas existentes do módulo.
Todos os valores anteriores foram comparados antes/depois, dentro da transação.
Metadados dos schemas `public`/`portal` e as flags de RLS também foram comparados
e permaneceram iguais. Não houve importação, movimentação de banco ou downgrade.

A credencial runtime foi conferida por conexão própria, incluindo leitura das
tabelas novas. O papel não possui superuser, bypass de RLS ou associação herdada
a outros papéis. Nas sete tabelas novas, foram conferidos os privilégios efetivos:
SELECT/INSERT; UPDATE somente nos cadastros, atribuições e ficha atual.
Históricos, marcas e revisões institucionais não admitem UPDATE; nenhuma dessas
tabelas concede DELETE/TRUNCATE/REFERENCES/TRIGGER ao runtime.

As evidências operacionais ficam fora do Git:

- `artifacts/migrations/production-clinical-activation.json`: etapas, hashes,
  contagens, identificadores e resultado dos checks; sem linhas de pacientes.
- `artifacts/private-import/backups/`: dump cifrado anterior à revisão `0009`;
  o caminho exato está no relatório privado acima.
- `artifacts/production-config.env`: configuração privada anterior, preservada,
  incluindo a chave geral necessária ao backup.
- `artifacts/private-secrets/clinical-production.env`: recuperação da chave clínica,
  separada do dump e não versionada. Preservar sua custódia e a configuração remota;
  não executar geração/rotação de chave novamente ao republicar.

## Verificação após a publicação

O domínio público foi consultado depois de confirmar `READY` e sua associação
ao novo deployment. A flag foi lida pelo endpoint individual de configuração
da Vercel, sem revelar qualquer segredo. A chave foi conferida como sensível e
restrita a produção; o arquivo de recuperação foi validado com Fernet.

| Verificação externa | Resultado |
| --- | --- |
| Health da API e login | HTTP 200; health `API_OK` |
| Página `/profissionais` sem sessão | Redirecionamento para `/login` por streaming do Next.js, com HTTP 200 e tag de redirecionamento conferida |
| Sessão, ações, profissionais e indicadores sem autenticação | HTTP 401 |
| Decisão de acesso, leitura e gravação clínicas sem autenticação | HTTP 401 |
| Gravação clínica com origem externa | HTTP 403 |
| Respostas das APIs privadas acima | `Cache-Control: no-store` |

Os caminhos clínicos de teste usaram UUIDs sintéticos, sem identificadores reais
e sem sessão. Não houve gravação de paciente ou concessão artificial de acesso.
A conferência final confirmou novamente revisão `0009`, privilégios efetivos,
schemas compartilhados/RLS e preservação dos dados da ação, beneficiários e
participações existentes. Não foi executada nova exportação para Agenda/Portal.

O commit já tinha 184 testes backend, 28 E2E, lint, TypeScript, build, Ruff,
`pip check` e teste PostgreSQL descartável aprovados, conforme o registro da
implementação. Nesta operação foram executados restore/ensaio e checks produtivos;
esses resultados não são homologação clínica ou teste de impressão física.

## Uso e limites

O recurso está ligado no ambiente produtivo. O cadastro/atribuição administrativa
não cria uma conta de login nem concede acesso clínico por si só. Cada operação
continua exigindo sessão institucional validada, vínculo à própria identidade,
habilitação conferida, autorização clínica específica e atribuição ativa à ação/local.
Acesso administrativo sozinho não permite ler campos clínicos.

Não foi exercitada uma gravação clínica autenticada em produção: não há profissional
habilitado/atribuído nesse banco, e não foram inventados cadastros ou competências.
A verificação da cifra e da autorização com escrita permanece a da suíte e do
PostgreSQL descartável. Não se declara piloto homologado, conformidade absoluta,
exame concluído ou receita assinada. Permanecem os limites funcionais e de governança
documentados na implementação, inclusive identidade operacional, competências,
finalidade/retenção, custódia externa das chaves e revisão dos documentos físicos.

## Reversão

Para interromper novas entradas clínicas, a Tecnologia deve mudar somente a variável
de produção `CLINICAL_FIELDS_ENABLED` para `false` e republicar a versão compatível.
Manter `CLINICAL_KEY`, `BENEFICIARIES_KEY`, registros, versões, atribuições e backups.
Não executar downgrade nem apagar tabelas como parte da reversão.

Se houver regressão da publicação, o deployment anterior identificado acima é o
candidato de rollback do domínio, sujeito à conferência da configuração e dos
registros produzidos desde a ativação. Ele contém o mesmo código, com a configuração
clínica anterior desligada. Reverter o domínio não altera automaticamente as variáveis
do projeto: corrigir a flag também para as publicações futuras.

Uma restauração produtiva do dump não foi executada nem está autorizada por este
registro. Exige interromper escritas, reconciliar alterações posteriores ao backup
e autorização própria. O ensaio de restore comprovou recuperação do snapshot em
ambiente descartável; não equivale à homologação da recuperação integral da base
compartilhada. Não usar `scripts/provision_production.py` para atualizar esta base
em uso; seu fluxo é de provisionamento inicial.
