# AC Actions Map — Plano consolidado de implementação

**Data do alinhamento:** 12/11/2026\
**Estado:** requisitos consolidados para execução; implementação ainda não iniciada por este documento\
**Aplicação:** AC Actions Map (ações, cadastro de beneficiários e atendimentos oftalmológicos)\
**Integração arquitetural:** AC Core para TI/Administração; autenticação específica do Actions Map para profissionais clínicos e recepção, conforme desenho vigente.

## 1. Objetivo

Atualizar o cadastro de ações, a identificação de instituições e os fluxos de atendimento do Actions Map, corrigindo lentidão e reforçando o isolamento de informações por ação, profissional e atendimento. Preservar os cadastros existentes e as integrações atuais com Agenda Digital, plataforma consolidada e Portal Institucional.

## 2. Escopo decidido no alinhamento

| ID | Frente | Requisito confirmado | Prioridade proposta |
|---|---|---|---|
| AM-01 | Instituições e logomarcas | Ao pesquisar pelo nome de uma instituição, sugerir correspondências e logomarcas, mantendo a escolha entre sugestão e upload de imagem própria. | P1 |
| AM-02 | Contratantes | Renomear **“Identificação Institucional da Ação”** para **“Contratantes”**; permitir adicionar **N contratantes** a uma ação. | P0 |
| AM-03 | Apoiadores | Consolidar **“Modalidade de Apoio”** em uma única seção repetível, como “Locais de Realização”, permitindo **N apoiadores**. | P0 |
| AM-04 | Apoio obrigatório | Para cada apoiador, registrar instituição, tipo (órgão governamental, clínica, outros etc.) e modalidade **total/parcial**; exigir informação de apoio no cadastro da ação. | P0 |
| AM-05 | Profissionais | Trocar a opção/rótulo **“Médica”** por **“Oftalmologista”**; manter **“Nome do profissional”**. Registro profissional exigido de oftalmologistas e optometristas, não da recepção. | P0 |
| AM-06 | Acesso restrito | Recepção somente nas ações a que foi vinculada e sem prontuário clínico; clínicos somente nos atendimentos/pacientes atribuídos, inclusive no acesso via API. | P0 — segurança |
| AM-07 | Ficha clínica | Disponibilizar no atendimento os campos de **olho direito (OD)**, **olho esquerdo (OE)** e **tipo sanguíneo**; apenas oftalmologistas/optometristas podem preencher e editar. | P0 |
| AM-08 | Registro e laudo | O profissional clínico responsável registra o atendimento e emite/assina os documentos compatíveis com sua atribuição profissional. | P0 |
| AM-09 | Desempenho | Diagnosticar e reduzir lentidão de carregamento, requisições e gravação de informações. | P0 — transversal |

**Regra consolidada para o cadastro:** uma ação admite múltiplos contratantes e múltiplos apoiadores, em seções separadas. Como premissa de validação derivada do alinhamento, o cadastro exige **ao menos um contratante e um apoiador**; preservar flexibilidade para revisar essa regra caso existam ações legitimamente sem apoiadores.

## 3. Interface proposta — Cadastro de ações

### 3.1 Contratantes

- Título da seção: **Contratantes** (substitui “Identificação Institucional da Ação”).
- Botão **Adicionar contratante**, no mesmo padrão visual da seção existente de locais de realização.
- Cada bloco permite escolher/cadastrar uma instituição, informar os dados aplicáveis e selecionar sua logomarca.
- Botão **Remover contratante** para os blocos adicionais, sem permitir remover o último quando a obrigatoriedade estiver ativa.
- A mesma instituição pode aparecer em mais de uma ação; evitar cadastros duplicados quando possível.
- O papel **contratante** não deve ser confundido com **apoiador** nos relatórios, documentos e integrações.

### 3.2 Apoiadores — seção única repetível

- Um campo/grupo repetível **Apoiadores** substitui os campos espalhados de modalidade de apoio.
- Para cada apoiador, registrar:
  - **Instituição:** seleção ou inclusão de instituição parceira.
  - **Tipo da instituição:** órgão governamental, clínica, organização/empresa ou outro (lista extensível).
  - **Modalidade de apoio:** total ou parcial (obrigatória por apoiador).
  - **Logomarca:** sugestão verificada ou arquivo enviado pelo usuário.
- Botão **Adicionar apoiador** sem limite fixo definido na interface; validar limites operacionais/segurança no backend.
- Permitir que uma instituição seja contratante numa ação e apoiadora em outra, ou tenha ambos os papéis quando apropriado.
- Diferenciar **tipo de instituição** de **modalidade de apoio**: “clínica” não equivale a “apoio parcial”.

### 3.3 Busca inteligente de instituições e logomarcas

1. Ao digitar, pesquisar primeiro na **base interna de instituições** por nome normalizado e aliases, com correspondências aproximadas claramente sinalizadas.
2. Se não houver resultado adequado, consultar uma fonte externa **autorizada/confiável** para encontrar a identidade visual oficial, priorizando sites institucionais.
3. Exibir nome, origem e prévia da logo sugerida; **não aplicar automaticamente** uma marca somente por similaridade textual.
4. Oferecer as opções **Usar logo sugerida** e **Enviar outra logo**; se não houver sugestão, manter upload disponível.
5. Persistir arquivo/URL gerenciado e metadados de proveniência; não depender de hotlink externo instável.
6. Validar MIME, tamanho, dimensões e segurança de upload; evitar logos falsas ou correspondências ambíguas entre municípios e órgãos homônimos.

**Decisão técnica em aberto:** qual provedor/mecanismo de busca de logomarcas será autorizado. Não assumir a existência de uma API de logos oficiais antes de verificar viabilidade, custo, licenciamento e qualidade dos resultados.

## 4. Cadastro de profissionais e acesso

### 4.1 Campos

- **Nome do profissional:** permanece.
- **Perfil/função:** Oftalmologista, Optometrista, Recepcionista (e demais perfis existentes, se houver).
- Substituir o rótulo **Médica** por **Oftalmologista** em textos, validações, filtros e opções de cadastro; **não** alterar identificadores internos existentes sem migração compatível.
- Para **Oftalmologista**, exigir identificação profissional aplicável (por exemplo, CRM/UF).
- Para **Optometrista**, exigir a identificação profissional pertinente **após validação jurídica/administrativa do tipo de registro aceito**; não rotular automaticamente como CRM.
- Para **Recepcionista**, não exigir nem mostrar campos de registro clínico.

### 4.2 Matriz de acesso

| Atividade | Recepção vinculada | Oftalmologista/optometrista designado | TI/Administração |
|---|---|---|---|
| Ver ação atribuída | Sim | Sim | Conforme perfil administrativo |
| Cadastrar/editar dados pessoais administrativos | Sim, na ação | Conforme necessidade do fluxo | Conforme política interna |
| Ver dados de ações não atribuídas | Não | Não | Somente se autorizado |
| Abrir informações clínicas | Não | Sim, **apenas** em pacientes/atendimentos designados | Não por padrão; exceções auditadas |
| Preencher OD/OE/tipo sanguíneo | Não | Sim, no atendimento designado | Não por padrão |
| Registrar conclusão, emitir ou assinar documento clínico | Não | Sim, **dentro de sua habilitação e atribuição** | Não |

**Obrigatório:** aplicar regras no servidor (RBAC + vínculo com ação/paciente/atendimento), não somente escondendo botões. Validar cada leitura, listagem, gravação, exportação, download e geração de PDF. Retornar `403` em acesso indevido e evitar enumeração de dados entre ações.

**Autenticação:** preservar o login específico do Actions Map para recepção e profissionais clínicos; TI/Administração continuam pelo desenho de integração com o AC Core. Não criar migração de identidade fora deste escopo.

## 5. Ficha clínica do beneficiário

### 5.1 Exibição e edição

- A ficha clínica deve aparecer **dentro do atendimento** quando aberta por profissional clínico autorizado.
- Campos previstos: **olho direito (OD)**, **olho esquerdo (OE)** e **tipo sanguíneo**.
- Modelar OD e OE como **grupos estruturados**, cujo conteúdo exato deverá ser conferido com o responsável clínico (não criar medições ou diagnósticos arbitrários).
- Permitir **“Não informado”** para tipo sanguíneo e campos ainda não aferidos; nunca preencher valores fictícios.
- Salvar com vínculo ao **beneficiário, à ação, ao atendimento e ao autor**, preservando data/hora e histórico de alterações quando necessário.
- Recepção não visualiza, preenche nem altera os campos clínicos.
- Conclusão/assinatura deve refletir atribuição profissional e regras clínicas vigentes: o termo genérico “laudo” não autoriza automaticamente todos os perfis a emitir laudos médicos.

### 5.2 Privacidade e LGPD

- Tratar OD/OE, tipo sanguíneo e documentos clínicos como **dados pessoais sensíveis**.
- Aplicar minimização, criptografia em trânsito, proteção adequada em repouso, trilha de auditoria, retenção/eliminação segundo política institucional e controle rigoroso de acesso.
- Verificar a necessidade clínica do **tipo sanguíneo** para este fluxo antes de torná-lo obrigatório; por ora, mantê-lo opcional.
- Não expor dados clínicos em logs, telemetria, analytics ou no Portal público.

## 6. Modelo de dados sugerido (adaptar ao banco real)

**Não substituir tabelas ou relações existentes sem inventário e migração planejada.** Abaixo está um modelo conceitual, não um script de produção.

```text
Action (existing)
  ├── ActionInstitution (junction)
  │     ├── action_id
  │     ├── institution_id
  │     ├── role: CONTRACTOR | SUPPORTER
  │     ├── support_mode: TOTAL | PARTIAL | NULL (somente SUPPORTER)
  │     ├── display_order
  │     └── ...metadata da relação
  ├── ActionProfessional (assignment)
  │     ├── action_id
  │     └── professional_id
  └── Attendance / BeneficiaryAssignment
        ├── action_id
        ├── beneficiary_id
        ├── assigned_professional_id
        └── ClinicalRecord (1:1 ou 1:N por evolução, a definir)
              ├── right_eye_data
              ├── left_eye_data
              ├── blood_type (nullable)
              ├── author_id
              └── timestamps / audit

Institution
  ├── name, aliases, type
  ├── logo_asset_id / logo_source_url
  └── logo_source / verification_status
```

**Migração segura:** identificar modelos Prisma, constraints, tipos e rotas reais; mapear dados legados da identificação institucional e do apoio para as novas relações; fazer migração **aditiva**; rodar backfill; validar contagens e vínculos; atualizar consumo das APIs; remover código antigo apenas após transição estável. Uma instituição não deve ser duplicada somente por ter papéis diferentes.

## 7. API e validações sugeridas

- `GET /institutions?query=...`: pesquisa interna e correspondências de nomes.
- `GET /institutions/logo-suggestions?...`: resultados de logo com fonte/proveniência quando houver provedor confiável.
- `POST/PATCH /actions`: recebe listas `contractors[]` e `supporters[]`, validando quantidade mínima, IDs, modalidade e duplicidades indevidas.
- `GET /actions/:id/attendances`: filtro obrigatório por vínculo de sessão; nunca aceitar `action_id` isolado como prova de autorização.
- `GET/PATCH /attendances/:id/clinical-record`: autenticação, papel clínico e designação do atendimento verificados no servidor.
- `POST /attendances/:id/clinical-documents`: valida habilitação, autoria, estado do atendimento e assinatura quando aplicável.

As rotas acima são **contratos ilustrativos**; preservar prefixos, convenções, DTOs e versões já usados na implementação. Validar payloads também no backend e impedir que um cliente envie IDs de pacientes ou ações fora da sua autorização.

## 8. Plano de diagnóstico de desempenho

**Não presumir gargalo antes de medir.** Instrumentar e registrar, sem conteúdo clínico sensível:

1. Tempo de abertura do cadastro de ação e do atendimento.
2. Duração das chamadas API (latência mediana e p95), payloads e falhas.
3. Duração das consultas Prisma/PostgreSQL, quantidade de queries, índices e padrões N+1.
4. Tempo de transações de escrita, upload de imagens, validação e geração de documentos.
5. Impacto de autenticação/autorização, serviços externos e infraestrutura Vercel/Neon.

Após identificar gargalos: paginar listas grandes; reduzir consultas duplicadas; usar índices para vínculos de ação/profissional/paciente; revisar includes/selects, cache seguro para dados **não clínicos**; aplicar debounce na busca de instituições; separar upload e autosave quando apropriado; melhorar feedback visual de salvamento/erro e prevenção de duplo envio. Definir metas de latência **depois** de obter a linha de base.

## 9. Sequência de implementação (recomendação)

| Fase | Entregas | Critério de saída |
|---|---|---|
| **0 — Auditoria do estado atual** | Inspecionar repositório/branch, migrations, APIs, formulários, perfis, fluxos e tempos de resposta. Criar backup e plano de rollback. | Inventário de código/dados e baseline de desempenho aprovados. |
| **1 — Segurança e ficha clínica** | Restrições servidor por vínculo; ajustes de cadastro profissional; exibição/gravação de OD/OE/tipo sanguíneo; trilha de auditoria. | Testes negativos de acesso aprovados; ficha clínica funcional para papéis autorizados. |
| **2 — Contratantes e apoiadores** | Seções dinâmicas, modelo relacional, migração aditiva, validação e integração com documentos/relatórios. | Ação salva e reabre corretamente com múltiplos contratantes/apoiadores. |
| **3 — Sugestão de logomarcas** | Busca interna, resolução externa confiável, escolha explícita, upload seguro e reutilização. | Fluxo funciona com sugestão correta, sugestão ambígua e nenhuma sugestão. |
| **4 — Otimização e homologação** | Corrigir gargalos medidos, validar integrações, testes ponta a ponta, piloto e monitoramento. | Sem regressão de acesso/dados e melhora comprovada nos fluxos lentos. |

A frente de desempenho começa na Fase 0 e atravessa as demais. Preferir commits pequenos, revisão manual e **não realizar push/deploy automático** sem autorização operacional.

## 10. Critérios de aceite e testes indispensáveis

- [ ] A tela exibe **Contratantes** no lugar do título antigo.
- [ ] É possível incluir, editar e remover vários contratantes sem perder outros registros.
- [ ] A seção **Apoiadores** permite incluir N registros, cada um com tipo e apoio total/parcial.
- [ ] Cadastro exige os vínculos mínimos definidos, tanto na UI quanto na API.
- [ ] Instituições existentes podem ser reutilizadas em ações distintas, sem duplicação indevida.
- [ ] A busca de logo sugere correspondências e mostra origem, mas o usuário sempre pode escolher upload próprio.
- [ ] Busca sem resultado/ambígua não impede cadastrar a instituição com logo enviada.
- [ ] O cadastro oferece **Oftalmologista**, **Optometrista** e **Recepcionista** com os campos de registro corretos para cada perfil.
- [ ] Recepcionista não consegue consultar dados clínicos, mesmo com URL ou requisição direta.
- [ ] Clínico não consegue abrir ação/paciente/atendimento não designado, mesmo alterando IDs em requisições.
- [ ] OD/OE/tipo sanguíneo aparecem no atendimento autorizado e persistem após recarregar.
- [ ] Campos desconhecidos permanecem vazios/“não informado”; não são criados dados clínicos falsos.
- [ ] Documentos clínicos registram autoria e respeitam a habilitação de quem os emite/assina.
- [ ] Documentos, PDFs, Agenda Digital, plataforma consolidada e Portal preservam compatibilidade e não expõem informação clínica publicamente.
- [ ] Dados antigos de instituições/apoios não são perdidos após migration/backfill.
- [ ] Latência antes/depois é medida; a equipe conhece gargalos corrigidos e pendências.

### Cenários mínimos de autorização

1. Recepção vinculada à **Ação A** tenta listar os pacientes da **Ação B** → negar.
2. Recepção vinculada à Ação A tenta abrir ficha OD/OE por URL direta → negar.
3. Clínico designado à Ação A e ao **Paciente 1** tenta abrir o **Paciente 2** sem designação → negar.
4. Clínico autorizado modifica e salva ficha do Paciente 1 → permitir e auditar.
5. Usuário não autenticado tenta acessar ficha ou documento → negar.
6. Formulário envia instituição sem tipo/modalidade de apoio → rejeitar com mensagem clara.

## 11. Dependências e pontos para validar no código/negócio

- **Modelo real do banco:** identificar tabelas já existentes para instituições, ações, parceiros, beneficiários e profissionais; este documento não presume nomes reais.
- **Registro de optometrista:** confirmar com a equipe responsável o identificador profissional exigível e sua apresentação no formulário; não assumir um conselho específico.
- **Escopo de “laudo”:** aprovar modelos documentais e regras de assinatura de acordo com habilitação profissional e orientação jurídica/técnica responsável.
- **Estrutura clínica OD/OE:** confirmar com a equipe assistencial as medidas/campos exatos de cada olho.
- **Tipo sanguíneo:** revisar finalidade, necessidade, fonte do dado e se deve aparecer nessa ficha específica.
- **Contratantes/apoiadores mínimos:** testar contra ações históricas e eventuais exceções de negócio antes de ativar constraints rígidas.
- **Provedor externo de logos:** validar confiabilidade, licenciamento, custos, privacidade e armazenamento.
- **Performance:** confirmar métricas de base e metas de aceitação por fluxo, sem inventar indicadores prévios.

## 12. Prompt inicial para execução no Workspace

> Analise o repositório atual do AC Actions Map e implemente o plano consolidado de 12/11/2026 de maneira incremental. Comece por mapear formulários, modelos Prisma, migrations, endpoints, permissões e integrações. **Não faça push nem deploy automático e não destrua ou renomeie tabelas existentes sem migração compatível.** Priorize autorização backend por ação/atendimento, correção da ficha clínica e cadastro de profissionais; depois implemente N contratantes e N apoiadores com suas respectivas validações; em seguida a busca opt-in de logomarcas e a otimização baseada em métricas. Produza alterações em commits lógicos, testes de acesso negativo e um resumo de mudanças, riscos e eventuais decisões pendentes. Não exponha dados clínicos em logs, APIs públicas ou integrações analíticas.

---

**Limite do documento:** os requisitos foram definidos na conversa; nenhum repositório, esquema de banco, endpoint ou infraestrutura foi inspecionado nesta etapa. As estruturas e rotas são propostas técnicas sujeitas à validação no código real.
