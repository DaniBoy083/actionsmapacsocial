# Implementação incremental do plano de 12/11/2026

**Atualização de 13/11:** a [etapa de acesso operacional](ACESSO_OPERACIONAL_2026-11-13.md)
implementou contas individuais, área da equipe e os escopos de AM-06 no código
e na demonstração. As referências abaixo à ausência desse login são o estado
histórico da entrega de 12/11; os demais gates não foram convertidos em homologações.

## Escopo e fontes

Solicitação: implementar a documentação anexada, auditar os princípios e preparar
commit local, sem push, deploy, migração produtiva ou importação definitiva.
Fonte nova: `AC_Actions_Map_Plano_Implementacao_2026-11-12(1).md`, confrontada com
`../AGENTS.md`, plano vinculante v2.1, README, branding e contratos de integração.
O banco real usa SQLAlchemy/Alembic, não Prisma. A autenticação disponível é
institucional e aceita somente Administração/Tecnologia. Não existe login
operacional específico validado nem integração AC Core ativa para substituir esse
controle. Não ampliar os tipos de identidade aceitos por suposição.

## Evidência de leitura anterior ao código

Em 12/11 foi aberto integralmente o ZIP/XML de
`docs/references/FICHA MELHOR VISÃO PARA ANALISTA.xlsx` e conferida visualmente a
renderização sanitizada `tmp/fase0/ficha-rotulos.png`. SHA-256 confirmado:
`74adf57b5d200d353dac5ae3626ce79a8b7c0a6a78cb8563c339785760f1f074`.
Uma aba `Planilha1`, área `A1:X25`, 39 mesclas, papel A4 paisagem,
sem versão/data de aprovação visível. Uma imagem incorporada não homologada como
marca permanece excluída do processamento. Valores preenchidos e assinaturas
não foram extraídos para prompts, fixtures, documentação ou Git.
O acervo preenchido de 50 páginas não é modelo de prescrição a publicar.

A matriz literal completa de origem, responsabilidade, validação, sensibilidade,
obrigatoriedade e destino está em
[Fase 0, seção 2](FASE_0_DESCOBERTA_2026-10-30.md#2-matriz-literal-de-campos).
Conferência desta execução:

| Seção e células | Campos confirmados | Responsável e tratamento |
| --- | --- | --- |
| A8:N9 | Nome, CPF, nascimento, nome da mãe, telefone, escolaridade | Recepção autorizada; pessoais; privados. Mãe não equivale a responsável. Necessidade de mãe/escolaridade permanece pendente. |
| A12:N12 | Glicose, pressão, tipo de sangue | Profissional habilitado; sensíveis, opcionais, cifrados; unidades e faixas não definidas na fonte. |
| A15:N17 | OD/OE: esférico, cilíndrico, eixo, DP; adição e lentes | Profissional designado; sensíveis, opcionais; conservar sinais/unidades informados, sem inventar medições. DP não é renomeado para DNP. |
| A20:N25 | Data, município, nome/registro/CPF profissional, declaração, carimbo e assinatura física | Identificação profissional distinta da pessoa atendida. Modelo final e fluxo físico exigem homologação; assinatura digital permanece em standby. |
| O1:X3 | Resumo nominal com rótulo literal “PESSÃO” | Não é analytics público e não pode sair para a Agenda/Portal. |

Nome/título, número textual e autor de emenda/convênio são metadados novos da
ação, cadastrados por Administração/Tecnologia, não campos do paciente. Mantêm
snapshot histórico e não são redigitados pela recepção. Logos oficiais continuam
optativas para terceiros; `public/logo-ac-social.png` é a marca fixa AC Social.

## Gates preservados

- Login operacional/AC Core: contratos reais e validação ausentes; permanece
  bloqueada a admissão de identidades operacionais novas. Negar acesso é seguro,
  mas não comprova o fluxo de recepção funcional.
- Emissão/conclusão de laudo, prescrição e etiqueta: modelo, competência e fluxo
  físico ainda não homologados. Não afirmar que registro em preenchimento é laudo.
- Logos externas: provedor, custo e licenciamento não aprovados. Implementar busca
  interna e upload com escolha explícita, sem fazer consulta externa automática.
- Integração: preservar contrato 1.1 e pipeline Actions Map → Agenda Digital →
  Plataforma Consolidada → Portal. Contrato novo exige aceite dos consumidores.
- Não declarar conformidade absoluta nem homologação clínica com base em testes.

## Resultado por requisito

| ID | Código entregue e limites |
| --- | --- |
| AM-01 | Busca interna por nome normalizado/aliases, resultados aproximados sinalizados, prévia e proveniência de upload, seleção de instituição separada de “Usar logo sugerida”, upload próprio disponível. Cache invalidado após salvar. Busca externa permanece bloqueada sem provedor autorizado. Não é um verificador de identidade oficial; homônimos exigem conferência humana. |
| AM-02 | Seção **Contratantes**, N blocos editáveis/removíveis, instituição reutilizável, papel próprio. |
| AM-03/04 | Seção única **Apoiadores**, N blocos, instituição/tipo e modalidade TOTAL/PARCIAL por vínculo. Ao criar ação, API e formulário exigem ao menos um de cada papel. Limite operacional de 100 por papel e corpo total de 1 MiB. Logos não são obrigatórias. |
| AM-05 | Rótulos **Oftalmologista**, **Optometrista**, **Recepcionista** e **Nome do profissional**. Identificador interno MEDICO preservado. CRM/UF para MEDICO; órgão/número/UF obrigatório para optometrista, sem conselho presumido. Habilitação e tipo de registro aceito exigem conferência institucional existente; recepção não recebe campos clínicos. |
| AM-06 | Designação explícita por participação, profissional e identidade antes da primeira leitura/gravação clínica. Escopo de ação/local, autorização específica, autoria e revogação conferidos em cada chamada. Backend institucional continua restrito aos perfis existentes; login de recepção/clínicos operacionais não é inventado. Logo, ainda não há operação desses perfis em piloto. |
| AM-07 | OD/OE estruturados e tipo de sangue opcionais já existentes na ficha foram preservados e testados após recarga. Criptografia clínica própria, versões e contexto histórico continuam ativos conforme a configuração já autorizada do ambiente. Sem unidades, diagnósticos ou valores inventados. |
| AM-08 | Autoria e histórico de registro em preenchimento preservados. Conclusão, prescrição/laudo, etiqueta e assinatura não foram liberados por falta de modelo/fluxo físico/competência homologados. Assinatura eletrônica e gov.br seguem em standby. |
| AM-09 | Baseline e correção do N+1 da lista de ações, paginação/contagem no SQL inclusive por município, agregação em lote e debounce de busca. Medição de carregamento completo, gravação e p95 produtivo ainda exige ambiente de homologação/infraestrutura. |

Os requisitos gerais de analytics clínicos, impressão física de ficha + etiqueta,
ranking público por emenda/autor, retenção institucional e integração 1.2 completa
continuam pendentes conforme os gates vinculantes. **Não há conformidade absoluta
nem liberação do MVP clínico inteiro.**

## Arquivos e contratos

- `backend/app/domain/institutional.py`, `domain/institutions.py`,
  `infrastructure/institutions.py` e `api/institutions.py`: validação, catálogo,
  busca e logos privados imutáveis.
- `backend/app/infrastructure/models.py`, `infrastructure/institutional.py` e
  `infrastructure/actions.py`: relações por papel/ordem e snapshots históricos.
  `api/action_filters.py` contempla múltiplos vínculos nos filtros internos.
- `backend/app/infrastructure/clinical.py`, `api/clinical.py` e
  `domain/clinical.py`: designação de caso versionada, CSRF e acesso atribuído.
- `src/features/actions/`, `src/features/clinical/designation-dialog.tsx`,
  `src/features/staff/` e BFF: formulários, busca, revisão, designação e rótulos.
  A segunda via administrativa inclui os vínculos e aguarda o carregamento de
  todas as logos antes de habilitar impressão; não se torna documento clínico.
- API interna **0.3.0**, prefixo real `/api/v1`; DTOs/OpenAPI regenerados em
  `docs/contracts/`, incluindo `institution-registration.schema.json` e
  `clinical-designation.schema.json`. Novas listas ficam em
  `institucional.contratantes` e `institucional.apoiadores`.
- Rotas reais: `GET/POST /api/v1/instituicoes`, imagem privada em
  `/api/v1/instituicoes/{id}/marcas/{logo_id}` e `GET/PUT`
  `/api/v1/acoes/{action_id}/beneficiarios/{person_id}/designacao-clinica`.
  A leitura/gravação clínica continua na rota `.../clinica` existente.
- Summary/exportação externa **1.1 inalterados**; nenhum nome de paciente,
  identificador de participação, conteúdo clínico ou imagem é incluído na outbox.

## Dados legados e migração

`0010_institutions_and_cases` adiciona quatro tabelas no schema `actions_map`,
FKs, constraints, índices e grants mínimos. O runtime não pode atualizar/apagar
instituições/logos imutáveis nem truncar as tabelas novas. O provisionamento
reaplica esses grants depois de concessões gerais.

Designações de fichas preexistentes vêm **somente** de seus autores já gravados,
incluindo a identidade original; isso não transfere casos quando um vínculo
institucional é trocado. Fichas sem habilitação/atribuição vigente continuam
inacessíveis. Participações ainda sem ficha exigem designação administrativa.

Marcas, apoio e metadados legados são mantidos integralmente. Não é possível
inferir contratante ou apoio individual a partir de um campo genérico de parceiro.
Por isso, nenhum vínculo fictício é criado no backfill: papéis históricos ficam
pendentes de revisão. Edições de clientes antigos que omitem as listas conservam
os vínculos existentes; listas explícitas vazias são rejeitadas. O formulário
novo orienta a revisão antes de salvar o legado sem papéis definidos. A mesma
instituição pode ter ambos os papéis; duplicidade no mesmo papel é rejeitada.

**Antes de servir o código novo**, o operador deve, mediante autorização própria:

1. Pausar gravações, confirmar revisão 0009 e preservar backup cifrado do banco
   e as chaves existentes por canal privado; restaurar/conferir em base descartável.
2. Ensaiar/aplicar a revisão 0010 pela conexão administrativa de migração já
   existente, conferir versão, contagens, vínculos, autoria e grants. Não trocar
   credenciais ou chaves. Só então disponibilizar a versão 0.3.0.
3. Em SQLite de desenvolvimento existente, usar
   `backend/.venv/Scripts/python.exe scripts/migrate_operational.py` para prévia e
   acrescentar `--apply` somente para aplicar. A aplicação gera/verifica backup
   cifrado antes de alterar a base. O script recusa produção/PostgreSQL e caminhos
   fora deste workspace. Não executado contra o banco local real nesta entrega.
4. Conferir designações/escopos com dados sintéticos e a segunda via em tela/papel.
   Não compartilhar credenciais administrativas para simular login de recepção.

## Testes e desempenho

- Baseline anterior: **184 testes de backend aprovados**.
- Verificação final: **200 testes de backend aprovados**. Incluem acesso negado,
  CSRF, caso não designado mesmo sem ficha, revogação imediata, autoria histórica,
  logos saneadas/privadas, mínimo de vínculos, reutilização e ausência de PII na
  integração, além de backup/restauração/idempotência em SQLite descartável.
- `scripts/check_institutional_postgres.py --bin <bin-local>` aprovado em
  PostgreSQL 18 **descartável**: revisões 0007–0010 repetíveis, CRUD/CAS, filtro
  territorial SQL, clínica cifrada, revogação concorrente e grants imutáveis.
  Nenhuma conexão produtiva foi usada.
- Build de produção, TypeScript e ESLint aprovados. Ruff aprovado nos 31 arquivos
  Python alterados/adicionados. A varredura global apontou 12 avisos de ordenação
  de imports em arquivos preexistentes fora da mudança, sem correção incidental.
- Os 30 cenários Playwright em desktop/celular passaram, incluindo acessibilidade,
  recarga, N vínculos, remoção sem perda, cache de busca, escolha/upload de logo,
  designação, versões, revogação e segunda via. Execução final fora do sandbox:
  **30 passed (2.7m), exit 0**, com encerramento dos servidores descartáveis.
- Revisão visual local das telas de instituições e clínica, em desktop/celular,
  e da segunda via com mídia de impressão: legíveis e sem perda de campos no
  layout inspecionado. Capturas sintéticas ficam em `artifacts/`, fora do Git.
  Não substitui teste com impressora e etiqueta reais.
- Gate de privacidade do staging aprovado: fontes privadas e bancos excluídos do
  Git, sem valores de segredos locais nas alterações; `git diff --cached --check`
  conferido antes do commit. O plano anexado foi incluído, normalizando apenas
  as quebras de linha Markdown do cabeçalho, sem mudar requisitos.

`scripts/benchmark_action_list.py` usa somente SQLite em memória, 500 ações
sintéticas, página de 20 e 20 amostras após aquecimento:

| Medida | Antes | Depois |
| --- | ---: | ---: |
| Consultas SQL por requisição | 61 | 4 |
| Mediana local (ms) | 21,39 | 2,02 |
| p95 local (ms) | 32,82 | 2,42 |

O teste não mede rede, Vercel/Neon nem tráfego clínico real. A paginação evita
carregar todas as ações e um teste protege o número constante de consultas.

## Reversão e próxima etapa

Não apagar tabelas nem históricos e não executar `alembic downgrade`; a revisão
recusa downgrade destrutivo. Preservar chaves e a designação explícita como
controle de segurança. Após gravar metadados com listas novas, **um simples retorno
ao backend anterior é incompatível** com seu DTO estrito: não o fazer às cegas.

Antes de novas gravações, uma reversão completa exige restaurar o backup
pré-migração validado em ambiente isolado e reconciliar contagens antes da troca.
Após novas gravações, preferir correção compatível mantendo a revisão 0010 e seus
dados; retorno à interface anterior só pode ocorrer mantendo a API que entende
as listas e conferindo os fluxos (clientes antigos não criam ações sem os novos
vínculos mínimos). Nunca sobrescrever históricos para fazê-los caber no DTO antigo.
A restauração SQLite a partir do backup cifrado foi comprovada em teste; restauração
produtiva depende do procedimento e aprovação do operador.

Próxima etapa operacional: homologar identidade/escopos reais de recepção e
profissionais, rever papéis das ações históricas, aprovar modelos e fluxo físico
de ficha/etiqueta e registrar baseline de latência em homologação. Homologação
clínica, impressora/etiquetadora física e consumidoras externas não podem ser
substituídas por testes automatizados locais.
