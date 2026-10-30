# AC Actions Map — Especificação otimizada para agente de desenvolvimento

**Versão:** 2.1 (30/10/2026)

**Estado:** PLANEJAMENTO ATUALIZADO / LEITURA DA FICHA ORIGINAL OBRIGATÓRIA PELO AGENTE / MVP OPERACIONAL SEM ASSINATURA DIGITAL

**Modelo previsto:** GPT-6.1 Sol no Codex, Work ou agente de IDE compatível  
**Destino no repositório:** `docs/PLANO_ACTIONS_MAP_GPT61_SOL.md`  
**Documento de entrada do agente:** `AGENTS.md` na raiz

> **REGRA DE EXECUÇÃO:** este documento orienta a futura implementação, sem autorizar deploy ou migração em produção. Antes de programar campos clínicos, o Sol deve **localizar, abrir e ler integralmente a ficha de exame real já mencionada como presente no workspace**; aqui não foi possível inspecioná-la. Não supor nome, páginas nem conteúdo. Desenvolver em fases após inspeção, testes e autorização pertinente.

## ATUALIZAÇÃO VINCULANTE — reunião de alinhamento de 30/10/2026

**Esta seção resolve decisões posteriores ao plano de 29/10 e prevalece em qualquer conflito com as seções históricas abaixo.** O objetivo é preparar o Actions Map para a próxima ação, prevista aproximadamente dez dias após 30/10; a data efetiva deverá ser confirmada pelo responsável. A urgência operacional NÃO dispensa segurança, revisão profissional nem testes.

### A. Primeiro gate do Sol: leitura da ficha clínica original (OBRIGATÓRIA)

1. **Antes de programar triagem, ficha, relatório, PDF, documento de laboratório, etiqueta ou campos de saúde, Sol DEVE encontrar e ler a ficha original no repositório/workspace** (não apenas este plano). Procurar recursivamente em `docs/`, `docs/reference/`, `data/`, anexos e caminho informado pelo projeto; identificar arquivo/versão/páginas e inspecionar todas as páginas, frente/verso, quadros, imagens e tabelas, inclusive por visualização quando OCR/texto forem incompletos.
2. Registrar resultado verificável: `caminho_real`, `tipo`, `total_paginas`, se há imagens escaneadas, seções/campos literais, campo → tipo/obrigatoriedade → preenchido por recepção ou profissional habilitado → destino na ficha/etiqueta/BD → finalidade/risco LGPD. Classificar lacunas `PENDENTE` antes de inventar valores ou regras.
3. A ficha será enriquecida **sem alterar os dados médicos existentes** pelos metadados da ação: **nome/título da emenda ou convênio, número da emenda ou convênio e autor da emenda**. A origem é a ação cadastrada por Administração/Tecnologia, nunca a digitação manual repetida pela recepção.
4. Se não encontrar a ficha, relatar `BLOQUEADO — FICHA NÃO LOCALIZADA` e caminhos pesquisados; parar somente desenvolvimento dependente da ficha. Não declarar leitura sem evidência. Não copiar dados reais de pacientes para Git, logs ou prompts.

### B. Cadastro administrativo da ação — logomarcas e financiamento

- Os perfis institucionais **Administração e Tecnologia** podem cadastrar/editar, além dos campos atuais, **nome/título da emenda ou convênio**, **número da emenda ou convênio** e **autor da emenda**, com classificação opcional do instrumento (`EMENDA`, `CONVENIO`, `OUTRO/NAO_INFORMADO`) conforme a realidade; se não há emenda, não obrigar autor fictício. Guardar vínculos e histórico de edição, validar consistência e evitar alterar retroativamente comprovantes emitidos.
- As posições de logo são **(1) AC Social, sempre mostrada a partir do arquivo oficial já existente no projeto; (2) órgão governamental, upload opcional; (3) clínica parceira, upload opcional**. As duas opções de upload devem existir **para toda ação, sem depender de apoio total/parcial**. Onde não houver parceiro, não mostrar logo falsa, não exigir imagem e não quebrar o layout. O cabeçalho da ficha/etiqueta/peças aplicáveis deve comportar até três logos mantendo a AC Social; validar formatos, resolução, acessibilidade, direitos de uso e autorização separada para divulgar no Portal.
- A modalidade de verba/apoio `TOTAL` ou `PARCIAL` **não é condição de exibição do cadastro de logos**. Outros parceiros (1:N) podem ser administrados no futuro sem prejudicar os três slots esperados nos impressos.

### C. Propagação automática para recepção, exame e laboratório

- Ao abrir a ação autorizada, a recepcionista visualiza **nome, número e autor da emenda/convênio** já preenchidos e bloqueados para edição operacional. O atendimento vincula-se à ação pelo identificador estável; persistir snapshot institucional apenas quando necessário à fidelidade de documentos emitidos e auditoria.
- A ficha que segue ao oftalmologista/profissional legalmente habilitado deve herdar esses metadados e as logos permitidas. Separar dados administrativos de informações clínicas. **Preservar integralmente a ficha original como fonte de campos** e conferir com responsável clínico quaisquer impressões de prescrição/ordem de laboratório; o papel profissional de optometrista depende de validação de competências, sem equipará-lo automaticamente a médico.
- Após conclusão autorizada, oferecer **dois artefatos simultâneos**: `ficha/documento de exame para o laboratório` **e** `etiqueta adesiva de identificação` para o saquinho/embalagem. Opções: imprimir ficha, imprimir etiqueta, imprimir ambos; reimprimir sem novo atendimento. A etiqueta deve conter apenas os identificadores operacionais mínimos aprovados (por exemplo: nome do beneficiário, código interno do atendimento, ação/data e referência do laboratório), sem diagnóstico, graus ou dados excessivos. Campo de emenda/autor na etiqueta somente se operacionalmente necessário e layout permitir; não confundir exigência de aparecer na ficha com exposição irrestrita na etiqueta.
- Testar largura real da etiqueta, margens, papel A4, escala `100%`, leitores, quebra de página, impressão sem internet quando aplicável e rastreio de reimpressões.

### D. Assinatura digital e autenticação avançada: **STANDBY PARA O MVP**

- **Não implementar agora** integração de assinatura eletrônica/digital, PAdES/ICP-Brasil, gov.br, captura digital de assinatura do paciente, verificação pública ou novo fluxo complexo de login local para a próxima ação. Manter o design e requisitos futuros documentados, mas **retirar assinatura digital da cadeia crítica** de recepção → exame → documento em papel → etiqueta → laboratório.
- O plano histórico de **duas identidades** continua como arquitetura futura, não como obrigação de lançamento piloto. No piloto, a equipe técnica deve primeiro verificar quais mecanismos de autenticação/autorização existentes podem ser usados **com segurança**; nunca disponibilizar prontuários ou dados pessoais sem controle de acesso, nem compartilhar credenciais. A ausência de um mecanismo mínimo confiável é bloqueio de go-live, não motivo para habilitar login anônimo.
- Documento clínico **sem assinatura eletrônica válida** não deve ser descrito como prescrição eletrônica assinada. Observar os procedimentos físicos de assinatura/validação exigidos pelo profissional responsável e assessoria institucional, mantendo trilha de emissão, segunda via e controle de entrega.

### E. Analytics completo e interoperabilidade

**Analytics interno (somente Administração/Tecnologia):** número de ações por período/município/local, perfis de parceira/órgão, quantitativos de beneficiários distintos, participações/atendimentos, triagens, fichas concluídas, fichas/etiquetas impressas, reimpressões, entregas, distribuição por **nome/número da emenda ou convênio e autor da emenda**, com filtros combináveis e tabelas/gráficos. Indicadores clínicos só se encontrados na ficha original, justificados e liberados. Mostrar denominador, duplicidades entre ações, nulos e atrasos da integração; não misturar pessoas únicas com atendimentos.

**Contrato intersistemas, sem conexões alternativas:**

```text
Actions Map (BD clínico privado + agregação)
  -> API interna autenticada -> Agenda Digital
  -> API/integração validada -> Plataforma Consolidada de Análise de Dados
  -> API pública read-only (saneada) -> Portal Institucional / Mapa de Ações
```

A carga agregada deve conter metadados aprovados da ação **inclusive nome/título, número e autor da emenda/convênio**, ID estável da ação, município/código IBGE, datas/status, eventual nome/logo de parceiro autorizados e contagens válidas por ação/emenda/autor. A Plataforma deve permitir consultas do tipo **quantas ações e pessoas beneficiadas por município/ação/emenda/autor**, especificando se a contagem é de participações ou pessoas únicas, com regras contra dupla contagem. A API pública deve expor apenas campos explicitamente aprovados, evitando dados pessoais, clínicos, financeiros privados ou grupos pequenos reidentificáveis. **O nome de um autor de emenda é um metadado administrativo da ação, não uma informação clínica do beneficiário**; não realizar vinculação nominal beneficiário ↔ agente político.

A Agenda recebe resumos versionados/idempotentes, faz encaminhamento controlado; a Plataforma valida e saneia; o Portal consome **somente** a Plataforma. Proteger cache, auditoria, autenticação serviço-a-serviço e sincronizações tardias. Não afirmar integração implantada sem teste E2E real.

### F. Sequência operacional sugerida (MVP versus evoluções)

| Prioridade | Entrega | Critério mínimo de aceite |
|---|---|---|
| P0 — Antes de qualquer implementação | **Sol lê e comprova leitura da ficha original**, inspeciona código, auth, schema, assets, logos oficiais, impressoras e contratos existentes; documenta lacunas. | Caminho/páginas/campos reais registrados, matriz de papéis e campos, riscos e cronograma de execução priorizado. |
| P1 — Essencial para a próxima ação | Cadastro administrativo com 3 logos (AC + uploads opcionais), metadados de emenda/convênio, recepção visualizando dados herdados, ficha de exame aprovada, impressão de ficha + etiqueta, listagem por ação e permissão segura. | Uso em testes operacionais com dados fictícios; impressão física legível; ausência de acesso indevido. |
| P2 — Útil para a próxima ação, conforme capacidade | Indicadores operacionais internos, exportação agregada segura e validação de propagação Actions Map → Agenda → Plataforma → Portal; ranking por emenda/autor somente quando números aprovados e consistentes. | Consistência de totais, sem PII, versionamento de contrato e testes de reconciliação. |
| P3 — Após a ação/sem pressa operacional | Autenticação local exclusiva com RBAC avançado, assinatura eletrônica válida, verificadores, QR público, dashboards clínicos avançados e automações opcionais. | Avaliação jurídica, clínica, LGPD e de segurança antes de liberar. |

**Regra de prioridade:** nenhum esforço em P3 pode bloquear impressão da ficha, etiqueta, atendimento seguro ou cadastro da ação no P1. Caso P2 não esteja pronto, manter integração anterior estável sem publicar dados incompletos como se estivessem atuais.

### G. Testes de aceite adicionais, obrigatórios

- [ ] Sol aponta o caminho e a versão da **ficha original** e prova revisão integral, incluindo páginas digitalizadas.
- [ ] Admin/Tech podem incluir logo governamental e clínica **em apoio TOTAL e PARCIAL**; ambas são opcionais; a logo oficial AC Social é aplicada no documento quando o arquivo legítimo estiver disponível.
- [ ] Cadastro administrativo alimenta automaticamente recepção → ficha médica → documento laboratorial; histórico consistente após edição administrativa.
- [ ] Ficha e etiqueta coexistem; impressão individual/conjunta e segunda via funcionam sem duplicar atendimento.
- [ ] Assinatura digital e novo login local **não bloqueiam** o MVP, mas controle de acesso seguro é obrigatório.
- [ ] Analytics interno somente Admin/Tech; filtros por ação, local, emenda/convênio e autor; totais conciliados e nulos identificados.
- [ ] Payload interno inclui atributos públicos aprovados da emenda e indicadores, sem ficha/identidade de beneficiário; pipeline até o Portal validado conforme fase autorizada.

---

## 0. Como usar com economia de tokens

**Estratégia de contexto em duas camadas.** `AGENTS.md` contém regras permanentes curtas; este documento é lido **somente na seção da fase solicitada** e nas seções transversais necessárias. Os MDs históricos são fontes de consulta, não prompts para serem concatenados repetidamente. Inventariar os PDFs e ler os relevantes quando for modelar/importar dados; não enviar o texto integral dos PDFs para o contexto sem necessidade.

**Prompt inicial recomendado (copiar no agente):**

> Leia `AGENTS.md`, **a atualização vinculante de 30/10/2026** em `docs/PLANO_ACTIONS_MAP_GPT61_SOL.md`, e as seções 1, 2 e Fase 0. **Localize e leia integralmente a ficha clínica ORIGINAL no workspace antes de planejar seus campos ou implementá-los; informe o caminho real e páginas verificadas.** Sua tarefa **agora é somente diagnóstico e planejamento detalhado**: inventarie arquivos e esquema reais, identifique conflitos com os MDs históricos e a ficha clínica, produza a matriz de campos/permissões e um backlog priorizado. Não escreva código, não aplique migrações, não acesse produção e não invente campos. Liste dúvidas bloqueantes objetivas. Depois aguarde autorização para cada fase.

**Em cada fase posterior:** “Execute **somente a Fase N** do plano. Leia apenas os arquivos afetados, implemente o menor conjunto coerente, rode testes aplicáveis e reporte diff/testes/bloqueios; não avance para outra fase.”

**Diretrizes ao GPT-6.1 Sol:** usar esforço `medium` para descoberta focalizada e tarefas delimitadas; aumentar para `high` ou superior em arquitetura de identidade, banco, permissões, contrato de integração, migração clínica ou assinatura quando disponível. Maior esforço **não garante menor custo**: medir qualidade, tool calls e retrabalho. Usar respostas concisas, saída incremental, diffs em vez de arquivos completos e contratos tipados. Não usar “leia tudo novamente” em cada prompt.

## 1. Fontes, precedência e conflitos resolvidos

**Referências já localizadas na Biblioteca do ChatGPT (anexar ao workspace/repo se ainda não estiverem lá):**

1. `AC_ACTIONS_MAP_DOCUMENTACAO_AGENT.md` — arquitetura, login institucional, locais N:N, importação, dashboard, área técnica e padrões de stack.
2. `PLANEJAMENTO_ACTIONS_MAP_BENEFICIARIOS.md` — vínculo beneficiário/ação, segundo modal, comprovante/segunda via, importação histórica, LGPD e idempotência.
3. `plano_integracao_mapa_acoes_portal_institucional.md` — contrato de leitura da Plataforma Consolidada, mapa do Portal, cache, normalização e testes.
4. `PLANEJAMENTO_AC_ACTIONS_FRAMEWORK_AC_SOCIAL.md` — histórico arquitetural geral; usar apenas partes compatíveis com a decisão atual.
5. **Fonte definitiva para campos clínicos: ficha original de atendimento ocular indicada pelo responsável como presente no workspace (ainda NÃO INSPECIONADA neste documento)**. O Sol deve localizar e ler o arquivo real antes de modelar ou implementar. Não supor seu layout nem seu nome.

**Ordem de prioridade (sempre subordinada às exigências legais/profissionais):** decisões de 30/10/2026 (seção vinculante) > requisitos explícitos de 29/10/2026 > ficha clínica aprovada quanto aos campos > contratos/esquema reais > MDs antigos como legado de funcionalidades. As decisões atuais **substituem** duas premissas antigas: (a) Actions Map genérico, sem dados clínicos; (b) login exclusivamente institucional/único domínio de banco. A proposta anterior de compartilhar `usuario_id` dos pacientes e a ideia de não criar contas locais **não se aplicam** ao fluxo atual.

**Não apagar PDFs ou registros legados.** Construir uma matriz de conflitos `origem → decisão atual → impacto → migração` antes de codificar.

## 2. Decisões de arquitetura inegociáveis

### 2.1 Domínios e fluxo

```text
AC Actions Map (banco próprio, contas locais + acesso global autorizado)
    ├─ ações/localidades/parceiros
    ├─ pacientes/triagem/ficha clínica/documentos impressos no MVP; assinatura eletrônica somente no futuro
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

### 2.2 Autenticação — duas tabelas e isolamento real (DESENHO FUTURO; NÃO IMPLANTAR NOVA AUTH LOCAL NO MVP)

| Origem | Persistência | Quem usa | Direito de acesso |
|---|---|---|---|
| **Global AC Social** | Tabela existente de autenticação institucional, pertencente ao sistema AC | Membros ativos das equipes **Administração** e **Tecnologia**, com tipo de login autorizado | Actions Map e outras aplicações **somente segundo as permissões institucionais já existentes**. O Actions Map apenas consulta/verifica essa identidade por integração autorizada, sem replicar senhas. |
| **Local Actions Map** | **Nova tabela própria no banco do Actions Map**, distinta da global | Médicos e recepcionistas cadastrados para ações | **Exclusivamente Actions Map**, conforme papel e ações atribuídas. Zero credenciais/escopos/sessões reutilizáveis nas outras aplicações AC. |

**Obrigatório quando a arquitetura futura for implantada:** `auth_source` explícito (`GLOBAL` ou `LOCAL`), roles/claims e audiência da sessão específicas, expiração, revogação, validação no backend, separação de namespaces/cookies/tokens, rate limiting, recuperação de conta controlada, hash de senha moderno para locais, MFA para contas privilegiadas conforme política aprovada, registro mínimo de auditoria. Preferir login institucional via mecanismo existente de verificação confiável; não consultar diretamente hash global nem armazená-lo na base local. Proteger contra mesmo login/e-mail em origens diferentes, confusão de sessão, IDOR e escalada de privilégios.

**Experiência local:** exibir somente marca e páginas do Actions Map; jamais apresentar link, sidebar, URL de navegação, descrição interna ou atalho da Agenda, de outros frameworks, de analytics ou da tela técnica. Segurança real exige que **as outras aplicações recusem o token local por issuer/audience/escopo**, inclusive em chamadas diretas. Esconder links não substitui autenticação/autorização.

**Login e rotas exatos** serão definidos após inspeção do repositório; uma separação possível é tela de acesso local própria e entrada institucional não divulgada a operadores locais. **A existência de dois fluxos não deve obrigar o profissional local a escolher ou conhecer a origem institucional.**

### 2.3 Matriz mínima de permissões (aplicar segregação também no MVP, com os mecanismos existentes validados)

Legenda: `A` acesso; `R` leitura restrita; `—` proibido. Autorizações verificadas no servidor, por ação atribuída, por recurso e por status.

| Recurso/ação | Admin global | Tecnologia global | Médico local | Recepcionista local |
|---|:---:|:---:|:---:|:---:|
| Cadastro/edição/arquivamento de ação, locais, parcerias | A | A | — | — |
| Cadastro/ativação de profissionais locais e suas atribuições | A | A | — | — |
| Ver ações e pacientes **atribuídos** para executar função | A* | A* | R | R |
| Cadastrar/corrigir dados pessoais de triagem | A* | A* | R | A (na ação designada) |
| Preencher/alterar ficha clínica autorizada | A* | A* | A (somente competência autorizada) | — |
| Assinatura eletrônica da prescrição (FUTURO / STANDBY) | — | — | A (somente médico habilitado, quando implementada) | — |
| Imprimir ficha e etiqueta / registrar entrega do documento em papel | A* | A* | A (na ação atribuída) | R (conforme fluxo aprovado) |
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
- Gestão de parceiros/apoio: `apoio = TOTAL | PARCIAL` (validar significado operacional). Em **TOTAL ou PARCIAL**, permitir **sempre** os uploads opcionais de logotipo governamental e de clínica parceira, além da marca oficial AC Social (padrão). Parcerias adicionais 1..N com nome, categoria, contribuição e autorização podem ser mantidas sem condicionar os dois uploads à modalidade de apoio.
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
  → Gera ficha/documento para IMPRESSÃO EM PAPEL (MVP)
  → Gera ETIQUETA de identificação para o saquinho/laboratório
  → Assinatura/validação física por profissional habilitado, conforme fluxo aprovado
  → Entrega e registro de recebimento (papel no MVP)
  → Segunda via/impressão sem criar novo atendimento
```

- Usar paciente separado de atendimento; um paciente pode comparecer a várias ações, com registros separados e chave idempotente de evento. Deduplicação cuidadosa, nunca unificar só por nome.
- Estados sugeridos (ajustar à operação real): `EM_TRIAGEM`, `AGUARDANDO_MEDICO`, `EM_ATENDIMENTO`, `FICHA_CONCLUIDA`, `DOCUMENTO_IMPRESSO`, `ENTREGUE`, `CANCELADO` e `PENDENTE_REVISAO`; os estados `AGUARDANDO_ASSINATURA` e `ASSINADO` são exclusivos de uma fase FUTURA de assinatura eletrônica. Transições validadas no backend; alterações assinadas demandam nova versão e nova assinatura.
- Campos pessoais e clínicos em entidades **separadas**, controles diferentes por papel, mascaramento nas listagens, trilha de leitura/edição e prazo de retenção. Não fazer consultas clínicas a partir da Agenda.
- A futura **ficha real é a fonte dos campos**, com matriz `campo → finalidade → titular → tipo (pessoal/sensível) → responsável por preenchimento → obrigatório? → validação → persistência → visibilidade → retenção`. Não inventar CPF, sangue ou dados oftálmicos obrigatórios sem conferência.

### 3.4 Documentos, assinaturas e comprovantes
> **ATUALIZAÇÃO 30/10:** a descrição de assinatura digital abaixo é **exclusivamente para fase futura**, não para o MVP. O MVP usa documento clínico impresso, etiqueta de laboratório e validação profissional em papel conforme exigências aplicáveis.
- **Documento médico eletrônico (FUTURO / STANDBY):** assinatura do médico habilitado com mecanismo **qualificado/ICP-Brasil**, conforme enquadramento regulatório que deve ser validado antes da implementação; assinatura visível em PDF não equivale a assinatura criptográfica verificável. Preferir PDF assinado PAdES ou formato aceito pelo validador escolhido; preservar hash, versão, evidências e cadeia de verificação.
- Integração com **gov.br não é pressuposta nem condição de implementação**: verificar elegibilidade da API, tipo de assinatura efetivamente produzido e aderência às regras de documentos médicos. Não prometer integração automática sem viabilidade demonstrada.
- **Paciente:** comprovante de recebimento em papel no MVP; assinatura/captura digital na própria aplicação apenas em fase futura, com forma, horário, vínculo ao documento e armazenamento restrito. **Não tratar assinatura do paciente como aprovação do conteúdo clínico.**
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

- Dashboard por ação, período, município, local, profissional e modalidade de apoio, se justificável. Totais coerentes de `pacientes_unicos`, `atendimentos`, `fichas_finalizadas`, `fichas_impressas`, `etiquetas_impressas`, `comprovantes_entregues`, `reimpressoes` (e `prescricoes_assinadas` somente após fase futura) (reimpressões NÃO aumentam atendimentos).
- Indicadores clínicos **somente quando presentes na ficha e clinicamente pertinentes**, inclusive distribuição de tipos sanguíneos exemplificada, com denominador conhecido, nulos à parte, filtros e política contra grupos pequenos.
- Distinguir relatório **operacional nominal restrito** de **análise estatística agregada**; o recurso de Analytics nunca aparece em menus, rotas, downloads ou respostas de API de contas locais.
- Preferir agregação no servidor/SQL e filtros parametrizados. Para dados grandes, definir índices e possível pré-agregação; usar Pandas/NumPy somente se comprovadamente necessários. Evitar carregar o conjunto clínico integral no navegador.

## 6. Integrações e contrato público

**Pipeline preservado:** Actions Map → Agenda Digital → Plataforma Consolidada → Portal Institucional. Reaproveitar contratos e endpoints **reais**, sem criar nomes fictícios; introduzir versão nova retrocompatível quando necessário.

**Permitir somente:** identificador **da ação** (não da pessoa), título/descrição/resumo público aprovado, período/status, municípios IBGE e locais públicos, totais agregados seguros, **nome/título, número e autor da emenda/convênio, após aprovação de publicação**, metadados de parceiro (nome/logo autorizados), e médico parceiro **apenas com flag de exibição e autorização vigente** (`nome`, `CRM/UF`; CNES só no contexto do estabelecimento quando aprovado). Default para profissionais/parceiros é **não publicar**.

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
| **2 — Login local e RBAC (FUTURO, STANDBY)** | Arquitetura de contas locais e validação segura, sem implantar novo login para o MVP. No MVP, auditar os controles já existentes e exigir autorização real. | Nunca replicar senha da AC nem abrir dados clínicos sem autenticação. | Negativos entre sistemas e endpoints antes de ativar. |
| **3 — Ações, profissionais, parceiros** | CRUD atual + logos AC Social, governo e clínica (dois uploads opcionais em apoio total/parcial), campos de emenda/convênio, seleção autorizada de profissionais. | Conferir asset oficial e direitos de uso. | Locais N, CRUD, autoria dos campos, impressão e publicação opt-in. |
| **4 — Triagem e ficha clínica** | Modal secundário, pacientes/atendimentos, fila do médico, separação pessoal/clínico. | **Ficha clínica obrigatória** + aprovação de campos e competências. | Fluxo recepção→médico, autorização por ação, transições. |
| **5 — Ficha e etiqueta de laboratório (MVP) / assinatura eletrônica (FUTURO)** | Gerar/validar PDF para papel, etiqueta de identificação, impressão conjunta/separada, segunda via e entrega. Assinatura eletrônica permanece em STANDBY. | Ficha real lida e fluxos de impressão/validação física aprovados. | Papel e etiqueta legíveis; 2ª via não duplica dados; nenhuma afirmação falsa de assinatura digital. |
| **6 — Importação dos PDFs antigos** | Manifesto, mapeamento, `dry-run`, conferência, lote idempotente, correção auditável. | **Aprovação expressa antes de gravação definitiva.** | Rodar 2x não duplica; registros ambíguos não são inventados. |
| **7 — Analytics privado** | Totais operacionais e estatísticas clínicas aprovadas; filtros por emenda/convênio, autor, ação e local; contagens, vazios. | Validar campos clínicos, denominadores e risco de reidentificação. | Somente Admin/Tech; totais, pessoas únicas e denominadores corretos. |
| **8 — APIs e Portal** | Ajustar pipeline e contrato público com emenda/convênio/autor aprovados, indicadores por ação e ranking de beneficiados, parceiros opt-in, mapa, cache/observabilidade. | Compatibilidade das 3 aplicações e revisão LGPD/atribuições. | Teste ponta a ponta sem PII, sem dupla contagem e com rollback. |
| **9 — Homologação/rollout** | E2E, stress/acessibilidade, backup, guia de operação, flags, rollout gradual. | Aprovação técnica, clínica, jurídica/institucional. | Checklist final e rollback comprovável. |

**Não misturar as fases 2 (identidade), 4 (dados de saúde) e 8 (publicação)** numa única mudança grande. Em transições, permitir feature flags e testes de regressão no fluxo antigo. O agente trabalha somente a fase liberada e registra o que foi validado para reutilização em futuras sessões.

## 9. Importação legada — compatibilidade com MDs antigos

- Preservar cadastro de beneficiário, tabela vinculada à ação, modal secundário, comprovantes e **2ª via**.
- Examinar PDFs em `docs/` e `data/` recursivamente; o acervo pode conter formulários do programa “Melhor Visão”, mas **confirmar nome e conteúdo**. Criar manifesto (arquivo, hash, páginas, campos, qualidade).
- Extrair/mapeamento fiel, comparar pessoas e ações sem confundir município de residência e município do evento; nunca presumir informações clínicas ausentes nos PDFs. Registros sem identificação inequívoca de ação ou com leitura ruim entram em revisão.
- `dry-run` obrigatório, relatório de agregados sem PII, idempotência por origem/linha/hash e aprovação humana antes do lote. Preservar originais sem exclusão/overwrite inadvertidos.
- Registros legados não precisam ganhar fichas clínicas completas retroativamente. Uma importação de cadastro geral **não prova** consulta ou prescrição; documento clínico somente com elementos e assinatura verdadeiros.

## 10. Critérios de aceite de sistema completo

1. **MVP:** acesso seguro aproveitando mecanismos existentes validados, sem exposição pública de dados pessoais/clínicos. **Futuro:** conta global e conta local exclusiva do Actions Map, com sessões/tabelas separadas e testadas.
2. Recepcionista e profissional operacional não veem analytics, tela técnica, outro framework nem link da Agenda; chamadas diretas negadas. Administração e Tecnologia acessam analytics; apenas Tecnologia acessa operações técnicas.
3. Cadastro da ação mantém municípios IBGE e N locais, **nome/número/autor de emenda ou convênio**, e logos da AC Social + governamental/clínica opcionais **em apoio total ou parcial**, com publicação autorizada.
4. Cadastro de profissional mantém CRM/UF quando médico; CNES é de estabelecimento; médico parceiro só aparece no Portal se autorizado.
5. **Sol deve comprovar que leu a ficha real no workspace**; ficha é dividida entre dados pessoais e clínicos, com triagem e consulta atribuídas e auditáveis; a recepção vê dados de emenda herdados da ação.
6. **MVP:** ficha/documento clínico é impresso em papel e acompanhado de etiqueta para o laboratório; validação profissional física conforme fluxo aprovado, confirmação de recebimento e segunda via sem duplicidade. **Fase futura:** assinatura eletrônica válida/verificável, após autorização e enquadramento regulatório.
7. Indicadores clínicos e dados sensíveis ficam restritos ao Actions Map; recepção e médico locais não têm acesso a analytics.
8. API intersistemas/publicação inclui somente agregados seguros, metadados institucionais aprovados **(nome/número/autor da emenda/convênio)** e dados profissionais/parceiros aprovados; **nunca** paciente/ficha/documento clínico; permitir visualização/ranking de beneficiados por emenda/autor sem dupla contagem.
9. Importação histórica auditada, idempotente, com revisão humana de PDFs problemáticos e sem fabricar registros.
10. Testes de integração + E2E + segurança/IDOR, acessibilidade, migração/rollback, logs saneados, limites de consultas e estados vazios/erro passam em homologação.

## 11. Perguntas pendentes (agrupar e resolver antes da fase afetada)

| Decisão | Necessária para | Critério de resposta |
|---|---|---|
| Qual é a **ficha oficial** e quais campos são de recepção, de médico e opcionais? | Fases 1/4/5/7 | Anexo real, matriz aprovada e exemplos anonimizados. |
| Quem pode exercer quais atos: oftalmologista, médico de outra especialidade, optometrista? | Fases 2/4/5 | Responsável clínico/jurídico confirma competência profissional. |
| Qual solução de **assinatura qualificada** e verificador será adotado? | Fase futura (pós-MVP) | Custo, validação jurídica, integração, posse do certificado e teste. |
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
