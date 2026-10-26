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
| Governança editorial | Cadastro inicial em rascunho; inclusão de participações agora também retira aprovação anterior. Publicação continua bloqueada até contrato receptor e homologação |
| Pipeline institucional | Mantém Map → Agenda → Plataforma → Portal. Outbox transmite apenas resumos permitidos, `publicavel=false`, sem nomes/IDs individuais ou campos clínicos |
| Responsividade e acessibilidade | Fluxos de navegador em desktop/celular, labels, foco, mensagens, prévia privada e verificação Axe. Corrigida interação do seletor de arquivos antes da hidratação; análise do modal espera sua animação terminar |
| Segredos e migrações | Nenhuma chave/DSN/transcrição/PDF em commits. Migração `0003` aditiva com backup cifrado verificado, duas tabelas privadas, grants mínimos e preservação do RLS e das ações existentes |

## Verificação executável

- Backend: **61 testes aprovados**, incluindo arquivos reais sintéticos, conteúdo ativo/forjado, dados extras, quotas, proprietário, CSRF, expiração, rotação, revisão, autorização produtiva, idempotência e rollback.
- Frontend: build de produção, TypeScript e ESLint aprovados. Ruff verificado com a configuração explícita `backend/pyproject.toml`.
- Playwright: **14 cenários aprovados** em desktop/celular, incluindo cadastro/edição/arquivamento, perfis, 404, upload binário PDF, rotação, importação CSV, preservação de revisão e Axe. A execução completa terminou em 57,4 segundos. Capturas conferidas visualmente.
- Dados de testes automatizados são sintéticos e usam SQLite temporário. Não há teste de login com a senha real do responsável nem criação de sessão por impersonação.

Comandos completos no README. Artefatos locais de teste ficam ignorados pelo Git.

## Pendências que impedem uma afirmação de “100%”

1. Receptor na Agenda, integração com a Plataforma, substituição do escritor no Portal e publicação pública dependem de outros projetos/contratos. Não se simula entrega nem se libera publicação sem esses componentes.
2. Política institucional de retenção, governança de publicação, monitoramento operacional e ensaio integral de restauração ainda precisam de homologação. O expurgo tem comando seguro, mas seu agendamento institucional não foi presumido.
3. Correção/remoção de beneficiários, associação de cadastro existente, conciliação entre fontes distintas, filtros analíticos avançados e refinamentos do modelo relacional continuam pendências do MVP já registradas. Não houve preenchimento por inferência nem migração automática de dados clínicos/Portal.
4. O PDF histórico tem grafias que exigem confirmação humana. A ação Melhor Visão/Mamanguape e 32 registros conferidos foram gravados em produção após autorização expressa, staging cifrado e backup verificado; 18 páginas aguardam confirmação da grafia. A prévia nominal fica privada e separada do commit. Não declarar todas as páginas importadas ou pessoas únicas sem resolver essa conferência.
5. O GitHub Actions permanece sujeito ao bloqueio de faturamento previamente identificado na conta. Verificações locais e build Vercel não são apresentados como execução bem-sucedida desse workflow.

As alterações solicitadas foram verificadas tecnicamente dentro do projeto; estes limites continuam explícitos. Testes aprovados não constituem certificação jurídica, aceite institucional integral ou prova de ausência absoluta de falhas.
