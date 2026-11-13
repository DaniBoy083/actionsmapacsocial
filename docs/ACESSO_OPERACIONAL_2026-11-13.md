# Acesso individual dos profissionais — 13/11/2026

## Diagnóstico e autorização desta etapa

O cadastro anterior mantinha profissionais, atribuições e designações clínicas,
mas não criava credenciais operacionais. O login aceitava exclusivamente as
identidades institucionais de Administração/Tecnologia. Portanto, cadastrar
recepção/oftalmologista/optometrista não permitia que essas pessoas entrassem.
O demo anterior também não demonstrava esses perfis. Isso era uma lacuna real,
documentada como pendente, e não um fluxo operacional implementado.

A solicitação atual autoriza implementar esse acesso básico e seus escopos,
antes em standby. Não autoriza deploy, migração produtiva, alteração de AC Auth/
AC Core, assinatura digital, recuperação pública de senha ou MFA. A execução
institucional permanece desligada por padrão até migração e liberação próprias;
o demo usa o mesmo código operacional com contas e dados exclusivamente fictícios.

## Fonte conferida antes de desenvolver

`docs/references/FICHA MELHOR VISÃO PARA ANALISTA.xlsx`: XLSX, `Planilha1`,
`A1:X25`, 41.860 bytes, SHA-256
`74adf57b5d200d353dac5ae3626ce79a8b7c0a6a78cb8563c339785760f1f074`.
Fonte lida nesta conversa, XML completo/mesclas/configuração e rótulos revistos
visualmente em prévia local sanitizada; valores preenchidos e imagem privada
não são fixtures. Sem versão clínica aprovada visível. A
[matriz literal por célula, finalidade, responsável, validação, obrigatoriedade,
sensibilidade e destino](FASE_0_DESCOBERTA_2026-10-30.md#2-matriz-literal-de-campos)
permanece a referência, sem inventar medidas, unidades ou campos:

| Origem | Responsável / destino |
| --- | --- |
| A8:N9, identificação | Recepção, dados gerais privados; campos existentes e ausência explícita |
| A12:N12 e A15:N17, saúde/OD/OE/adição/lentes | Clínico habilitado/autorizado, cifragem e versões privadas; não recepção |
| A20:N25, termo/profissional/registro/assinaturas | Fluxo físico e versão oficial ainda exigem homologação; não equiparar optometrista a médico |
| O2:X3, resumo nominal | Privado; não é analytics público |
| Nome/número/autor de emenda/convênio | Origem no cadastro administrativo da ação; leitura herdada, sem redigitação por paciente |

## Objetivo e arquivos previstos

Contas individuais vinculadas 1:1 ao cadastro profissional, com senha protegida,
sessão própria, gestão por Administração/Tecnologia com confirmação de senha,
revogação, área operacional e autorização backend por ação/local/caso.
Alterações em domínio/modelos, infraestrutura/API/security, migração aditiva,
BFF e telas; fixtures do demo, testes negativos e contratos/documentação.

Aceite: recepção cadastra/consulta somente a própria ação/local e não lê clínica;
oftalmo/opto veem somente casos designados e usam os campos existentes conforme
habilitação; nenhuma conta operacional acessa gestão, analytics, integrações ou
Agenda. Reset/inativação/revogação bloqueiam acesso. Não há migração produtiva.
O fluxo de ficha final/etiqueta e integrações externas não será declarado
implementado ou homologado por causa de um teste de login.

## Implementação e operação

API interna **0.4.0**. A exportação agregada continua no contrato **1.1**, sem
dados novos de pacientes, saúde ou contas operacionais.

```powershell
npm.cmd run demo -- --frontend-port 3000 --backend-port 8300
```

Equipe: `http://localhost:3000/acesso`. Administração/Tecnologia:
`http://localhost:3000/login`. Há link visível para a equipe na entrada do demo;
a tela da equipe oferece os três botões de preenchimento.

| Perfil fictício | Usuário | Escopo inicial |
| --- | --- | --- |
| Oftalmologista | `oftalmo.demo` | João Pessoa, local Centro, atendimento DEMO 02 |
| Optometrista | `opto.demo` | Mesma ação, local Bairro, atendimento DEMO 03 |
| Recepção | `recepcao.demo` | Mesma ação, local Centro; cadastros DEMO 02/04 e encaminhamentos |

Senha exclusiva dos exemplos: `Demonstracao-local-2026!`. Identificadores,
habilitações e registros profissionais são simulações descartáveis. Os acessos
`admin@demo.invalid`/`tecnologia@demo.invalid` continuam administrativos; não
ganham um cadastro clínico fictício para simular a função de médico. Reiniciar
restaura dados, contas, sessões e IDs. Nunca cadastrar pessoas reais no demo.

Roteiro: recepção escolhe sua ação, cadastra no local permitido e encaminha ao
profissional elegível; oftalmo/opto entram com suas próprias contas, abrem a fila
e preenchem somente o caso designado. O formulário clínico existente conserva
OD/OE, sangue e os demais campos da fonte, opcionais, cifrados e versionados.
Continua em preenchimento, sem emissão de laudo/prescrição assinada. A segunda
via disponível é a do cadastro geral, identificada como demonstração.

### Gestão individual

Administração/Tecnologia: cadastrar o profissional; registrar habilitação e
autorização clínica específica, quando aplicáveis; em Profissionais → **Acesso**,
definir usuário e senha inicial de pelo menos 12 caracteres, confirmando a própria
senha institucional. A mesma tela redefine senha ou desativa acesso. Não há
senha padrão fora do demo, autocadastro ou recuperação pública de senha.

Conta, cadastro profissional e atribuição são recursos distintos. Criar conta
não atribui ação/caso: vincular profissional à ação/locais e encaminhar cada caso.
Optometrista conserva categoria/registro próprios, sem CRM automático nem
equiparação a médico. Cadastro com vínculo institucional anterior não recebe
conta local sobreposta: revisar a origem preservando a autoria existente.

### Permissões verificadas no servidor

| Operação | Recepção | Oftalmo/opto | Administração/Tecnologia |
| --- | --- | --- | --- |
| Ver ações | Somente atribuídas e ativas | Somente atribuídas e ativas | Gestão institucional existente |
| Consultar cadastros | Locais atribuídos | Casos designados e local permitido | Gestão privada existente |
| Cadastrar/corrigir identificação | Próprio local | Não | Fluxo administrativo existente |
| Encaminhar/revogar designação | Próprio local, profissional elegível | Não | Gestão existente |
| Ler/editar clínica e versões | Não | Habilitação + autorização + ação/local + designação + autoria | Ser Admin/Tech não basta; compatibilidade legada exige vínculo clínico individual válido |
| Editar ação/parceiros/marcas | Não | Não | Sim |
| Dashboard/imports/catálogo completo | Não | Não | Sim |
| Tokens/diagnóstico/sincronização | Não | Não | Só Tecnologia |
| Outras aplicações AC | Nenhum mecanismo concedido | Nenhum mecanismo concedido | Identidade institucional preservada |

Rotas da equipe: `/api/v1/operacao/...`, com allowlist própria no BFF. Rotas
institucionais mantêm sua autenticação. Trocar menu, ID ou cookie não concede
permissão. Pacientes são listados com paginação e campos mínimos, sem CPF,
contato ou clínica. Marcas privadas também exigem ação e vínculo apropriados;
operadores não recebem acesso ao catálogo geral. Emenda/convênio são herdados
em leitura; contexto clínico é preservado por versão, sem redigitação pessoal.

### Segurança e persistência

- Tabelas `acoes_map_contas_operacionais` e `acoes_map_sessoes_operacionais`,
  exclusivas do Actions Map. Não copiam senhas AC ou pacientes para a Agenda.
- Salt aleatório e scrypt; sessão opaca de oito horas, somente hash no banco.
  Origem `LOCAL`, sujeito `actions-local:<UUID>` e papel derivados do cadastro.
- Cookie HttpOnly/SameSite Strict, Secure em produção: `ac_actions_operational`,
  ou `ac_actions_demo_operational` no demo; distinto do administrativo. Origem,
  CSRF, limites de tentativas e revalidação por requisição continuam ativos.
- Alteração/reset da conta elimina sessões. Inativação/alteração de habilitação
  revoga sessões e atribuições. Reativar não restaura vínculos automaticamente.
  Escopo revalida a versão da conta antes de operar, inclusive quando um reset
  venceu uma requisição já autenticada. Locks: ação → profissional → conta → atribuição.
- Cadastro da recepção usa UUID de idempotência por operação, encaminhado pelo
  BFF. Reenvio idêntico não cria outra participação/outbox; conteúdo diferente
  com a mesma chave é recusado. Não há deduplicação automática por nome.
- Auditoria contém IDs/origem/operação, sem senhas ou valores clínicos. A ficha
  mantém cifragem clínica segregada e não é enviada à recepção ou à integração.
  O novo fluxo aciona a outbox, contendo só o agregado 1.1 já contratado.
- Grants PostgreSQL limitam UPDATE às colunas administrativas da conta; runtime
  não altera ID/proprietário nem apaga contas. Sessões permitem SELECT/INSERT/
  DELETE. Regra reaplicável após defaults de provisionamento legados permissivos.

## Migração, liberação e reversão

`OPERATIONAL_ACCESS_ENABLED=false` é o padrão; o demo habilita somente no próprio
processo/banco descartável. Nenhuma configuração, tabela, credencial ou registro
produtivo foi alterado. A migração aditiva **0011_operational_accounts** depende
de 0010; não reescreve pacientes, identidade AC, atribuições ou fichas. Contas
reais não são criadas automaticamente para profissionais existentes.

Antes da ativação real: preservar backup cifrado e chaves, provar restauração
isolada, ensaiar/aplicar 0011 pela conexão administrativa, conferir grants, criar
contas individuais e validar habilitação/atribuição/designação. Só então liberar
a flag no ambiente aprovado. Com flag desligada, a linha de código conserva os
fluxos institucionais existentes. SQLite novo recebe as tabelas pelos modelos;
uma base local existente exige backup controlado antes de iniciar a nova versão.

Homologar origem/CSRF e orçamento de tentativas atrás do BFF: o limite herdado
por endereço pode representar vários operadores sob o mesmo upstream. Não confiar
em `X-Forwarded-For` do navegador nem ampliar limites sem contrato de proxy e
ensaio de carga. Teste local não certifica audiência nas outras aplicações AC.

Rollback: desligar a flag e encerrar sessões por procedimento administrativo;
preservar contas e autoria. Downgrade recusa exclusão destrutiva. Reversão de
código precisa manter compatibilidade com 0010 e registros de origem LOCAL;
não transferi-los para outra identidade para caber no login antigo. Interromper
a operação local até retomar versão compatível; não apagar tabelas ou trocar chaves.

## Conferência de todo o planejamento vinculante

Comparados AGENTS.md, plano v2.1/adendo de 30/10, plano consolidado de 12/11
(AM-01–AM-09), contratos e implementação reais. Histórico não prevalece sobre
as decisões vinculantes. Código testado é distinto de homologação real:

| Item planejado | Implementação comprovada | Lacuna ou limite |
| --- | --- | --- |
| Fase 0: fonte/campos/permissões | XLSX, matriz literal e descoberta de código/schema/rotas documentados | Modelo oficial/verso e interpretações dependem do responsável clínico |
| Identificação integral da fonte | Nome/CPF/nascimento/telefone e dados gerais do legado | Nome da mãe e escolaridade ainda não incorporados ao cadastro; exigem finalidade/necessidade e regras aprovadas. Responsável não foi tratado como sinônimo de mãe |
| Ações/período/categoria/resumo/IBGE/N locais | CRUD, versão/CAS, arquivo lógico, busca/filtros/paginação SQL | Implementado/testado; homologação operacional separada |
| AM-01: instituição/logo | Catálogo interno, aliases, prévia/proveniência, escolha explícita e upload | Fonte externa não implementada sem provedor autorizado; não inventar logo oficial |
| AM-02–04: N contratantes/apoiadores/modalidade | Blocos repetíveis, catálogo reutilizável e validações | Implementado/testado; papéis de legados exigem revisão |
| Três marcas e emenda/convênio | AC oficial, governo/clínica opcionais em TOTAL/PARCIAL; autorizações e nome/número/autor herdados/versionados | Ficha clínica final e etiqueta ainda precisam desses artefatos |
| AM-05: profissional e registro | Categorias/registro/CRM correto, habilitação/autorização e histórico | Implementado; competências reais não são provadas por fixtures |
| AM-06: acesso restrito | Conta individual, área própria, backend por ação/local/caso, reset/revogação e sessão separada | Implementado/testado nesta entrega; ativação real ainda exige migração e homologação |
| AM-07: campos clínicos | OD/OE/sangue e demais campos existentes, opcionais, cifrados/versionados, autoria/contexto | Estado em preenchimento; unidades/finalidade/fluxo final não foram presumidos |
| AM-08: conclusão/laudo/documentos | Registro com autoria; cadastro geral e segunda via A4 | Conclusão clínica, ficha final para laboratório, etiqueta, impressão conjunta e eventos próprios de entrega/reimpressão **não implementados/homologados** |
| Assinatura/gov.br | Não introduzidos | Continuam em standby; validar fluxo físico do MVP |
| AM-09: desempenho | SQL sem N+1, paginação/agregação e consultas por IDs | p95 de fluxo completo e carga de múltiplos operadores no ambiente real pendentes |
| Importação histórica | Revisão/ownership/fonte cifrada, origem idempotente e cadastro geral | Conciliação entre fontes e ilegíveis pendentes; nenhum lote real novo |
| Analytics completo | Admin/Tech, filtros institucionais/período/território, participações e cadastros distintos com denominadores | Pessoas reconciliadas entre ações, ficha/etiqueta/entrega/reimpressão e indicadores clínicos aprovados pendentes |
| Pipeline exato | Map → Agenda → Plataforma → Portal, item 1.1 minimizado, outbox/ACK/tokens | Novo contrato de metadados, consumidor de ações na Plataforma, mapa/ranking sem duplicação e E2E real das quatro aplicações pendentes |
| Identidade institucional/AC Core | Login existente preservado; LOCAL não replica credenciais AC | Integração futura AC Core não está ativa; não foi substituída por endpoint presumido |
| LGPD/retenção/backup | Minimização, cifragem, autorização, auditoria, contratos e testes sintéticos de restauração | Bases legais, prazos/avisos/retenção, aprovação profissional e recuperação produtiva exigem responsáveis |

**Conclusão: não estava tudo implementado e ainda não há conformidade global
absoluta.** A lacuna de acesso/atuação da equipe foi corrigida no código e no
demo. Linhas pendentes não se tornam prontas por estarem planejadas. A próxima
fase clínica/documental depende de modelo/fluxo físico aprovados; evolução
pública depende das consumidoras e finalidade/publicação aprovadas. Não houve
deploy ou migração produtiva.

## Verificações

Resultados observados nesta execução. Capturas e relatórios contêm somente
exemplos sintéticos e ficam fora do Git.

- **215 testes de backend aprovados**, com oito cenários novos de autorização
  operacional: escopos, negações, cadastro idempotente/outbox sem PII, senhas
  protegidas, CSRF/origem/rate limit, revogação/reset, reativação sem atribuição
  implícita e reset vencendo uma requisição previamente autenticada. Após ajustar
  o acionamento da outbox no novo prefixo, os oito cenários foram repetidos e
  aprovados. Os testes do demo conferem hashes dos arquivos de ambiente e banco
  operacional existentes antes/depois da execução descartável.
- **PostgreSQL 18 local descartável aprovado:** revisões 0007–0011 executadas e
  repetidas por Alembic, CRUD/CAS e clínica cifrada existentes, criação/reset de
  conta no papel runtime e negações de DELETE/alteração do proprietário da conta
  e UPDATE das sessões. Não utilizou banco ou credencial produtivos.
- Build Next, TypeScript, ESLint, Ruff nos arquivos Python alterados e `pip check`
  aprovados. OpenAPI 0.4.0 e schemas de entrada/saída de contas regenerados sem
  consulta ao banco. O contrato de integração 1.1 não foi ampliado.
- **30 cenários E2E institucionais aprovados**, desktop/celular, saída 0;
  **10 cenários do demo aprovados**, saída 0, cobrindo os três perfis, gestão de
  acesso, persistência dos campos clínicos, cadastro/encaminhamento, negações e
  segunda via. Após o ajuste final de contraste também passaram os quatro
  cenários de acessibilidade/formulários afetados, sem desativar regras Axe.
  Verificação de largura da página operacional aprovada em desktop e celular.
  Capturas sintéticas do cabeçalho/recepção e formulário clínico foram revisadas;
  segunda via do demo continua em uma página A4, sem teste físico de impressora.
- As primeiras execuções de navegador identificaram seletores de labels
  obrigatórios, notificação com contraste transitório e falta de sincronização
  no fechamento da seleção de modalidade em teste mobile. Seletores passaram a
  usar os nomes acessíveis; notificações têm cor/contraste constantes sem fade;
  o helper verifica seleção por teclado e fechamento do menu. Regras Axe não
  foram desativadas. O layout da equipe usa marca de tamanho fixo e tabela com
  rolagem interna no celular, preservando nomes e ações legíveis.

Comandos: `npm.cmd run test:backend`, `npm.cmd run test:e2e`, `npm.cmd run test:demo`,
`npm.cmd run build`, `npm.cmd run typecheck`, `npm.cmd run lint`;
`backend/.venv/Scripts/python.exe scripts/check_institutional_postgres.py --bin "C:/Program Files/PostgreSQL/18/bin"`
cria exclusivamente um PostgreSQL de teste em pasta temporária própria. Os
testes com subprocessos foram executados fora do sandbox Windows quando necessário
ao encerramento normal. Avisos herdados de depreciação Starlette/httpx e
`NO_COLOR`/`FORCE_COLOR` não foram ocultados por mudança de dependências.

A revisão final também corrigiu o seletor administrativo de designação, que
antes aceitava apenas vínculo institucional. A resposta de atribuições informa
se existe conta operacional ativa, calculada em lote; a seleção aceita a origem
apropriada e o backend continua conferindo local/habilitação/autoria. Os dois
cenários de gestão/designação administrativa passaram em desktop/celular após
esse ajuste, assim como os 39 testes de backend afetados (profissionais/acessos).
