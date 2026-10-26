# Revisão dos princípios — 26/10/2026

Revisão contra a especificação específica do AC Actions Map, os anexos inspecionados e as decisões posteriores do responsável. O pedido atual prevalece sobre a proposta anterior de manter páginas separadas de Visão geral/Indicadores e um assistente limitado a uma fonte histórica fixa.

## Resultado técnico

| Princípio/requisito | Evidência e tratamento |
| --- | --- |
| Identidade institucional única | Sem contas/senhas locais. Consulta delegada por e-mail/ID, scrypt institucional, RLS preservado e autorização administrativa por equipe revalidada em todas as APIs |
| Tecnologia exclusiva | Página e API verificam equipe no servidor; teste impede acesso da Administração |
| Frontend tipado e componentes reutilizáveis | TypeScript estrito, Next App Router, MUI/Emotion, TanStack Query; conferência nominal isolada em componente RHF/Zod, reaproveitamento do cadastro de ação |
| Separação de camadas | Domínio contém DTOs/regras/portas; aplicação de ações depende da porta de persistência; SQL, cifragem, documentos e carga assistida ficam em adaptadores de infraestrutura. Rotas de leitura/importação ainda compõem adaptadores diretamente; extração adicional de portas permanece melhoria arquitetural, sem alegação de implementação integral de todas as evoluções do MVP |
| Menor redundância | Página `/indicadores` removida; métricas mantidas em `/dashboard`. `/dados-iniciais` redireciona para `/importacoes`; sidebar e atalhos atualizados |
| Inserção por arquivos | PDF/CSV/JSON, envio binário por partes, prévia, rotação, revisão individual, ação de destino, confirmação e relatório. Não grava beneficiários no simples envio |
| Minimização | Apenas nome e município de residência opcional no cadastro; CSV/JSON recusam outros campos; abreviações/ilegíveis não são inferidos. Sem CPF, prontuário ou correlação com `usuario_id` clínico |
| Proteção dos arquivos | Conteúdo cifrado no schema próprio, proprietário por profissional, expiração, quotas, sem nomes originais de arquivo persistidos, sem URL pública, OCR externo ou armazenamento de revisão em localStorage |
| Entrada não confiável | Tamanho/hash, assinatura e parser PDF isolado, limites de tempo/CPU/memória/objetos, formatos estruturados estritos, SQL parametrizado, CSRF/origem e limite de corpo no BFF/API |
| Atomicidade e duplicação | Origem por hash/página ou registro/ação, transação com auditoria/outbox, reenvio idêntico reconhecido, divergência de dados retorna 409, falha desfaz o lote e nomes iguais não são unidos |
| Governança editorial | Cadastro direto em revisão, validação e publicação. Estado antigo removido por solicitação do responsável. Mudanças retiram aprovação e elegibilidade pública anterior |
| Pipeline institucional | Mantém Map → Agenda → Plataforma → Portal. Contrato 1.1 envia pessoas contempladas, quantidade de ações e municípios. `publicavel=true` somente após publicação; nenhum nome/ID individual ou campo clínico |
| Responsividade e acessibilidade | Fluxos de navegador em desktop/celular, labels, foco, mensagens, prévia privada e verificação Axe. Corrigida interação do seletor de arquivos antes da hidratação; análise do modal espera sua animação terminar |
| Segredos e migrações | Nenhuma chave/DSN/transcrição/PDF em commits. Migrações administrativas com backup cifrado verificado e preservação do RLS/dados. Revisões 0005/0006 preparadas para credenciais por hash e exportações agregadas, sem migração produtiva nesta entrega |
| Gestão de integrações | Criação, rotação e revogação de tokens de leitura exigem perfil, origem, CSRF e senha institucional; segredo exibido uma vez fora do cache/storage. Cota transacional, endpoints/cURL copiáveis, exportação congelada e auditoria; a credencial de envio permanece independente |

## Verificação executável

- Backend: **77 testes aprovados**, incluindo arquivos sintéticos, dados extras, quotas, proprietário, CSRF, expiração, rotação, revisão, autorização, idempotência, rollback, publicação com ACK, retirada, rejeição do estado removido e gestão de tokens. PostgreSQL local descartável confirmou migração, grants, revogação e 60 aceitações em 70 consultas concorrentes com 12 trabalhadores.
- Frontend: build de produção, TypeScript e ESLint aprovados. Ruff verificado com a configuração explícita `backend/pyproject.toml`.
- Playwright: **16 cenários aprovados** em desktop/celular, incluindo cadastro/edição/arquivamento, perfis, 404, upload binário PDF, importação CSV, preservação de revisão, gestão de tokens, cópia de endpoint/cURL e Axe. As tabelas da página de integrações receberam região identificada e foco para rolagem por teclado no celular.
- Dados de testes automatizados são sintéticos e usam SQLite temporário. Não há teste de login com a senha real do responsável nem criação de sessão por impersonação.

Comandos completos no README. Artefatos locais de teste ficam ignorados pelo Git.

## Pendências que impedem uma afirmação de “100%”

1. O receptor e a exportação de ações foram implementados na Agenda. A Plataforma ainda deve consumir essa fonte e atualizar o Portal; a recepção na Agenda não é prova de atualização do mapa público.
2. Política institucional de retenção, governança de publicação, monitoramento operacional e ensaio integral de restauração ainda precisam de homologação. O expurgo tem comando seguro, mas seu agendamento institucional não foi presumido.
3. Correção/remoção de beneficiários, associação de cadastro existente, conciliação entre fontes distintas, filtros analíticos avançados e refinamentos do modelo relacional continuam pendências do MVP já registradas. Não houve preenchimento por inferência nem migração automática de dados clínicos/Portal.
4. O lote histórico foi concluído após aprovação expressa do responsável das 18 fichas restantes e sua orientação de preencher municípios ausentes com Mamanguape. A conferência produtiva confirmou 50 fichas, nenhum município ausente e ausência de duplicação da origem, após staging cifrado e backup verificado. A prévia nominal fica privada e separada do commit. A identificação de pessoas únicas entre fontes diferentes continua dependendo de conciliação supervisionada.
5. O GitHub Actions permanece sujeito ao bloqueio de faturamento previamente identificado na conta. Verificações locais e build Vercel não são apresentados como execução bem-sucedida desse workflow.

As alterações solicitadas foram verificadas tecnicamente dentro do projeto; estes limites continuam explícitos. Testes aprovados não constituem certificação jurídica, aceite institucional integral ou prova de ausência absoluta de falhas.
