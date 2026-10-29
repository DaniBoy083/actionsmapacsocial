# AC Actions Map — Especificação otimizada para agente de desenvolvimento

**Versão:** 2.0 (29/10/2026)  
**Estado:** PLANEJAMENTO / AGUARDANDO FICHA CLÍNICA E ALINHAMENTOS  
**Modelo previsto:** GPT-6.1 Sol no Codex, Work ou agente de IDE compatível  
**Destino no repositório:** `docs/PLANO_ACTIONS_MAP_GPT61_SOL.md`  
**Documento de entrada do agente:** `AGENTS.md` na raiz

> **REGRA DE EXECUÇÃO:** este documento define a futura implementação, mas não a autoriza. Primeiro examinar o código e os documentos reais e produzir um inventário. Não implementar com base em campos presumidos de ficha ainda não anexada. Implementar em fases, cada uma após autorização, com testes, evidências e rollback.

## 0. Como usar com economia de tokens

**Estratégia de contexto em duas camadas.** `AGENTS.md` contém regras permanentes curtas; este documento é lido **somente na seção da fase solicitada** e nas seções transversais necessárias. Os MDs históricos são fontes de consulta, não prompts para serem concatenados repetidamente. Inventariar os PDFs e ler os relevantes quando for modelar/importar dados; não enviar o texto integral dos PDFs para o contexto sem necessidade.

**Prompt inicial recomendado (copiar no agente):**

> Leia `AGENTS.md` e `docs/PLANO_ACTIONS_MAP_GPT61_SOL.md`, principalmente as seções 1, 2 e Fase 0. Sua tarefa **agora é somente diagnóstico e planejamento detalhado**: inventarie arquivos e esquema reais, identifique conflitos com os MDs históricos e a ficha clínica, produza a matriz de campos/permissões e um backlog priorizado. Não escreva código, não aplique migrações, não acesse produção e não invente campos. Liste dúvidas bloqueantes objetivas. Depois aguarde autorização para cada fase.

**Em cada fase posterior:** “Execute **somente a Fase N** do plano. Leia apenas os arquivos afetados, implemente o menor conjunto coerente, rode testes aplicáveis e reporte diff/testes/bloqueios; não avance para outra fase.”

**Diretrizes ao GPT-6.1 Sol:** usar esforço `medium` para descoberta focalizada e tarefas delimitadas; aumentar para `high` ou superior em arquitetura de identidade, banco, permissões, contrato de integração, migração clínica ou assinatura quando disponível. Maior esforço **não garante menor custo**: medir qualidade, tool calls e retrabalho. Usar respostas concisas, saída incremental, diffs em vez de arquivos completos e contratos tipados. Não usar “leia tudo novamente” em cada prompt.

## 1. Fontes, precedência e conflitos resolvidos

**Referências já localizadas na Biblioteca do ChatGPT (anexar ao workspace/repo se ainda não estiverem lá):**

1. `AC_ACTIONS_MAP_DOCUMENTACAO_AGENT.md` — arquitetura, login institucional, locais N:N, importação, dashboard, área técnica e padrões de stack.
2. `PLANEJAMENTO_ACTIONS_MAP_BENEFICIARIOS.md` — vínculo beneficiário/ação, segundo modal, comprovante/segunda via, importação histórica, LGPD e idempotência.
3. `plano_integracao_mapa_acoes_portal_institucional.md` — contrato de leitura da Plataforma Consolidada, mapa do Portal, cache, normalização e testes.
4. `PLANEJAMENTO_AC_ACTIONS_FRAMEWORK_AC_SOCIAL.md` — histórico arquitetural geral; usar apenas partes compatíveis com a decisão atual.
5. **Fonte definitiva para campos clínicos: ficha de atendimento ocular AINDA A SER ANEXADA** ao workspace e explicada pelo responsável. Não supor seu layout.

**Ordem de prioridade:** requisitos explícitos acordados em 29/10/2026 > ficha clínica aprovada quanto aos campos > contratos/esquema reais e legislação aplicável > MDs antigos como legado de funcionalidades. As decisões atuais **substituem** duas premissas antigas: (a) Actions Map genérico, sem dados clínicos; (b) login exclusivamente institucional/único domínio de banco. A proposta anterior de compartilhar `usuario_id` dos pacientes e a ideia de não criar contas locais **não se aplicam** ao fluxo atual.

**Não apagar PDFs ou registros legados.** Construir uma matriz de conflitos `origem → decisão atual → impacto → migração` antes de codificar.

## 2. Decisões de arquitetura inegociáveis

### 2.1 Domínios e fluxo

```text
AC Actions Map (banco próprio, contas locais + acesso global autorizado)
    ├─ ações/localidades/parceiros
    ├─ pacientes/triagem/ficha clínica/documentos assinados
    ├─ dashboards internos (somente Administração/Tecnologia)
    └─ API de exportação: indicadores agregados + profissionais/parceiros públicos aprovados
                   │
                   ▼
             Agenda Digital (banco e login institucional próprios)
                   │
                   ▼
       Plataforma Consolidada de Análise de Dados
                   │ API pública read-only, saneada
                   ▼
           Portal Institucional (Mapa de Ações)
```

- Cada serviço preserva a sua responsabilidade. Não inserir fichas, pacientes, contas locais nem prescrições no banco da Agenda ou da Plataforma.
- Se o ambiente atual usar o mesmo cluster/instância Neon, **confirmar como realizar bancos lógicos separados e credenciais restritas**; a exigência é independência de dados e autenticação, não simplesmente criar tabelas com prefixos no banco da Agenda. Não duplicar infraestrutura sem avaliar custo/risco e obter aprovação.
- APIs entre serviços autenticadas, contratos versionados, dados minimizados, entrega idempotente, retries, auditoria e observabilidade.
- Portal recebe apenas dados públicos revisados e não passa a administrar Actions Map.

### 2.2 Autenticação — duas tabelas e isolamento real

| Origem | Persistência | Quem usa | Direito de acesso |
|---|---|---|---|
| **Global AC Social** | Tabela existente de autenticação institucional, pertencente ao sistema AC | Membros ativos das equipes **Administração** e **Tecnologia**, com tipo de login autorizado | Actions Map e outras aplicações **somente segundo as permissões institucionais já existentes**. O Actions Map apenas consulta/verifica essa identidade por integração autorizada, sem replicar senhas. |
| **Local Actions Map** | **Nova tabela própria no banco do Actions Map**, distinta da global | Médicos e recepcionistas cadastrados para ações | **Exclusivamente Actions Map**, conforme papel e ações atribuídas. Zero credenciais/escopos/sessões reutilizáveis nas outras aplicações AC. |

**Obrigatório:** `auth_source` explícito (`GLOBAL` ou `LOCAL`), roles/claims e audiência da sessão específicas, expiração, revogação, validação no backend, separação de namespaces/cookies/tokens, rate limiting, recuperação de conta controlada, hash de senha moderno para locais, MFA para contas privilegiadas conforme política aprovada, registro mínimo de auditoria. Preferir login institucional via mecanismo existente de verificação confiável; não consultar diretamente hash global nem armazená-lo na base local. Proteger contra mesmo login/e-mail em origens diferentes, confusão de sessão, IDOR e escalada de privilégios.

**Experiência local:** exibir somente marca e páginas do Actions Map; jamais apresentar link, sidebar, URL de navegação, descrição interna ou atalho da Agenda, de outros frameworks, de analytics ou da tela técnica. Segurança real exige que **as outras aplicações recusem o token local por issuer/audience/escopo**, inclusive em chamadas diretas. Esconder links não substitui autenticação/autorização.

**Login e rotas exatos** serão definidos após inspeção do repositório; uma separação possível é tela de acesso local própria e entrada institucional não divulgada a operadores locais. **A existência de dois fluxos não deve obrigar o profissional local a escolher ou conhecer a origem institucional.**

### 2.3 Matriz mínima de permissões

Legenda: `A` acesso; `R` leitura restrita; `—` proibido. Autorizações verificadas no servidor, por ação atribuída, por recurso e por status.

| Recurso/ação | Admin global | Tecnologia global | Médico local | Recepcionista local |
|---|:---:|:---:|:---:|:---:|
| Cadastro/edição/arquivamento de ação, locais, parcerias | A | A | — | — |
| Cadastro/ativação de profissionais locais e suas atribuições | A | A | — | — |
| Ver ações e pacientes **atribuídos** para executar função | A* | A* | R | R |
| Cadastrar/corrigir dados pessoais de triagem | A* | A* | R | A (na ação designada) |
| Preencher/alterar ficha clínica, antes de assinar | A* | A* | A (somente competência autorizada) | — |
| Assinar prescrição/documento médico | — | — | A (somente médico habilitado) | — |
| Imprimir/registrar entrega de documento assinado | A* | A* | A | R (conforme fluxo aprovado) |
| Análises de dados, incluindo indicadores de saúde | A | A | — | — |
| Importar PDFs históricos e administrar correções | A** | A** | — | — |
| Conexões, tokens, monitoramento, rotas técnicas | — | A | — | — |
| Acesso por conta local a **qualquer outra aplicação AC** | — | — | — | — |

`*` Acesso administrativo/tecnológico a **telas** não implica consulta clínica irrestrita: leitura de dados sensíveis apenas quando necessária, com motivo/permissão específica e auditoria; Tecnologia prioriza metadados técnicos e dados sintéticos. `**` Importação definitiva requer aprovação e registro de quem autorizou. Revisar matriz com responsáveis clínicos e institucionais antes de liberar.

**Testes negativos essenciais:** recepcionista vê apenas triagem dos casos da própria ação; médico não acessa casos de outro médico/ação sem atribuição; ambos recebem 403 em `/analytics`, `/tecnologia` e qualquer endpoint protegido; Admin recebe 403 na área técnica; token local é rejeitado pelas APIs AC externas; nenhum vazamento por busca, autocomplete, export, ID previsível ou cache.

## 3. Experiência do produto (macrofluxo)

### 3.1 Gestão de ações (Administração/Tecnologia)
- Preservar o formulário existente: **nome, período inicial/final, categoria se aplicável, descrição interna, resumo público opcional, município e N locais**; municípios por **código IBGE** (PB = 25), vários locais por ação e município, validação de duplicatas e status.
- Tabela de ações com busca, filtros por município/período/status/categoria, paginação, visualizar, editar, arquivar logicamente, trilha de mudanças.
- Gestão de parceiros/apoio: `apoio = TOTAL | PARCIAL` (validar significado operacional). Em **PARCIAL**, adicionar 1..N **clínicas, médicos e/ou instituições** com nome, categoria, contribuição, logotipo, vínculo à ação e autorização de uso de marca/publicação. Não presumir que apoio total proíbe parceiro; decisão pendente.
- Indicadores de ações: agendadas, concluídas, municípios, locais, número de pacientes únicos, atendimentos e documentos emitidos (contagem diferenciada).
- Possibilidade de marcar médico como **“Exibir como médico parceiro no Portal”**, padrão desativado; registrar autorização, data/versão e revogação. Expor **nome e CRM/UF**, se aprovados; **CNES refere-se ao estabelecimento**, não é número de conselho pessoal do médico. Validar vínculo e necessidade de exibição de CNES na entidade clínica.
- Valores de apoio/convênios e informações financeiras, se existirem, ficam restritos e exigem definição de campos, governança e divulgação. Não vincular dados clínicos a apoiadores, parceiros, parlamentares ou campanhas.

### 3.2 Profissionais locais (Administração/Tecnologia)
- Cadastro completo, porém **minimizado por finalidade**, de médico/oftalmologista, demais profissionais permitidos e recepcionista. Dados pessoais, contatos, atribuição funcional, cargo/papel, situação ativo/inativo, municípios/ações designadas e credenciais locais em entidade separada.
- Para médico: nome profissional, CRM/UF, eventual RQE quando pertinente, verificação de habilitação e certificado/identidade de assinatura; vínculo a clínica/estabelecimento e **CNES da clínica**, quando aplicável.
- **Optometrista não é sinônimo de médico**: só habilitar registros e atos clínicos dentro das atribuições efetivamente permitidas após validação jurídica/regulatória. Prescrição médica e assinatura médica são exclusivas de profissional habilitado.
- Separar `profissional` de `conta_local` e de `atribuicao_acao` para permitir um profissional em múltiplas ações sem múltiplos logins. Desativação cancela sessões e atribuições futuras; preservar histórico.

### 3.3 Atendimento em duas etapas

```text
Admin cria ação/locais e designa profissionais
  → Recepcionista local escolhe SUA ação autorizada
  → Localiza ou cadastra paciente (modal secundário)
  → Preenche somente campos de IDENTIFICAÇÃO/TRIAGEM da ficha real
  → Salva atendimento com estado TRIAGEM_CONCLUIDA
  → Médico habilitado visualiza ficha pré-preenchida na SUA fila
  → Preenche campos CLÍNICOS conforme ficha aprovada
  → Valida/fecha avaliação
  → Gera PDF de prescrição/solicitação de óculos conforme modelo aprovado
  → Assina digitalmente (assinatura qualificada adequada)
  → Documento imutável e verificável
  → Entrega e registro de recebimento do paciente (papel ou digital)
  → Segunda via/impressão sem criar novo atendimento
```

- Usar paciente separado de atendimento; um paciente pode comparecer a várias ações, com registros separados e chave idempotente de evento. Deduplicação cuidadosa, nunca unificar só por nome.
- Estados sugeridos (ajustar à operação real): `EM_TRIAGEM`, `AGUARDANDO_MEDICO`, `EM_ATENDIMENTO`, `AGUARDANDO_ASSINATURA`, `ASSINADO`, `ENTREGUE`, `CANCELADO` e `PENDENTE_REVISAO`. Transições validadas no backend; alterações assinadas demandam nova versão e nova assinatura.
- Campos pessoais e clínicos em entidades **separadas**, controles diferentes por papel, mascaramento nas listagens, trilha de leitura/edição e prazo de retenção. Não fazer consultas clínicas a partir da Agenda.
- A futura **ficha real é a fonte dos campos**, com matriz `campo → finalidade → titular → tipo (pessoal/sensível) → responsável por preenchimento → obrigatório? → validação → persistência → visibilidade → retenção`. Não inventar CPF, sangue ou dados oftálmicos obrigatórios sem conferência.

### 3.4 Documentos, assinaturas e comprovantes
- **Documento médico eletrônico:** assinatura do médico habilitado com mecanismo **qualificado/ICP-Brasil**, conforme enquadramento regulatório que deve ser validado antes da implementação; assinatura visível em PDF não equivale a assinatura criptográfica verificável. Preferir PDF assinado PAdES ou formato aceito pelo validador escolhido; preservar hash, versão, evidências e cadeia de verificação.
- Integração com **gov.br não é pressuposta nem condição de implementação**: verificar elegibilidade da API, tipo de assinatura efetivamente produzido e aderência às regras de documentos médicos. Não prometer integração automática sem viabilidade demonstrada.
- **Paciente:** comprovante de recebimento em papel ou assinatura/captura digital na própria aplicação, com forma, horário, vínculo ao documento e armazenamento restrito. **Não tratar assinatura do paciente como aprovação do conteúdo clínico.**
- Armazenar documento assinado em storage privado com controle de acesso; nunca em `/public`. Emissão e reemissão registradas; **2ª via conserva o mesmo atendimento/documento e não invalida assinatura digital**, nem aumenta contagens. Não editar bytes do PDF já assinado para inserir marca de segunda via: exibir informação separada ou gerar cópia verificável sem quebrar assinatura.
- Comprovante operacional histórico de participação (MD antigo) é **diferente** de prescrição médica; migrar a funcionalidade anterior como tipo de documento distinto. QR Code/verificação pública, se adotados, exibem apenas status e mínimo indispensável, sem PII.

## 4. Segurança e tratamento de dados

- **Dados pessoais comuns:** nome, contato, telefone, identificadores e endereço/município ligados a pessoa identificável; acesso apenas pela finalidade e papel.
- **Dados sensíveis:** dados de saúde, histórico clínico, achados, graus, prescrição, exames e **tipo sanguíneo** quando vinculado à pessoa; segurança e base legal do art. 11 LGPD, segregação lógica/física apropriada, criptografia em trânsito e repouso, controle de acesso, auditabilidade e gestão de retenção.
- Coletar **tipo sanguíneo somente se estiver na ficha aprovada e houver justificativa clínica/operacional**. Se usado, analytics interno pode mostrar por grupo ABO/Rh e “não informado” **sem valores inventados**; pequenos grupos tratados contra reidentificação e nenhum detalhe individual em exportações.
- Definir com controlador responsável hipóteses legais adequadas, aviso de privacidade, retenção e exclusão/correção, menores de idade e acesso emergencial. **Consentimento de imagem é finalidade separada** de registro clínico e de autorização de divulgação de profissional/logo.
- Auditoria com ator `GLOBAL/LOCAL`, papel, ação, tipo de operação, data e ID de recurso; sem conteúdo de ficha, PII ou tokens em logs. Proteção contra IDOR/BOLA, CSRF aplicável, XSS, SQLi, abuso de endpoint, vazamento por paginação e snapshots.
- Dados de teste sintéticos. Não mover os PDFs históricos com PII para Git, Chat, prompts ou sistemas externos sem autorização e avaliação.

## 5. Análises internas (acesso exclusivo Administração/Tecnologia)

- Dashboard por ação, período, município, local, profissional e modalidade de apoio, se justificável. Totais coerentes de `pacientes_unicos`, `atendimentos`, `fichas_finalizadas`, `prescricoes_assinadas`, `comprovantes_entregues`, `reimpressoes` (reimpressões NÃO aumentam atendimentos).
- Indicadores clínicos **somente quando presentes na ficha e clinicamente pertinentes**, inclusive distribuição de tipos sanguíneos exemplificada, com denominador conhecido, nulos à parte, filtros e política contra grupos pequenos.
- Distinguir relatório **operacional nominal restrito** de **análise estatística agregada**; o recurso de Analytics nunca aparece em menus, rotas, downloads ou respostas de API de contas locais.
- Preferir agregação no servidor/SQL e filtros parametrizados. Para dados grandes, definir índices e possível pré-agregação; usar Pandas/NumPy somente se comprovadamente necessários. Evitar carregar o conjunto clínico integral no navegador.

## 6. Integrações e contrato público

**Pipeline preservado:** Actions Map → Agenda Digital → Plataforma Consolidada → Portal Institucional. Reaproveitar contratos e endpoints **reais**, sem criar nomes fictícios; introduzir versão nova retrocompatível quando necessário.

**Permitir somente:** identificador **da ação** (não da pessoa), título/descrição/resumo público aprovado, período/status, municípios IBGE e locais públicos, totais agregados seguros, metadados de parceiro (nome/logo autorizados), e médico parceiro **apenas com flag de exibição e autorização vigente** (`nome`, `CRM/UF`; CNES só no contexto do estabelecimento quando aprovado). Default para profissionais/parceiros é **não publicar**.

**Negar sempre:** dados de pacientes, documentos de identidade, contatos particulares, IDs de pessoa, fichas, tipo sanguíneo individual, prescrições, arquivos, assinaturas, tokens, contas locais, dados financeiros privados e grupos estatísticos reidentificáveis. Contagens por recortes raros podem expor indivíduos; definir supressão/agrupamento de pequenos números antes da publicação. Não fazer do Portal uma cópia do banco clínico.

**Transporte e manutenção:** validação de esquema com versionamento, autenticação serviço-a-serviço, outbox/idempotency key, retries com backoff, métricas de atraso, fila de erros sem PII, atualização incremental e rollback de contrato. A Plataforma controla aprovação/saneamento da API pública; no Portal reutilizar mapa e normalizador, cache e estados de erro. Não criar conexão direta Portal ↔ Actions Map.

## 7. Modelo lógico — referência, NÃO schema executável

| Entidade (nomes ilustrativos) | Propósito | Relações/observações |
|---|---|---|
| `actions` | Metadados, período, status, tipo de apoio, publicação | 1:N locais, atribuições, atendimentos |
| `action_locations`/`locations` | Município IBGE e locais N por ação | Definir N:N ou 1:N após ler schema |
| `partners`, `action_partners` | Clínica/médico/instituição, logo, contribuição, autorização | N:N, publicação opt-in |
| `professionals` | Cadastro e habilitação profissional, CRM/RQE quando cabível | Vínculo a clínica/CNES |
| `local_auth_accounts` | **Segunda tabela de autenticação**, exclusiva Actions Map | FK profissional, hash, ativo, último acesso, revogação; NÃO sincronizar global |
| `action_assignments` | Atribuição de médico/recepcionista à ação | Papel/escopo/status |
| `patients` | Dados pessoais minimizados | Não correlacionar com paciente institucional da Agenda |
| `attendances` | Participação/consulta vinculada a paciente + ação + local | Estados, profissional, histórico |
| `clinical_records` | Campos sensíveis da ficha aprovada | Acesso clínico segregado |
| `documents`, `document_versions`, `signatures` | Comprovantes/prescrições, assinatura, versões | Storage privado, imutabilidade |
| `delivery_acknowledgements` | Recebimento pelo paciente, meio/evidência | Vinculado à versão entregue |
| `import_batches`, `import_items` | PDFs legados, origem/checksum, revisão | Idempotência |
| `integration_outbox` | Eventos agregados aprovados | Sem PII |
| `audit_events` | Trilha de ações relevantes | Metadados minimizados |

**A autenticação global preexistente não é criada nem migrada para este banco.** Usar um **adaptador de autenticação institucional somente para os dois papéis globais autorizados**. Produzir ERD e migrations **somente depois** de comparar com o schema real e definir topologia e retenção.

## 8. Plano incremental de execução e gates

| Fase | Entrega pequena e verificável | Bloqueio/gate | Teste/aceite principal |
|---|---|---|---|
| **0 — Descoberta** | Inventário de código, `docs/`/`data/`/PDFs, esquema de dados, auth atual, API, telas, decisões em conflito; matriz de campos e perguntas. | Ficha real e contratos ausentes são pendências; **sem código**. | Fontes localizadas e requisitos marcados `CONFIRMADO` ou `PENDENTE`. |
| **1 — Modelagem/segurança** | ERD, privilégios dos bancos, contrato RBAC, estados, migrations reversíveis em staging. | Aprovar separação de bancos e duas identidades. | Testes de esquema e concessões de acesso. |
| **2 — Login local e RBAC** | Contas locais, verificação global autorizada, sessões/issuer/audience, login separado, perfis, atribuições. | Nunca replicar senha da AC. | Negativos entre sistemas, endpoints, menu e ações. |
| **3 — Ações, profissionais, parceiros** | CRUD atual preservado + apoio total/parcial, logos, autorizações, seleção de profissionais. | Confirmar semântica de apoio e uso de marca. | Locais N, CRUD, publicação opt-in, revogação. |
| **4 — Triagem e ficha clínica** | Modal secundário, pacientes/atendimentos, fila do médico, separação pessoal/clínico. | **Ficha clínica obrigatória** + aprovação de campos e competências. | Fluxo recepção→médico, autorização por ação, transições. |
| **5 — Prescrição, assinatura e entrega** | PDF clínico, assinatura qualificada validada, recebimento, verificação, segunda via, histórico. | Decidir assinatura válida/provedor e layout. | Assinatura verificável e 2ª via não duplica dados nem quebra PDF. |
| **6 — Importação dos PDFs antigos** | Manifesto, mapeamento, `dry-run`, conferência, lote idempotente, correção auditável. | **Aprovação expressa antes de gravação definitiva.** | Rodar 2x não duplica; registros ambíguos não são inventados. |
| **7 — Analytics privado** | Totais operacionais e estatísticas clínicas aprovadas; filtros, contagens, vazios. | Validar quais dados clínicos e indicadores cabem. | Somente Admin/Tech; totais e denominadores corretos. |
| **8 — APIs e Portal** | Ajustar pipeline e contrato público, médico/parceiros opt-in, mapa, cache/observabilidade. | Compatibilidade das 3 aplicações e revisão LGPD. | Teste ponta a ponta sem PII e com rollback. |
| **9 — Homologação/rollout** | E2E, stress/acessibilidade, backup, guia de operação, flags, rollout gradual. | Aprovação técnica, clínica, jurídica/institucional. | Checklist final e rollback comprovável. |

**Não misturar as fases 2 (identidade), 4 (dados de saúde) e 8 (publicação)** numa única mudança grande. Em transições, permitir feature flags e testes de regressão no fluxo antigo. O agente trabalha somente a fase liberada e registra o que foi validado para reutilização em futuras sessões.

## 9. Importação legada — compatibilidade com MDs antigos

- Preservar cadastro de beneficiário, tabela vinculada à ação, modal secundário, comprovantes e **2ª via**.
- Examinar PDFs em `docs/` e `data/` recursivamente; o acervo pode conter formulários do programa “Melhor Visão”, mas **confirmar nome e conteúdo**. Criar manifesto (arquivo, hash, páginas, campos, qualidade).
- Extrair/mapeamento fiel, comparar pessoas e ações sem confundir município de residência e município do evento; nunca presumir informações clínicas ausentes nos PDFs. Registros sem identificação inequívoca de ação ou com leitura ruim entram em revisão.
- `dry-run` obrigatório, relatório de agregados sem PII, idempotência por origem/linha/hash e aprovação humana antes do lote. Preservar originais sem exclusão/overwrite inadvertidos.
- Registros legados não precisam ganhar fichas clínicas completas retroativamente. Uma importação de cadastro geral **não prova** consulta ou prescrição; documento clínico somente com elementos e assinatura verdadeiros.

## 10. Critérios de aceite de sistema completo

1. Conta global autorizada entra no Actions Map sem duplicar credenciais; conta local entra **só no Actions Map**; sessões e tabelas de auth são distintas e testadas.
2. Recepcionista e médico locais não veem analytics, tela técnica, outro framework nem link da Agenda; chamadas diretas negadas. Administração e Tecnologia acessam analytics; apenas Tecnologia acessa operações técnicas.
3. Cadastro de ação mantém municípios IBGE e N locais, gestão de apoio total/parcial, parceiros e marca autorizada.
4. Cadastro de profissional mantém CRM/UF quando médico; CNES é de estabelecimento; médico parceiro só aparece no Portal se autorizado.
5. Ficha real é dividida entre dados pessoais e clínicos, com triagem e consulta atribuídas e auditáveis.
6. Documento médico é assinado por profissional habilitado com assinatura eletrônica válida/verificável; há confirmação de recebimento e segunda via sem duplicidade ou quebra da assinatura.
7. Indicadores clínicos e dados sensíveis ficam restritos ao Actions Map; recepção e médico locais não têm acesso a analytics.
8. API intersistemas/publicação inclui somente agregados seguros e dados profissionais/parceiros aprovados; **nunca** paciente/ficha/documento clínico.
9. Importação histórica auditada, idempotente, com revisão humana de PDFs problemáticos e sem fabricar registros.
10. Testes de integração + E2E + segurança/IDOR, acessibilidade, migração/rollback, logs saneados, limites de consultas e estados vazios/erro passam em homologação.

## 11. Perguntas pendentes (agrupar e resolver antes da fase afetada)

| Decisão | Necessária para | Critério de resposta |
|---|---|---|
| Qual é a **ficha oficial** e quais campos são de recepção, de médico e opcionais? | Fases 1/4/5/7 | Anexo real, matriz aprovada e exemplos anonimizados. |
| Quem pode exercer quais atos: oftalmologista, médico de outra especialidade, optometrista? | Fases 2/4/5 | Responsável clínico/jurídico confirma competência profissional. |
| Qual solução de **assinatura qualificada** e verificador será adotado? | Fase 5 | Custo, validação jurídica, integração, posse do certificado e teste. |
| Os **bancos** serão instâncias independentes ou bancos separados no mesmo cluster? Como a conta global será validada? | Fases 1/2 | Diagrama real e controles de privilégio/latência. |
| O que exatamente significam **apoio total/parcial**, quando não há parceiros, e quem autoriza publicar logos/CRM? | Fases 3/8 | Regras de negócio e autorização documentadas. |
| Quais **indicadores clínicos** são necessários e justificáveis (ex.: tipo sanguíneo)? | Fase 7 | Lista aprovada, definição de denominadores e privacidade. |
| Quais os endpoints/payloads existentes no pipeline e a política de supressão pública? | Fase 8 | Contratos reais e testes de versão. |
| Qual a política de retenção da ficha, prescrição, logs e termo de recebimento? | Fases 1/4/5 | Aprovação LGPD e política de segurança. |

## 12. Fontes normativas e técnicas para validação na implementação

- LGPD, dados sensíveis e bases legais: https://www.gov.br/anpd/pt-br/acesso-a-informacao/perguntas-frequentes
- Cadastro Nacional de Estabelecimentos de Saúde: https://cnes.datasus.gov.br/
- Documentos médicos eletrônicos, regra de assinatura qualificada a confirmar para o documento exato: https://portal.cfm.org.br/noticias/cfm-atualiza-resolucao-que-regulamenta-emissao-de-atestado-medico
- Localidades do IBGE: https://servicodados.ibge.gov.br/api/docs/localidades
- Uso do `AGENTS.md` e plano em etapas no Codex: https://developers.openai.com/cookbook/examples/codex/iterating-development-workflows-with-codex
- GPT-6.1 Sol e níveis de esforço: https://developers.openai.com/api/docs/models/gpt-6.1-sol

**Nota:** esta especificação organiza trabalho de engenharia; não substitui aprovação clínica, jurídica ou de proteção de dados. Os nomes de entidades, papéis e estados são modelos propostos, sujeitos à verificação contra código e documentos existentes.
