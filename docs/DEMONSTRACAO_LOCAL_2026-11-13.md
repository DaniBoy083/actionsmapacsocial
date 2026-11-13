# Demonstração local e revisão de princípios — 13/11/2026

Escopo autorizado: modo de apresentação local, documentação, auditoria técnica,
correções verificáveis e commit. Sem deploy, migração de banco existente,
importação definitiva, mudança de identidade institucional ou assinatura digital.

## Evidência da fonte antes da implementação

Fonte aberta localmente nesta revisão:
`docs/references/FICHA MELHOR VISÃO PARA ANALISTA.xlsx`, XLSX, 41.860 bytes,
SHA-256 `74adf57b5d200d353dac5ae3626ce79a8b7c0a6a78cb8563c339785760f1f074`.
Uma aba (`Planilha1`), `A1:X25`, 382 células serializadas, 39 mesclas e uma imagem.
Leitura estrutural de todo o XML, strings, inventário do desenho e configuração de impressão;
inspeção visual local dos rótulos, ocultando valores preenchidos e imagem privada.
Papel A4 paisagem; sem versão/data de aprovação visível. Nenhum valor pessoal
foi usado como fixture, enviado a serviço externo ou registrado nesta entrega.

A matriz detalhada de [origem, finalidade, responsável, validação, obrigatoriedade,
sensibilidade e destino de cada campo](FASE_0_DESCOBERTA_2026-10-30.md#2-matriz-literal-de-campos)
foi comparada aos rótulos da fonte. Continua aplicável:

| Seção / células | Campos e responsável | Regras e destino |
| --- | --- | --- |
| Identificação, A8:N9 | Nome, CPF, nascimento, mãe, telefone e escolaridade; recepção conforme aprovação | Dados pessoais privados; CPF validado no cadastro, datas reais, ausências explícitas; obrigatoriedade não indicada pela fonte |
| Medidas, A12:N12 | Glicose, pressão, sangue; profissional autorizado | Saúde, cifragem segregada; finalidade, unidades e faixas pendentes; sem etiqueta/exportação nominal |
| Quadro ocular, A15:N17 | OD/OE: esférico, cilíndrico, eixo, DP; adição e lentes; profissional | Saúde, registro privado existente; sem inferir unidades, diagnóstico ou obrigatoriedade |
| Termo, A20:N25 | Data, município, profissional, registro, CPF profissional e assinaturas físicas | Não confundir CPF profissional com paciente; assinatura eletrônica em standby; aprovação física pendente |
| Resumo, O2:X3 | Identificação, escolaridade, medidas, local, data, responsável | Resumo nominal privado, não analytics público; “PESSÃO”, LOCAL e RESPONS. mantêm ambiguidades documentadas |

Os três campos institucionais (nome/título, número e autor de emenda/convênio)
não são campos pessoais da fonte: vêm do cadastro da ação por Administração/
Tecnologia, com leitura operacional e snapshots já existentes. Não redigitar
por paciente. A imagem privada não foi aprovada como marca; usa-se exclusivamente
`public/logo-ac-social.png`. Acervo escaneado, verso físico, interpretação clínica
e aprovação institucional não foram homologados nesta revisão. Não se acrescentam
campos clínicos nem modelos de prescrição/etiqueta com base nessas lacunas.

## Executar a demonstração

Na raiz, Windows, Node.js 22+ e Python 3.12:

```powershell
npm.cmd ci
py -3.12 -m venv backend/.venv
.\backend\.venv\Scripts\python.exe -m pip install -r backend/requirements-dev.txt
npm.cmd run demo
```

Abra `http://localhost:3300`, preencha um dos acessos pelos botões do login e
clique em Acessar plataforma. Administração: `admin@demo.invalid`; Tecnologia:
`tecnologia@demo.invalid`; senha **fictícia**, exclusiva deste processo:
`Demonstracao-local-2026!`. Não usar senha ou conta institucional no demo.

O launcher inicia Next em `127.0.0.1:3300` e FastAPI em `127.0.0.1:8300`. Para
outras portas: `npm.cmd run demo -- --frontend-port 3301 --backend-port 8301`.
Abra `localhost` na porta escolhida: a origem exata integra a proteção CSRF.
Portas ocupadas são recusadas; o launcher não encerra serviços preexistentes.
Não usar túneis, hosting ou exposição de rede para esta demonstração local.

Não há preparação de `.env`, migração ou autenticação pela base institucional.
As configurações conhecidas do backend, inclusive todos os aliases de conexão,
são sobrescritas no processo isolado, com chaves novas em memória e SQLite novo
em diretório temporário exclusivo. Não copia nem altera o banco operacional
existente, arquivos `.env` ou chaves do operador. Os testes conferem seus hashes
antes/depois. O launcher não herda credenciais, proxies ou opções de execução.

`Ctrl+C` encerra os dois processos criados e limpa seu diretório temporário.
Reiniciar restaura os exemplos com novos IDs, sessões e chaves. Encerramento
forçado do launcher pelo sistema pode deixar arquivos temporários cifrados;
eles não são reutilizados na execução seguinte. O cache `.next-demo/` é separado
de `.next/`, ignorado por Git/ESLint e não é um backup dos dados da demonstração.

## Conteúdo demonstrável e controles

- Três ações fictícias (João Pessoa, Campina Grande e Santa Rita), quatro locais,
  12 cadastros/participações; duas ações validadas e uma em revisão. Instrumentos
  fictícios e apoio total/parcial; nenhuma logo de terceiro inventada.
- Dois acessos administrativos fictícios com permissões reais de Administração
  e Tecnologia. Cadastro profissional de recepção não cria conta operacional.
- Um profissional clínico fictício, atribuições explícitas e um caso designado;
  campo textual de exemplo nos registros existentes. Todos os dados são
  sintéticos; indicação de habilitação é uma simulação descartável, sem validade.
  Administração não recebe acesso clínico automaticamente.
- Login, verificação de senha, sessões opacas, expiração, CSRF, rate limit,
  permissões no backend, cifragem e autoria continuam ativos. Cookie exclusivo
  `ac_actions_demo_session`; o runtime normal mantém `ac_actions_session`.
  A marcação visual vem do backend deste processo, sem `NEXT_PUBLIC_` ou bypass
  de autenticação. `APP_ENV=demo` sozinho não instala identidades fictícias.
- Banner no shell, identificação de sessão, aviso no login e identificação na
  segunda via impressa. A segunda via continua sendo cadastro geral, não laudo,
  prescrição assinada ou etiqueta de laboratório.
- PDF histórico real substituído por documento sintético de duas páginas.
  Upload externo desabilitado; usar a fonte sintética na importação. Endpoints
  de integração e sincronização recusados no backend e worker sem configuração
  de envio. O gate normal de publicação permanece ativo (503 sem integração).
- `backend/demo.py` é executável separado; nunca importado por `app.main` ou pelo
  adaptador institucional. Recusa `APP_ENV=production` e ambiente Vercel.
  Não adiciona contas/senhas em banco institucional ou contas locais do MVP.

Roteiro: entrar como Administração, mostrar painel/filtros, abrir uma ação,
mostrar metadados herdados, cadastros e segunda via identificada; sair. Entrar
como Tecnologia para mostrar atribuições, caso designado e registros existentes.
Não cadastrar pessoas reais, usar marcas não autorizadas ou apresentar exemplos
como atos clínicos válidos. O demo mostra os recursos existentes, incluindo seus
estados incompletos; não acrescenta fluxos clínicos presumidos.

## Auditoria dos princípios vinculantes

Revisão de código, contratos reais e testes locais; nenhuma leitura de registros
produtivos ou revalidação das quatro aplicações em produção. “Conforme nos
cenários testados” não equivale a homologação institucional ou conformidade absoluta.

| Princípio | Evidência / estado | Pendência ou limite |
| --- | --- | --- |
| Ficha original e fidelidade | XLSX conferido; matriz literal preservada; nenhum campo novo inventado | Aprovar modelo/verso e interpretações clínicas; acervo preenchido não foi reimportado |
| Ação, período, IBGE e N locais | CRUD/validação/versionamento/filtros SQL e testes existentes preservados | Homologação operacional real |
| Administração/Tecnologia; técnica só Tecnologia | Identidade institucional revalidada, backend restringe; demo conserva matriz e testes de negação | Identidades operacionais de recepção/profissionais ainda não homologadas; permanecem bloqueadas por padrão |
| Metadados emenda/convênio | Nome/número/autor na ação, revisões privadas e snapshot da segunda via; não redigitação por pessoa | Propagação para documento clínico/etiqueta final depende desses artefatos |
| Três marcas e autorizações | AC Social oficial; governo/clínica opcionais em total/parcial; testes existentes de saneamento/uso/publicação e snapshot | Validação de uso real pelo responsável e aplicação no futuro modelo clínico/etiqueta |
| Segregação clínica | Campos existentes cifrados, escopo identidade/profissional/ação/local/caso, designação e revisões; recepção/sem escopo negados | Competências, finalidade e fluxo completo de triagem/conclusão dependem de aceite clínico |
| Ficha e etiqueta coexistentes | Segunda via geral preservada e identificada no demo | Documento clínico final, etiqueta, emissão conjunta, rastreio de reimpressão/entrega ainda não implementados/homologados; bloqueiam MVP completo |
| Analytics interno | Admin/Tech, filtros institucionais/territoriais/período; participações e cadastros distintos com denominadores explícitos | Pessoas únicas reconciliadas entre ações, eventos de ficha/etiqueta/entrega e indicadores clínicos aprovados pendentes |
| Pipeline exato e nenhuma PII de paciente | Contrato 1.1 com allowlist/outbox/ACK; regressão verifica ausência de dados clínicos/pessoais; demo não transmite | Metadados novos exigem contrato coordenado e E2E Agenda → Plataforma → Portal, política pública de pequenos grupos e ranking sem duplicação |
| Login avançado e assinatura em standby | Nenhum novo mecanismo institucional/local de produção, gov.br, assinatura digital ou promessa de receita assinada | Evolução futura apenas em fase própria; assinatura física e responsáveis ainda exigem validação |
| LGPD, backup e rollback | Sem dados reais em fixtures; fontes/bancos ignorados; gate de privacidade; regressões locais de backup/restauração mantidas | Retenção/base legal e aceite institucional não podem ser inventados; topologia e restauração produtiva não foram revalidadas |
| Trabalho por fase / produção | Somente demo local e auditoria; nenhum deploy, migração de base existente, importação definitiva ou rotação | Revisão 0010 continua pré-requisito de futura disponibilização institucional desta linha de código |

**Resultado: conformidade global PARCIAL.** Para atingir o MVP integral ainda é
necessário implementar as fases clínicas/documentais e analíticas pendentes,
validar identidades operacionais com mecanismos existentes e homologar os
contratos nas consumidoras. O `AGENTS.md` e o plano v2.1 exigem aprovação de
campos, competências e fluxo físico antes dessas fases. Esta solicitação autoriza
código e commit, mas não substitui essas decisões clínicas/institucionais.

## Validação e reversão

Comandos de teste: `npm.cmd run lint`, `npm.cmd run typecheck`, `npm.cmd run build`,
`npm.cmd run test:backend`, `npm.cmd run test:e2e`, `npm.cmd run test:demo` e Ruff
nos arquivos Python alterados. Para preparar Chromium uma vez:
`npx.cmd playwright install chromium`. Testes usam somente dados sintéticos.
Os resultados finais desta execução são registrados abaixo.

- **207 testes de backend aprovados**, saída 0 (78,26 s), incluindo sete testes
  específicos do demo: isolamento de settings, credenciais, RBAC/CSRF, origem
  sintética, reinicialização, recusa de produção e porta ocupada. Arquivos de
  ambiente e banco operacional existente preservados por comparação de hashes.
- Next build, TypeScript e ESLint aprovados; Ruff nos cinco arquivos Python
  alterados/adicionados e `pip check` aprovados. Contrato OpenAPI regenerado
  sem consultar banco; novo sinal público de contexto não contém identidade.
- **30 cenários E2E existentes aprovados**, desktop/celular, saída 0 (2,8 min).
- **2 cenários do demo aprovados**, desktop/celular, saída 0 (27,3 s), com login,
  preenchimento de acesso, negações no BFF/backend, navegação, segunda via e logout.
  Axe sem violações nas regras A/AA selecionadas na tela de login do demo.
- Os dois PDFs sintéticos do demo foram conferidos pelo parser: **uma página A4**
  cada, aviso de demonstração presente; renderização final inspecionada visualmente.
  Houve correção do espaçamento exclusivo da impressão demo, sem reduzir a fonte.
  Isso não substitui teste com impressora/etiquetadora ou homologação clínica.
- A primeira execução de navegador revelou o indicador de desenvolvimento sobre
  Sair no celular; corrigido no demo, sem desativar erros do Next. Arquivos gerados
  foram excluídos de Git/ESLint/Prettier. Relatórios e capturas permanecem privados
  em `artifacts/`, `test-results-demo/` e `tmp/`, fora do commit.
- O sandbox Windows impediu encerrar certas árvores de subprocessos; as execuções
  finais de navegador e de isolamento foram feitas fora do sandbox em bases
  descartáveis. Corrigido o encerramento da árvore Python do fixture; processos
  remanescentes de testes anteriores foram identificados e encerrados. Pastas
  temporárias novas evitaram conflito de permissões com o cache pytest anterior.
- Avisos conhecidos: depreciação Starlette/httpx e `NO_COLOR`/`FORCE_COLOR` no
  Playwright; não representam falha funcional. Não foi feita atualização incidental
  de dependências.

Reversão local: encerrar o demo. A instância institucional não recebeu mudanças
de configuração ou dados. Para desfazer esta entrega de código, reverter somente
seu commit após conferir alterações posteriores; não executar downgrade do banco
ou retornar a uma API incompatível com a revisão 0010. O modo normal mantém os
comandos de dois terminais documentados no README e suas configurações existentes.

Próxima etapa: aprovar o modelo clínico/etiqueta e a matriz operacional antes de
implementar/homologar essas fases; validar contrato e critérios de publicação
com as consumidoras antes de qualquer novo envio de metadados.
