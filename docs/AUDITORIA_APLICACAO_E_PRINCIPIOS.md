# Auditoria técnica da aplicação e princípios — 30/10/2026

## Estado atual contra o plano v2.1

**Conclusão: a aplicação NÃO está integralmente de acordo com o MVP ocular de
30/10. O novo piloto NÃO está liberado.** O fluxo geral existente passou nas
verificações locais; faltam funcionalidades e aceites da nova especificação.
O `PROMPT_INICIAL_SOL.md` determina Fase 0, inventário e planejamento, sem
implementação clínica. Não se apresenta documentação como sistema implementado.

Entregáveis desta revisão:

- [Descoberta e matriz literal da ficha](FASE_0_DESCOBERTA_2026-10-30.md): fontes,
  hashes, páginas/aba/células, campos, esquema local em leitura, RBAC e contratos.
- [Modelo proposto, backlog e aceite](PLANO_MVP_E_ACEITE_2026-10-30.md): prioridades,
  contrato agregado futuro, migração/rollback e testes físicos ainda pendentes.
- Correção de privacidade: fonte XLSX preenchida retirada do índice, mantida no
  disco com hash idêntico; ignore para fontes, checagem Git com nomes Unicode/NUL,
  modo `--tracked` no CI e nove casos sintéticos de regressão. Nenhum valor de
  paciente foi incluído nos novos documentos/testes.

| Requisito/princípio de 30/10 | Evidência atual | Estado |
| --- | --- | --- |
| Ler a ficha real antes de modelar | XLSX uma aba A1:X25 lido estruturalmente/renderizado com valores ocultos; PDF 50 páginas renderizado localmente, OCR só de rótulos e contatos mascarados | Fonte localizada; versão oficial/valores ilegíveis, inclusive página 34, pendentes |
| Campos fiéis e minimização | Matriz separa mãe/responsável, CPF paciente/profissional, observação clínica/geral, município do termo/residência/evento | Documentado; nova coleta depende de aprovação |
| Identidade e autorização no servidor | Tipo administrativo e equipes Admin/Tech revalidados; CSRF, sessão e acesso técnico exclusivo testados | Atende fluxo anterior; recepção/médico com escopo por ação/caso ainda ausentes |
| Banco operacional independente | SQLite próprio local; código produtivo usa URL lógica comum com schema isolado e função delegada | Nova topologia/grants não homologados; nenhum acesso SQL produtivo nesta execução |
| Três marcas em TOTAL/PARCIAL | Logo AC Social real no shell/login; não há upload governo/clínica no cadastro | Não implementado no novo fluxo; segunda via atual usa cabeçalho textual |
| Nome/número/autor da emenda na ação e herança | Campos ausentes de ActionInput/Action, UI e contratos atuais | Não implementado; proposta com histórico/snapshot documentada |
| Triagem, ficha clínica e atribuição | DTOs e persistência atuais são gerais; prévias históricas podem conter imagem de saúde | Não implementado; segregação operacional é gate de liberação |
| Ficha + etiqueta, impressão conjunta/individual | Existe segunda via geral A4 dos dados atuais, com emissão auditada | Documento clínico/etiqueta/snapshot não implementados; impressão física pendente |
| Contadores e analytics completo | Dashboard diferencia participações de pessoas únicas; escopo todo período/não arquivadas | Filtros novos, pessoas reconciliadas, fichas/etiquetas/entregas e emenda/autor pendentes |
| Pipeline obrigatório sem PII de paciente | Item 1.1 allowlist, outbox/ACK, token/escopo e exportação testados; definições vizinhas lidas | Metadados novos exigem versão coordenada; E2E das quatro aplicações não executado |
| Documentação corresponde ao código | Relatos anteriores preservados como histórico; inventário atual distingue código, proposta e deploy | Corrigido para esta revisão |
| Fontes privadas fora de Git | XLSX preenchido estava rastreado; agora retirado do índice e protegido; original preservado | Corrigido no próximo estado versionado; histórico anterior ainda requer avaliação |
| Assinatura digital e login local avançado | Não introduzidos; ambos permanecem em standby | Conforme decisão do MVP; acesso mínimo seguro continua obrigatório |
| Retenção, restauração, governança e aceites | Lacunas documentadas, sem prazos/autorizações fabricados | Não homologado; impede alegação de 100% |

### Verificações executadas em 30/10

| Comando/verificação | Resultado observado |
| --- | --- |
| `npm.cmd run test:backend` | **114 aprovados**, 27,82s: 105 existentes e nove casos novos do gate Git; fontes/identidades sintéticas |
| `npm.cmd run test:e2e` | **20 aprovados**, desktop/celular, saída 0, sem retries; geração dos PDFs sintéticos de segunda via e verificações Axe |
| `npm.cmd run lint` | Aprovado |
| `npm.cmd run typecheck` | Aprovado, tipos de rota gerados e tsc sem erro |
| `npm.cmd run build` | Aprovado, 13 páginas geradas; nenhuma rota clínica/etiqueta foi adicionada |
| `python -m ruff check --config backend/pyproject.toml backend/app backend/tests scripts` | Aprovado, incluindo o novo teste/script |
| `python -m pip check` | Sem incompatibilidades instaladas |
| `python scripts/check_staged_privacy.py --tracked` | Aprovado após retirar a fonte do índice; cobre caminhos rastreados, não classificação semântica de todo conteúdo |
| Impressão digital da segunda via atual | PDFs sintéticos desktop/celular com uma página A4 cada; renderização desktop inspecionada, campos/declaração/assinatura em branco legíveis e sem navegação. Não é teste físico nem impressão da nova ficha clínica |
| Fonte XLSX após retirada do índice | Arquivo local existente com SHA-256 idêntico ao inventário |
| Metadados de SQLite | 12 tabelas, somente leitura; nenhum registro pessoal consultado |

O pytest mantém um aviso de depreciação httpx/Starlette já existente. O Playwright
concluiu os 20 cenários e aguardou encerramento dos servidores no Windows; foram
encerrados somente os dois processos de teste identificados nesta execução, nas
portas 3310/8310, permitindo o relatório final com saída 0.

Não foram repetidas operações produtivas históricas nem executados deploy,
importação, DDL, rotação de segredo, teste físico de impressão ou E2E com serviços
institucionais reais. CI foi configurado, mas não se afirma execução remota.
Testes verdes verificam os cenários existentes, não implementam os recursos que
faltam. O gate de privacidade não saneia commits antigos nem substitui revisão
de conteúdo/controle de acesso a anexos privados.

## Histórico da auditoria — 28/10/2026

As seções seguintes registram o escopo anterior. Afirmações de ausência de dados
oculares estruturados descrevem o código atual antigo; não revogam o novo plano.

## Escopo e conclusão

Implementada a decisão posterior do responsável: cadastro dos dados gerais do
PDF, excluindo graus/dados oculares; consulta e edição completas; segunda via
imprimível; remoção total da página do mapa desta aplicação. A solicitação
posterior autorizou a complementação no banco institucional. Ela substitui a
restrição anterior a nome/município e a implementação do mapa no commit `d361873`.

[Campos, contratos, operação e resultado do lote](CADASTRO_BENEFICIARIOS_E_SEGUNDA_VIA.md).
O anexo original e os relatos anteriores foram preservados como histórico,
com indicação do estado atual. Guias locais do Next 16.4.3 foram consultados.

Os controles técnicos abaixo foram verificados nos cenários descritos. **Não se
declara conformidade absoluta de toda a aplicação/instituição**, nem se convertem
aprovações locais em homologações de infraestrutura, privacidade ou operação.

## Matriz de princípios

| Princípio | Evidência e tratamento |
| --- | --- |
| Fronteiras do domínio | Cadastro próprio de ações/beneficiários; sem prontuários, graus, atributos oculares ou vínculo automático à identidade clínica |
| Identidade institucional | Login único, sem escolha de tipo/equipe; tipo administrativo e vínculo Administração/Tecnologia revalidados no backend; revogação bloqueia ficha e segunda via |
| Mínimo privilégio | APIs individuais verificam participação na ação; ausência de vínculo retorna 404. Diagnóstico/tokens continuam exclusivos de Tecnologia |
| Arquitetura | DTOs/porta no domínio; serviço depende de `BeneficiaryRepository`; persistência/cifragem/auditoria em infraestrutura; composição na API. Fluxos antigos de cadastro/importação ainda têm extração arquitetural pendente |
| Contratos e validação | Pydantic/Zod, allowlist, extra forbid, CPF com verificadores, CPF documental separado, datas e municípios PB; telefone sem DDD inventado. OpenAPI/schemas regenerados |
| Completude honesta | Todos os campos gerais da fonte estão disponíveis; ausência/ilegibilidade permanece explícita, sem fabricar valores para tornar a ficha aparentemente completa |
| Privacidade | Novos dados no envelope Fernet existente, vinculado ao ID e versão; sem novas colunas nominais/índices, conteúdo na auditoria ou dados reais em testes/Git |
| Integridade e concorrência | Envelopes antigos legíveis; edição com versão e compare-and-swap; auditoria na mesma transação; tentativa antiga recebe 409 |
| Separação de métricas | Município da ficha, residência e local da participação distintos; dados privados não entram no outbox/exportação. Complementação produtiva preservou ação, participações e resumos |
| Entrada não confiável | Validação compartilhada na importação/manual; proteção anterior de parser, tamanho, quotas, ownership e storage cifrado preservada; campos oculares/assinatura estruturada rejeitados |
| Transporte e acesso | BFF com allowlist, cookies privados, origem/CSRF nas mutações; respostas no-store, nosniff e no-referrer; nenhuma credencial NEXT_PUBLIC |
| Segunda via | Dados atuais, revisão e emissão em Brasília; impressão A4 com nova assinatura em branco. Emissão auditada não confirma recebimento ou impressão física |
| Interface e branding | Componentes MUI, identidade vermelho/vinho e shell existentes; campos RHF/Zod compartilhados entre cadastro, edição e revisão de importação |
| Acessibilidade | Conteúdo com rolagem recebe foco pelo teclado; controles identificam pessoa, erro e estado. Axe e cenários desktop/celular, sem desativar regras para passar |
| Remoção do mapa | Página, sidebar, endpoint/BFF, DTOs, adaptadores, malha, cache, configuração, diagnóstico e contratos específicos excluídos; verificações de 404 e ausência de navegação |
| Operação autorizada | Lote por hash/página/ação, revisão, prévia com rollback, backup cifrado verificado, transação, locks, auditoria técnica explícita e leitura posterior; nenhum deploy executado |

O campo de observações é texto livre de uso geral. A orientação de não inserir
conteúdo ocular depende também do operador; não se promete classificação
semântica automática de todo texto. Isso está explícito na interface e no guia.

## Evidências executáveis

| Verificação local | Resultado |
| --- | --- |
| `npm.cmd run test:backend` | 105 aprovados, incluindo 28 casos novos do cadastro/complementação; SQLite descartável |
| `npm.cmd run test:e2e` | 20 aprovados em desktop/celular, sem retries; saída 0. Inspeção de impressão e ajuste final descritos abaixo |
| `npm.cmd run build` | Aprovado, TypeScript e 13 páginas geradas; `/mapa-acoes` ausente |
| `npm.cmd run typecheck` e `npm.cmd run lint` | Aprovados |
| Ruff `--config backend/pyproject.toml backend/app backend/tests scripts` | Aprovado |
| `python -m pip check` | Sem incompatibilidades instaladas |
| Contratos gerados | OpenAPI atual e schemas de cadastro/edição; contratos do mapa excluídos |
| Privacidade do staging/bundle | 141 valores pessoais da fonte e dez segredos locais procurados, nenhuma ocorrência no staging ou nos 32 arquivos JavaScript do build |

Arquivos privados e logs não entram no commit; o log gerado pelo navegador
foi incluído no `.gitignore` e a checagem de staging também recusa `.log`.

Os testes de backend verificam cifragem, leitura mínima versus ficha completa,
validação/ausência de eco de dados inválidos, CPF documental, telefone local,
legado, versão/CSRF, vínculo incorreto, revogação, ID do envelope, segunda via e
auditoria sem confirmar recebimento, CSV completo, idempotência/conflitos e
interrupção do lote inteiro quando falta origem. Testes anteriores de ações,
login, importação e integrações permanecem. A redução da contagem em relação
ao relatório anterior decorre da exclusão dos testes do mapa removido.

No navegador são verificados cadastro, leitura, edição e segunda via com dados
sintéticos, chamada explícita de impressão, CSS de impressão sem navegação,
ausência do mapa e regras WCAG A/AA selecionadas com Axe. Capturas e PDFs de
impressão são artefatos locais ignorados pelo Git. Não se confunde teste da
chamada `window.print` com comprovação de uma impressão física.

A inspeção visual do PDF gerado confirmou ficha legível em uma página A4,
com campos, declaração e espaço para assinatura. Identificou também o fundo
rosa do shell no espaço restante da folha; o CSS de impressão passou a usar
fundo branco e remover a sombra do painel. Esse ajuste foi verificado nos
cenários da segunda via e em nova inspeção do PDF renderizado.

Após o ajuste de impressão, os quatro cenários específicos de beneficiários
foram repetidos em desktop/celular, com saída 0 e sem violações Axe. Ambos os
PDFs gerados têm uma página A4 e contêm os dados sintéticos esperados.

A primeira rodada encontrou a área de leitura sem foco por teclado; foi corrigida
com região nomeada e `tabIndex`, mantendo as regras Axe ativas. Também foram
ajustados seletores exatos de células, pois os novos botões acessíveis incluem
o nome do beneficiário. Nenhuma quota de login foi aumentada/desativada.

O encerramento automático da árvore de processos pode aguardar neste sandbox
Windows. Depois dos casos finalizados, somente os servidores iniciados pela
própria suíte são encerrados para permitir que o runner emita o relatório final.
As portas 3310/8310 são isoladas e configuráveis; serviços do usuário não são
encerrados. Há um aviso conhecido de depreciação httpx/Starlette no TestClient.

## Conferência do lote produtivo

As 50 fichas foram inspecionadas em imagens locais. A operação autorizada
preencheu **294 campos em 50 cadastros**, sem novos beneficiários e sem conflitos.
O backup cifrado foi verificado antes da escrita. A comparação dos dados
operacionais antes/depois confirmou preservação de ação, participações e outbox.
Leitura posterior confirmou **294/294 campos iguais ao manifesto revisado**,
sem erro de codificação restante. A distribuição está no guia específico.

Uma repetição em prévia, lendo o manifesto cifrado, conferiu os mesmos 50
cadastros e propôs **zero atualizações e zero conflitos**, com rollback. Isso
também verificou o suporte operacional ao manifesto `.fernet` sem expor valores.

Uma falha de acentuação no transporte do PowerShell foi identificada em 41
campos de responsável e corrigida especificamente com novo backup, versão/CAS
e auditoria. A conferência final confirmou zero ocorrências. Não se apresenta
essa correção como novos campos nem se duplica a contagem de beneficiários.

O ator técnico `operacao-assistida:complemento-pdf` identifica a complementação;
a correção usa `operacao-assistida:correcao-utf8`. Não foi forjada identidade ou
sessão de funcionário. O script de complementação é administrativo, não uma
API pública, e exige confirmação explícita para escrita produtiva.

Anos abreviados de nascimento 77/84/89 foram normalizados para 1977/1984/1989,
conforme resposta do responsável; datas de ficha com ano 26 usam 2026. Datas
completas divergentes foram preservadas. Dois séculos de nascimento ainda
aguardam confirmação; valores ilegíveis/ausentes não foram inferidos. Cinco
CPFs legíveis que falham nos verificadores estão em campo documental pendente,
separado do CPF validado. Fonte, transcrições, manifestos e backups ficam privados,
cifrados quando preparados pela operação e fora do Git.

## Limites e pendências reais

- O banco recebeu o complemento autorizado; o novo código **não foi implantado**.
  É necessário deploy deste commit para disponibilizar formulários/segunda via e
  retirar a página antiga no ambiente publicado. Nenhum push foi executado.
- Persistem campos em branco/ilegíveis e ambiguidades descritos no guia. Completude
  do modelo não equivale a afirmar que o documento fornece todos os valores.
- Retenção, base institucional de tratamento, atendimento aos titulares, guarda
  dos impressos e publicação de pequenos grupos precisam de decisão/evidência
  institucional; não se presume homologação pelo resultado dos testes.
- Backup foi verificado por decifragem, sem ensaio integral de restauração do
  serviço. Agendamento/monitoramento de expurgo e retentativas, grants e operação
  de infraestrutura exigem comprovação própria.
- Remoção de beneficiários, associação de cadastro existente a outra ação,
  conciliação supervisionada entre fontes, filtros avançados e evolução relacional
  dos locais continuam evoluções pendentes. Edição/correção está implementada.
- CI remoto, revisão independente de segurança, tecnologias assistivas reais,
  impressão física e desempenho de campo não são comprovados pelo build/Axe local.

Essas pendências permanecem explícitas. A passagem dos testes comprova os
cenários executados e não garante ausência absoluta de falhas.
