# Auditoria técnica da aplicação e princípios — 27/10/2026

## Escopo e conclusão

Revisão do Actions Map e implementação do anexo adaptado ao repositório por
confirmação do responsável. Critérios: especificação específica, decisões
posteriores de publicação/importação, branding, arquitetura, privacidade e
[plano adaptado](MAPA_CONSOLIDADO_ACTIONS_MAP.md). Os guias locais do pacote
Next 16.4.3 foram lidos antes das alterações de código.

Os controles abaixo têm evidência técnica local. **Não há evidência para declarar
a aplicação inteira “100% absolutamente” conforme**, nem para marcar como
concluídas homologações institucionais ou a integração real ainda não configurada.
Nenhum critério foi removido para produzir aprovação aparente.

## Matriz de princípios

| Princípio | Evidência conferida / resultado |
| --- | --- |
| Fronteiras do domínio | Cadastro próprio de ações/beneficiários; nenhum tracking clínico novo ou correlação nominal entre fontes. Consulta consolidada apenas de agregados |
| Identidade única e mínimo privilégio | Login sem escolha de tipo/equipe; scrypt institucional e revalidação por requisição. API do mapa usa a mesma proteção. Teste bloqueia ausência de sessão e revogação do vínculo |
| Tecnologia exclusiva | Endpoints existentes de diagnóstico/tokens continuam protegidos também no backend; regressão mantida |
| Arquitetura | Novo fluxo tem DTO/porta no domínio, caso de uso, adaptadores de contrato/HTTP e apresentação separados. Sem SQL em aplicação/domínio novos |
| Código/contratos | TypeScript estrito, validação Pydantic/Zod, OpenAPI/schemas reproduzíveis, nenhuma dependência nova ou API Next presumida |
| Fonte institucional | Mapa lê somente a API da Plataforma. Cadastro e outbox continuam Map → Agenda; não há atalhos de banco nem fallback local no mapa |
| Integridade analítica | Pessoas/participações/presenças municipais distintas; subtotais não distribuídos preservados; datas desconhecidas explícitas; geração decimal sem perda de precisão |
| Segredos e transporte | Token exclusivo no servidor, HTTPS/host/caminho aprovados, sem redirects, deadline e limite de corpo; nenhuma chave existente copiada |
| Minimização/entrada não confiável | Allowlist de campos e catálogo de 223 municípios; extras pessoais, contagens inválidas, duplicações e exportações expiradas recusados; nomes da malha local |
| Falhas e observabilidade | Cache limitado à validade, single flight por processo, 429/503 com backoff, falha distinta de zero e logs sem corpo/segredo; diagnóstico CLI sanitizado |
| Governança editorial | Cadastro operacional/revisão/publicação existentes mantidos. A consulta interna não concede aprovação editorial nem publica novos dados ao público |
| Privacidade | Mapa autenticado, sem listas de beneficiários, prontuários ou novas tabelas; imagens/PDFs/dados/segredos continuam fora de fixtures e Git |
| UI/UX e branding | MUI, tokens vermelho/vinho, shell/footer existentes; mapa municipal oficial, legenda textual, seleção, tabela, busca e paginação |
| Acessibilidade | Alternativa textual ao mapa, teclado/foco, labels e estados anunciados. Testes desktop/mobile e Axe registrados abaixo; avaliação manual com tecnologias assistivas continua separada |
| Operação e mudanças | Sem migração/deploy/gravação produtiva; configuração opcional documentada, diagnóstico e rollback de código. Anexo original preservado |

## Correções desta revisão

1. Implementada a consulta consolidada que não existia no Actions Map, com
   adaptação explícita do contrato real agregado ao plano originalmente do Portal.
2. Acrescentados controles de validade, geração, integridade territorial/contábil,
   minimização, tempo/tamanho e concorrência, com cenários sintéticos de falha.
3. Padronizados headers privados também nas falhas locais da BFF.
4. Adicionados contratos gerados, diagnóstico sanitizado e testes isolados da rede
   institucional; mantidas as verificações e permissões existentes.
5. Criado este documento, corrigindo o destino de auditoria já referenciado pelo
   branding; registros históricos apontam para o estado atual, sem apagar pendências.
6. Corrigida a aplicação dos estilos da legenda/tabela no loader CSS existente,
   identificada na inspeção visual; verificados os estilos efetivamente computados.
   Paginação passa a acompanhar redução da lista após atualização.
7. Isoladas as portas dos testes (3310/8310, configuráveis) e eliminados logins
   redundantes dos novos cenários por reutilização de sessão sintética legítima.
   O rate limit da aplicação não foi aumentado, desativado ou contornado no servidor.

## Evidências executáveis

| Verificação local | Resultado |
| --- | --- |
| `npm.cmd run test:backend` | **133 aprovados**: 77 existentes e 56 novos; banco descartável |
| `npm.cmd run test:e2e` | **26 aprovados**, desktop/celular, sem retries; relatório final com saída 0 |
| `npm.cmd run build` | Build Next de produção aprovado, incluindo TypeScript e `/mapa-acoes` |
| `npm.cmd run typecheck` / `npm.cmd run lint` | Aprovados |
| Ruff com `--config backend/pyproject.toml` | Aprovado em aplicação, testes e scripts |
| `python -m pip check` | Sem incompatibilidades instaladas |
| Diagnóstico `scripts/check_published_map.py` | `ready=false`, `not_configured`; saída 1 esperada sem credencial |
| Inspeção de bundle | 35 arquivos JavaScript, dez valores secretos locais procurados, nenhum encontrado |
| Fonte cartográfica | Todos os 223 códigos e nomes iguais ao catálogo existente, por teste automatizado |

Axe verificou regras WCAG A/AA selecionadas nos fluxos existentes e no mapa,
sem violações na rodada final. Cenários novos incluem autenticação/revogação,
dados privados/invalidade, timeout/HTTP 301/401/403/404/429/500/503, JSON duplicado,
limite de resposta, cache/concorrência, precisão/conflito de geração, vazio,
expiração, teclado, busca e paginação após retirada. Layout verificado também
em largura de 320 px, aguardando a conclusão da transição da sidebar. Capturas
desktop/celular foram de fato inspecionadas; legenda e tabela corrigidas estão
visíveis e com estilos computados conferidos.

As rodadas anteriores expuseram conflito da porta 3100, quota de logins repetidos
e verificações durante animações. A sessão sintética passou a ser reutilizada
pelos testes do mapa; os testes aguardam a remoção real do menu e o fim do ajuste
responsivo antes das asserções. Nenhuma regra Axe ou proteção foi desativada.
O encerramento automático da árvore de processos pelo Playwright ficou aguardando
neste sandbox Windows; após os 26 casos aprovados, somente os dois servidores
iniciados pela própria suíte foram encerrados com `Stop-Process`. O runner então
finalizou normalmente com **26 passed, exit code 0**. Não foram encerrados serviços
do usuário. Isso deve ser considerado ao reproduzir o teste neste mesmo sandbox.

Há um aviso existente de depreciação httpx/Starlette no TestClient; a suíte passa,
mas a atualização futura deve ser tratada separadamente. Não houve auditoria
independente de segurança ou consulta de vulnerabilidades nesta revisão.
Fixtures são sintéticas; bancos descartáveis. Capturas `artifacts/published-map-*`
e relatório `artifacts/e2e-results.json` ficam fora do Git. A varredura de segredos
locais do staging também foi executada antes do commit.

Na preparação do commit, o Git encontrou falta de espaço no disco. Foram removidos
somente os caches reconstruíveis `.next/cache` e `tsconfig.tsbuildinfo`, após as
verificações. Código, contratos, documentos, bancos, segredos e backups foram
preservados. A limpeza não altera o código validado; esses caches serão recriados
pelos próximos comandos de desenvolvimento/build.

O anexo original foi incluído sem alteração de conteúdo, com SHA-256 registrado
no guia. `git diff --cached --check` sinaliza apenas os dois finais de linha com
dois espaços desse anexo (quebras explícitas de Markdown); foram preservados para
manter o documento recebido intacto. A varredura de privacidade do staging passou.

## Limites e pendências reais

- A nova consulta está **sem credencial própria configurada** neste ambiente.
  Diagnóstico retornou `not_configured`. Não foi executado teste real desse novo
  consumidor contra a Plataforma nem deploy/validação de propagação produtiva.
- Cache e referência de geração são por processo; não constituem registro durável
  compartilhado entre instâncias. O cliente mantém sua referência por montagem.
- Políticas institucionais de publicação de grupos pequenos, retenção, atendimento
  aos titulares e aceite de privacidade não são decisões que o código possa homologar.
  Não se presume aprovação pública pela disponibilidade de agregados autenticados.
- Agendamento/monitoramento do expurgo e retentativas, restauração integral de
  backups, validação de infraestrutura/grants e operação real precisam de evidências
  próprias. Nenhum cron, backup ou deploy foi apresentado como executado aqui.
- Permanecem as evoluções do MVP já registradas: correção/remoção/associação de
  beneficiários existentes, conciliação supervisionada entre fontes, filtros
  analíticos avançados e evolução relacional dos locais. São requisitos funcionais
  além da adaptação do mapa; não foram declarados prontos nesta revisão.
- Fluxos antigos de beneficiários/importação ainda compõem adaptadores em rotas;
  sua separação adicional em portas/casos de uso permanece melhoria arquitetural.
- Execução do CI remoto, revisão independente, dispositivos/tecnologias assistivas
  reais e desempenho de campo não são comprovados por build/Axe locais.

Esses itens permanecem abertos e revisáveis. A passagem dos testes comprova os
cenários executados e não representa garantia absoluta de ausência de falhas.
