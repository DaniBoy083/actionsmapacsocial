# AGENTS.md — AC Actions Map (instruções persistentes do agente)

> **Status: PLANEJAMENTO.** Não implementar, migrar dados, publicar ou alterar produção sem autorização expressa. Fonte de requisitos: `docs/PLANO_ACTIONS_MAP_GPT61_SOL.md`. Em conflito, decisões recentes deste plano prevalecem sobre os MDs antigos; o código/schema real prevalece sobre nomes e rotas ilustrativos.

## Missão e fronteiras
- Refatorar o **AC Actions Map** para **ações de saúde ocular**, com triagem da recepcionista, complemento clínico pelo profissional habilitado, documento médico assinado, registro de entrega e indicadores internos.
- **Preservar** o cadastro de ações (período, categoria quando existir, descrições, município IBGE, N locais), histórico de beneficiários, segunda via, importação de PDFs e pipeline **Actions Map → Agenda Digital → Plataforma Consolidada → Portal**.
- **Duas origens de autenticação e duas tabelas distintas**: identidade institucional existente da AC (`global`), exclusivamente para Administração/Tecnologia autorizadas; contas **locais do Actions Map** (`local`), exclusivamente para médicos e recepcionistas das ações. Não copiar senhas nem registrar conta local no login institucional. **Contas locais não têm qualquer direito nos demais sistemas AC.**
- **Dois bancos/domínios independentes**: a Agenda mantém o seu banco, o Actions Map mantém seus dados operacionais e clínicos no banco próprio. Validar topologia atual antes de criar migrações. Integração entre sistemas apenas por APIs/contratos aprovados.
- **Administração e Tecnologia** acessam os módulos de gestão e analytics; **somente Tecnologia** acessa rotas de conexão, segredos, APIs e integrações técnicas. **Médicos e recepcionistas não acessam análises de dados**, outras aplicações ou atalhos da Agenda; só ações/casos atribuídos e tarefas do próprio papel. Backend impõe RBAC + escopo por ação; ocultar menus **não** é controle de segurança.
- **Nenhum dado pessoal de paciente, ficha, prescrições ou dado sensível de saúde** segue pela API para Agenda/Plataforma/Portal. Só métricas agregadas publicáveis, com revisão de risco de reidentificação; nome/CRM de profissional e nome/logo de parceiro apenas se expressamente habilitados e aprovados para divulgação.

## Execução econômica e precisa
1. **Leia primeiro este arquivo e o índice/etapa relevante do plano.** Não injete todos os MDs/PDFs no contexto; inventarie e leia cada fonte integralmente **quando a etapa exigir**. A ficha clínica ainda depende do anexo real.
2. Faça **Fase 0 (discovery) antes de qualquer código**. Inspecione `README`, `docs/`, `data/`, `docs/reference/`, `Branding Guide`, migrations, autenticação, integrações e arquivos relevantes, com buscas delimitadas (`rg`, `find`, etc.). Não revelar valores de `.env`.
3. Trabalhe **uma fase por solicitação**. Mudanças mínimas e testáveis; reaproveite stack, componentes, contratos e Clean Architecture existentes. Não inventar nome de tabela/coluna, endpoint ou campo da ficha.
4. Antes de editar: escreva apenas **objetivo, arquivos a alterar, impacto, critérios de aceite e bloqueios**. Ao finalizar: informe apenas **arquivos modificados, testes executados/resultados, pendências e próximo passo**. Evite repetir o contexto completo e logs extensos.
5. Marque `CONFIRMAR` para lacunas que afetam privacidade, atos médicos, assinatura, migração ou contratos. Faça perguntas agrupadas e objetivas somente quando necessárias; não resolva suposições como fatos.
6. Nunca fazer deleção destrutiva, importação definitiva, mudança de permissões em produção, deploy nem rotação de credencial sem aprovação. Usar staging, backup, dry-run, migrações reversíveis, feature flags e rollback.
7. Teste **deny-by-default**: conta local não autentica nas demais APIs; recepção não vê clínica/analytics; médico não acessa casos de outras ações; admin não acessa endpoints técnicos; dados sensíveis nunca saem para o Portal.

## Definição de pronto (por fase)
- Código e migrações compatíveis com repositório real, lint/types/tests pertinentes passando; controle de acesso testado no **servidor**; documentação de contratos alterados; sem PII em logs ou Git; diff enxuto e rollback documentado.
- A implementação completa só é considerada pronta após testes de ponta a ponta, validação da ficha, aprovação dos fluxos profissionais/regulatórios e conferência da API pública.
