# Profissionais, atribuições e campos clínicos — 11/11/2026

## Escopo e autorização

Continuação do cadastro administrativo entregue em `53be39e`, a partir dos
documentos do workspace. O responsável autorizou expressamente nesta solicitação
a inclusão dos campos clínicos. A implementação acrescenta cadastro de profissionais,
escala por ação/local e registro privado **em preenchimento** dos campos da ficha.
Não implementa conclusão de exame, receita, ficha impressa de laboratório ou etiqueta.

O login institucional existente, AC Auth, AC Core, o contrato Agenda 1.1 e o pipeline
Actions Map → Agenda → Plataforma → Portal foram preservados. Nenhuma migração em
banco real, importação, ativação clínica real, configuração de segredo, deploy ou
push foi executado. A alteração de formatação preexistente em
`PLANO_ACTIONS_MAP_GPT61_SOL.md` foi preservada e não pertence a esta entrega.

**Estado: código implementado e testado em ambientes sintéticos; liberação clínica
real permanece desligada e NÃO HOMOLOGADA.** A autorização para incluir campos
não equivale à validação de competências profissionais ou do fluxo clínico completo.

## Fonte original e matriz de campos

Fonte: `docs/references/FICHA MELHOR VISÃO PARA ANALISTA.xlsx`, uma aba `Planilha1`,
área `A1:X25`, 39 mesclas, uma imagem incorporada. O arquivo foi aberto novamente
para estrutura e hash; SHA-256 confirmado igual ao inspecionado anteriormente:
`74adf57b5d200d353dac5ae3626ce79a8b7c0a6a78cb8563c339785760f1f074`.
Conferência visual da área completa em `tmp/fase0/ficha-rotulos.png`, com os valores
preenchidos ocultos, e comparação com a
[matriz literal por célula](FASE_0_DESCOBERTA_2026-10-30.md#2-matriz-literal-de-campos).
Não há versão/data de aprovação visível no modelo. O original não foi alterado.

A imagem incorporada foi aberta/processada **localmente** e submetida a OCR com
allowlist de rótulos. Não foram recuperados rótulos clínicos permitidos nela; nenhum
pixel/texto privado foi enviado ao contexto. A cópia bruta temporária foi apagada.
A imagem não foi utilizada como fonte adicional de campos, unidades ou branding;
seu conteúdo literal continua pendente de conferência humana privada. O acervo
`docs/data/ilovepdf_merged.pdf` não foi reimportado nem usado para fabricar exames;
suas pendências históricas de leitura, inclusive página 34, permanecem documentadas.
Não se afirma nova revisão nominal integral das 50 fichas.

| Campos implementados | Origem literal na planilha | Tipo e validação técnica |
| --- | --- | --- |
| Glicose | A12, área B12:C12 | Texto opcional, até 80 caracteres |
| Pressão | D12:E12, área F12:I12 | Texto opcional, até 80; sem presumir tipo/unidade |
| Tipo de sangue | J12:K12, área L12:N12 | Texto opcional, até 32; sem resultado ou grupo presumido |
| OD: esférico, cilíndrico, eixo, DP | Cabeçalhos C15:F15; C16:F16 | Quatro textos opcionais, até 40 cada |
| OE: esférico, cilíndrico, eixo, DP | Cabeçalhos C15:F15; C17:F17 | Quatro textos opcionais, até 40 cada |
| Adição | H16; I16:N16 | Texto opcional, até 40 |
| Lentes | H17; I17:N17 | Texto opcional, até 160 |

São **13 campos clínicos**, preenchidos somente por profissional com autorização
específica e atribuição válidas. Todos são dados sensíveis de saúde, com finalidade
de registro fiel da ficha e destino exclusivo nas tabelas clínicas cifradas do Map.
Não entram no cadastro geral, comprovante geral, etiqueta, logs ou API de integração.
Obrigatoriedade clínica, unidades, convenções de sinal e faixas não foram fornecidas
pela fonte; por isso são transcrições textuais opcionais, sem cálculo, conversão,
interpretação, diagnóstico automático ou validação médica fictícia. Vazio vira
ausência (`null`), nunca zero. Os limites de texto são técnicos, não faixas médicas.

DP mantém o rótulo da fonte e não foi renomeado para DNP. O cabeçalho “OBSERVAÇÕES”
agrupa adição/lentes; não se inventou um campo livre de diagnóstico/observação clínica.
Não foram acrescentados acuidade visual, medicamentos, dose, sexo, RG ou outros campos
ausentes. Mãe/escolaridade são dados pessoais, não foram misturados aos campos de saúde.

Nome/título, número e autor de emenda/convênio continuam cadastrados uma vez na ação
por Administração/Tecnologia. O registro clínico herda automaticamente esses dados,
marcas e identidade profissional em um snapshot do primeiro salvamento. O profissional
não os redigita nem os altera no payload clínico. Edições posteriores da ação preservam
o contexto das versões já salvas.

## Profissionais e escala

- Tela `/profissionais`, acessível às duas equipes administrativas existentes:
  criar, buscar por nome, filtrar ativos/inativos, editar com CAS/409 e consultar
  histórico paginado. Sem remoção física, cópia de senhas ou criação de conta.
- Categorias distintas: médico, optometrista e recepção. Médico exige CRM/número/UF;
  RQE é opcional. CRM/RQE são recusados para as outras categorias. Registros não
  médicos não são tratados como CRM; recepção não recebe habilitação clínica.
  CNES não foi colocado no profissional, pois é identificador de estabelecimento.
- Conselho/número/UF precisam estar completos quando informados e são únicos como
  conjunto; nomes não são chave de identidade e não são mesclados automaticamente.
- Conferência da habilitação exige referência documental. A autorização para
  registrar campos clínicos é uma decisão **separada**, também com referência,
  desativada por padrão. Esses registros são declarações administrativas auditadas,
  não verificação automática de conselho ou parecer sobre competência legal.
- Divulgação de nome/CRM/UF exige opt-in, referência e profissional médico ativo
  com habilitação conferida. A autorização não ativa publicação: o item 1.1 da
  Agenda continua sem esses atributos.
- A página da ação permite atribuir profissional/recepção a todos os locais ou a
  um subconjunto de índices da versão atual da ação. IDs/versões de ação,
  profissional e atribuição são conferidos no servidor. Duplicatas e conflitos
  são recusados; registros de local/identificação ficam preservados em snapshots.
- Não se reordena/substitui local com atribuição específica ativa. Revogar permite
  revisar os locais; reativar exige submissão explícita com as versões atuais.
  Inativação, troca de identidade/categoria/registro/conferência/autorização clínica
  revogam as atribuições ativas na mesma transação. Arquivamento da ação também as
  revoga. Reativar o cadastro não reativa escalas automaticamente.
- Histórico de profissional e de atribuição é privado, paginado e apenas acrescentado.
  Auditoria operacional usa ator, operação e IDs, sem nomes ou conteúdo clínico no log.

## Identidade e autorização clínica

Não foi criado login local, SSO novo ou credencial para recepção/médico. O mecanismo
vigente ainda admite somente as identidades institucionais administrativas validadas.
Uma dessas pessoas pode vincular **sua própria identidade da sessão** ao seu cadastro
profissional; não pode indicar arbitrariamente a identidade de outro usuário.
O vínculo é único e opcional; cadastrar/escalar alguém não lhe concede acesso ao app.
Contas operacionais exclusivas continuam em standby. Direitos administrativos prévios
não são removidos nem concedidos pelo cadastro profissional.
Contas operacionais pendentes bloqueiam uso por esses perfis; ampliar seus privilégios
institucionais para contornar essa dependência não faz parte da implantação.

O backend exige cumulativamente, em cada leitura/salvamento clínico:

1. Sessão institucional vigente; CSRF/origem também na gravação.
2. Funcionalidade ativada e chave clínica válida, própria e diferente da chave geral.
3. Cadastro vinculado à identidade atual, ativo, médico/optometrista, com conferência
   de habilitação e autorização clínica específica registradas.
4. Ação disponível e atribuição ativa com papel profissional.
5. Participação da pessoa nessa ação e local compatível com o escopo. Local ausente
   não é presumido como local zero e não passa por atribuição de local específico.
6. Registro existente pertence ao mesmo profissional **e à mesma identidade autora**.
   Outro profissional na mesma ação não pode ler/sobrescrever a ficha. Reatribuir
   a identidade do mesmo cadastro profissional não transfere fichas anteriores.

Recepção, administrador sem vínculo clínico e token de integração não ganham leitura
clínica por possuir uma ação/ID. O backend é a barreira; ocultar o botão só acompanha
a decisão da API. A primeira gravação vincula o registro ao autor; não há transferência
de caso, acesso emergencial ou delegação implícita nesta etapa.

## Persistência, API e proteção

`0008_staff_assignments` acrescenta `acoes_map_profissionais`, `acoes_map_atribuicoes`
e `acoes_map_profissionais_historico`. `0009_clinical_fields` acrescenta
`acoes_map_fichas_clinicas` e `acoes_map_fichas_clinicas_versoes`, sem modificar campos
de pacientes ou as tabelas institucionais da Agenda.

Os campos clínicos e cada versão são cifrados com Fernet/`CLINICAL_KEY`. O envelope
autenticado confere ID da ficha, participação, profissional, identidade autora e
versão. Trocar ciphertext entre casos é recusado. Contexto institucional/profissional
é preservado separadamente; nenhum conteúdo de exame está em coluna de texto aberta.
A chave não aparece em resposta, frontend, banco ou repositório.

Grants do runtime: cadastro/atribuição/ficha admitem SELECT/INSERT/UPDATE; históricos
apenas SELECT/INSERT. DELETE/TRUNCATE e atualização dos históricos não são concedidos.
Migrações e provisionamento reaplicam a restrição após concessões gerais. A operação
produtiva ainda requer conferir grants/inheritance/owners reais; testes locais não
comprovam a configuração remota.

As gravações usam versões e locks em ordem consistente (ação → profissional →
atribuição → participação/ficha quando aplicável). Criação repetida de atribuição
ou ficha não duplica o vínculo. Gravar/revisar campos não altera a versão da ação,
não conta consulta/entrega e não enfileira qualquer dado clínico na outbox.

Principais rotas privadas, com contratos gerados em `docs/contracts/`:

- `/api/v1/profissionais`, `/{id}` e `/{id}/historico`.
- `/api/v1/acoes/{id}/atribuicoes`, `/{atribuicao}` e `/{atribuicao}/historico`.
- `GET /api/v1/acoes/{id}/acesso-clinico`: decisão booleana, sem conteúdo de paciente.
- `GET/PUT /api/v1/acoes/{id}/beneficiarios/{pessoa}/clinica`; GET com `versao=N`
  consulta uma versão anterior sob a mesma autorização. Toda resposta clínica é
  `no-store`; a consulta histórica é somente leitura na interface.

O navegador não persiste dados clínicos em localStorage/sessionStorage ou cache
offline. A consulta clínica usa `gcTime=0`, sem repetição automática, e o formulário
é desmontado ao fechar. A versão anterior nunca é alterada para salvar uma correção.

## Instalação controlada e reversão

Nenhum comando de aplicação abaixo foi executado contra o banco real nesta tarefa.
Antes de servir o novo código em PostgreSQL existente, preparar/aprovar a sequência
até **0009**, com backup consistente e chaves guardadas em canal separado.

SQLite local existente: `scripts/migrate_staff.py` e
`scripts/migrate_clinical_fields.py` fazem prévia por padrão; `--apply` cria as tabelas
faltantes após backup cifrado verificado. Exigem etapas anteriores 0007/0008,
respectivamente, rejeitam produção e caminhos de banco fora do workspace. Bancos
novos de desenvolvimento/teste recebem o modelo atual. Preparar tabelas não ativa
o registro clínico.

Configuração privada nova: `CLINICAL_FIELDS_ENABLED=false` por padrão e
`CLINICAL_KEY` vazia. Somente a equipe técnica deve fornecer a chave Fernet por seu
processo de segredos e ativar a flag após aprovação de ambiente, finalidade, matriz
clínica/competências e governança. O código recusa chave ausente/inválida ou igual
à chave geral. Nenhum segredo foi gerado/alterado no ambiente real nesta entrega.

Rollback: desligar a flag clínica, interromper novas entradas e preservar banco,
registros, versões e ambas as chaves. Não apagar tabelas nem executar downgrade
destrutivo; ele é recusado. Código anterior não serve como leitor clínico compatível.
Restore exige conciliação das gravações posteriores ao backup e autorização própria.

## Evidências e limites

Validação final: **184 testes backend aprovados** (139 anteriores + 45 novos),
**28 E2E aprovados**, lint, TypeScript, build, Ruff, `pip check` e teste em
PostgreSQL 18 temporário aprovados. O TestClient conserva o aviso de depreciação
httpx/Starlette já existente, sem falha. Os testes novos cobrem validação, escopo, CSRF/IDOR,
autoria, troca de identidade, revogação, cifra/versões, snapshot, ausência na API
geral/outbox e migrações/backup. O teste PostgreSQL aplica 0007/0008/0009 duas vezes,
exercita runtime e revogação concorrente, e recusa alteração dos históricos.
O novo E2E completo passou em desktop e celular, com verificação Axe do cadastro
profissional/formulário clínico, valores ausentes, histórico e bloqueio após revogação.
O caso de troca da identidade do mesmo cadastro também foi testado no backend:
o novo titular não herda as fichas da identidade autora anterior.

Privacidade do staging e dos caminhos rastreados: **PRIVACY_OK** em ambos os modos.
`git diff --cached --check` aprovado. A alteração de formatação preexistente no plano
permanece fora do staging; fontes, chaves, bancos e capturas não entraram no commit.

Capturas sintéticas em `artifacts/clinical-fields-{desktop,mobile}.png` revisadas:
campos OD/OE acessíveis e legíveis, responsividade e rolagem do modal. Isso não
homologa papel, etiqueta, leitor ou dispositivo real de campo. Os servidores próprios
de E2E foram encerrados explicitamente após os cenários para concluir o teardown no
sandbox Windows. Originais, bases, backups, chaves e capturas ficam fora do Git.

Continuam pendentes: identidade operacional exclusiva para recepção/profissionais,
topologia produtiva independente validada, políticas de retenção/restore e finalidade,
unidades/faixas/competências aprovadas para validação clínica, versão oficial da ficha
e conferências privadas restantes, triagem/fila/estados de atendimento, conclusão e
correção de exame finalizado, documentos físicos + etiqueta/entrega, reconciliação
de pessoas únicas e contrato 1.2 coordenado com as consumidoras. Não se declara o
MVP integral, prescrição legalmente assinada ou piloto clínico liberado.
