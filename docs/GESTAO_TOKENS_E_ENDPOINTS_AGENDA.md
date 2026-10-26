# Tokens, endpoints e cURL para a Agenda Digital

Atualização de 26/10/2026. Esta entrega implementa a gestão na página **Conexão e integrações**, em `/tecnologia/conexao`. O código e a migração devem estar instalados antes de usar o recurso em produção.

## Fluxos disponíveis

| Fluxo | Credencial e finalidade |
| --- | --- |
| Map envia à Agenda | `AGENDA_SERVICE_TOKEN`, escopo lógico `acoes.resumos.write`, mantido no gerenciador institucional de segredos; outbox e confirmação de recebimento existentes |
| Agenda consulta o Map | Token `acm_…`, criado na página pelo profissional autorizado, escopo fixo `acoes.resumos.read`; somente saúde e resumos agregados |

Criar um token de leitura não troca a credencial de envio nem instala automaticamente um consumidor na Agenda. A nova API pode ser usada pelo servidor da Agenda para consulta e reconciliação, preservando **Map → Agenda → Plataforma → Portal**. Não configurar a Plataforma ou o Portal para acessar diretamente esta API do Map.

## Como usar a página

1. Entrar com conta institucional de tipo administrativo vinculada à equipe Tecnologia.
2. Na seção **Endpoints para a Agenda consultar o Map**, usar **Copiar endpoint** ou **Copiar cURL**. Os campos também permitem selecionar/copiar manualmente se a permissão de área de transferência estiver indisponível.
3. Em **Tokens de leitura para a Agenda**, clicar **Criar token**, informar nome, validade e confirmar a própria senha institucional.
4. Copiar o token ou **Copiar cURL com token** na janela de exibição única. Ela se fecha/oculta após dois minutos; o segredo também é removido do estado da página ao sair ou concluir.
5. Guardar a credencial no gerenciador de segredos/backend da Agenda. Depois, a listagem mostra somente identificação mascarada, escopo, status, validade e uso.
6. Para substituir, usar **Rotacionar** e confirmar a senha. A substituição e a revogação anterior são atômicas; atualizar o consumidor da Agenda com a nova chave. Falha na criação do substituto preserva a credencial antiga.
7. Para encerrar acesso, usar **Revogar**. As próximas requisições, inclusive páginas de exportações já abertas, exigem novamente uma credencial ativa. Requisições autorizadas antes da revogação podem concluir normalmente.

Validade padrão de 90 dias. A interface oferece **Nunca expirar**, 30, 90, 180 ou 365 dias, tanto na criação quanto na rotação. Na API, `validade_dias: null` significa sem expiração e retorna `expira_em: null`; omitir o campo mantém o padrão de 90 dias. Prazos numéricos continuam limitados a 1–365 dias; zero não é um marcador de validade ilimitada.

A opção sem prazo aparece como **Nunca expira** na listagem e na exibição única. Rotacionar um token permanente mantém essa opção selecionada, podendo escolher um prazo. Os tokens existentes conservam suas datas e estados, inclusive os já expirados ou revogados. Tokens sem prazo permanecem sujeitos à revogação, rotação, escopo de leitura, confirmação institucional e cota; contam no limite de 20 ativos. Tokens inativos não são recuperáveis; criar substituto. A listagem prioriza ativos e mostra até 100 registros de metadados. A exportação continua expirando em cinco minutos, e a exibição única do segredo em dois minutos.

## Endpoints e comandos

Origem canônica em produção: `https://actionsmapacsocial.vercel.app`. A página usa `FRONTEND_ORIGIN`, sem aceitar o host arbitrário da requisição como fonte dos comandos. Os caminhos expostos pelo Next.js são:

| Método/caminho | Uso |
| --- | --- |
| `GET /api/integracoes/v1/health` | Saúde mínima da integração e limite por minuto |
| `GET /api/integracoes/v1/acoes/resumos` | Nova exportação agregada consistente |
| `GET /api/integracoes/v1/acoes/resumos?exportacao_id=UUID&page=2` | Outra página da mesma exportação |

Comando para PowerShell/Windows, substituindo o marcador pela credencial guardada no servidor:

```powershell
curl.exe --fail-with-body --request GET 'https://actionsmapacsocial.vercel.app/api/integracoes/v1/health' --header 'Accept: application/json' --header 'Authorization: Bearer <TOKEN_DA_AGENDA>'
curl.exe --fail-with-body --request GET 'https://actionsmapacsocial.vercel.app/api/integracoes/v1/acoes/resumos' --header 'Accept: application/json' --header 'Authorization: Bearer <TOKEN_DA_AGENDA>'
```

Em Linux/macOS, trocar `curl.exe` por `curl`. Os exemplos persistidos na tela usam marcador; o comando com a chave real está disponível somente durante sua emissão. Cabeçalhos, tokens e comandos autenticados não devem entrar em logs, repositórios ou chamados públicos.

## Contrato da consulta

O envelope usa `schema_version: "1.1"` e `source: "ac-actions-map"`. Contém `exportacao_id`, `capturado_em`, `expira_em`, `checksum`, `page`, `page_size`, `total_pages`, `total_itens`, totais publicados, `escopo` e `items`. Cada item é o `Summary` 1.1 já documentado, com evento, ação, revisão, categoria, período opcional, municípios, quantidades e elegibilidade. Não inclui título/descrição interna, nomes, CPF, contatos, fichas, IDs individuais ou dados clínicos.

As revisões correntes incluem ações em revisão e arquivadas: `publicavel=false` e/ou `operacao=archive` permitem à Agenda identificar retiradas. Os totais do envelope incluem apenas ações publicadas e se repetem em todas as páginas; não devem ser somados entre páginas. Pessoas são distintas dentro de cada ação, sem deduplicação entre ações/fontes. Não distribuir contagens entre vários municípios por suposição. Datas desconhecidas permanecem nulas.

A exportação é obtida de revisão/evento em uma consulta SQL e materializada, de forma imutável, por **cinco minutos**. As páginas seguintes devem informar o mesmo `exportacao_id`, com o mesmo token. Alterações posteriores aparecem somente na próxima exportação. O checksum é SHA-256 de `items` completos, ordenados por ID de ação, em JSON UTF-8 com chaves ordenadas, caracteres Unicode preservados e separadores compactos `,`/`:`. A lista municipal é normalizada pelo contrato.

Limites: 100 itens por página, até 1.000 ações e 2 MiB no conjunto, até cinco exportações abertas por token e 60 requisições/minuto por token. Não há retorno parcial silencioso ao exceder capacidade. Uma exportação vazia válida tem `items=[]`, `total_itens=0`, `total_pages=1` e totais zero. A ação cujo evento corrente ainda usa contrato anterior precisa de nova revisão antes de exportar; isso gera 503 seguro, sem inventar evento ou omitir ação.

Exportações expiradas ficam inacessíveis e são removidas na próxima consulta de exportação bem-sucedida. A revogação remove as exportações da credencial. Para expurgo mesmo sem tráfego, o executor institucional deve executar a rotina de retenção correspondente; não foi criado cron implicitamente por esta entrega. Recibos de auditoria e hashes de credenciais revogadas permanecem para rastreabilidade, sujeitos à política institucional de retenção.

## Autorização e segurança

- Todas as rotas de gestão exigem sessão institucional revalidada, tipo administrativo e equipe Tecnologia no backend. As mutações também exigem origem exata, CSRF e confirmação da senha institucional existente.
- A confirmação reutiliza a consulta delegada de identidade e o verificador scrypt. Não cria tabela de senhas ou novo login. Há limite de cinco tentativas por profissional em dez minutos e limite compartilhado de endereço; a resposta não reflete a senha.
- O token tem 256 bits aleatórios, é mostrado uma vez e persistido somente como SHA-256, com prefixo/sufixo mascarados. Nunca há endpoint de recuperação do segredo.
- Senha e token emitido ficam somente em estado transitório do componente, fora do cache de queries/mutações, localStorage, sessionStorage e URLs. A senha é apagada após cada tentativa.
- O proxy de serviço encaminha somente Bearer/Accept, sem cookies, CSRF ou Set-Cookie. O proxy da sessão não aceita Bearer para acessar CRUD, beneficiários ou gestão de tokens. O token também não serve como sessão institucional.
- A cota usa linha de credencial e UPDATE condicional transacional; sua validação inclui validade e revogação. Não depende de contador em memória por instância.
- Respostas usam `Cache-Control: no-store`; erros são sanitizados. Não há CORS amplo nem rotas de escrita de ações para tokens de leitura.
- Criação, rotação, revogação, listagem, confirmação recusada e abertura da exportação têm auditoria sem segredo/payload nominal. Nomes dos tokens são identificações administrativas; não inserir dados de beneficiários.

Erros: 401 credencial/senha inválida; 403 perfil, origem ou CSRF; 404 token inexistente; 409 limite de tokens/rotação de inativo; 410 exportação expirada ou indisponível para a credencial; 422 parâmetros; 429 cota/limite de exportações; 503 armazenamento, contrato anterior ou capacidade. `Retry-After` acompanha os limites aplicáveis. Repetir uma consulta de serviço não contorna a revogação.

## Migração e instalação

Alembic **`0005_integration_tokens`**, após `0004_remove_drafts`, acrescenta somente `actions_map.acoes_map_credenciais_integracao` e `actions_map.acoes_map_exportacoes_integracao`. O runtime recebe SELECT/INSERT/UPDATE de credenciais, sem DELETE; SELECT/INSERT/DELETE de exportações. Não ganha privilégios sobre profissionais, equipes, tabelas clínicas, segredos de outras aplicações ou auditoria existente.

Alembic **`0006_nonexpiring_tokens`** permite `NULL` somente em `expira_em` das credenciais. Não atualiza registros existentes nem altera a expiração das exportações. O comando abaixo aplica até 0006, partindo de 0004, 0005 ou da própria 0006; o provisionamento inicial também usa a nova revisão.

SQLite de desenvolvimento cria as tabelas próprias como já faz o projeto. PostgreSQL exige a migração administrativa; startup e build não fazem DDL. Com a configuração administrativa privada já preparada neste ambiente:

```powershell
# Prévia: verifica revisão e preservação, sem aplicar a migração.
backend\.venv\Scripts\python.exe scripts/migrate_integration_tokens.py

# Aplicação administrativa: backup cifrado verificado e migração transacional.
backend\.venv\Scripts\python.exe scripts/migrate_integration_tokens.py --apply
```

O script usa `.env.local` administrativo e `artifacts/production-config.env` privado; requer TLS e a chave existente do backup, sem imprimir valores. Snapshot em REPEATABLE READ, trava, timeouts, conferência de ações/beneficiários e flags de RLS. Não rotaciona credenciais existentes. Aplicar antes de disponibilizar a nova página em produção. O push/deploy é responsabilidade do operador que solicitou este commit; nenhuma migração/deploy produtivo foi executado nesta entrega.

Em um **SQLite de desenvolvimento já existente**, `create_all` não altera a coluna antiga. Com o backend local parado, aplicar a atualização administrativa própria, que faz backup cifrado verificado e preserva credenciais/validade antes de alterar a coluna por batch:

```powershell
backend\.venv\Scripts\python.exe scripts/migrate_integration_tokens.py --sqlite-development --apply
```

Esse modo recusa produção e arquivos fora do workspace; não usa a conexão PostgreSQL institucional. SQLite novo já recebe o modelo nullable. A migração local pode ser repetida sem novo efeito. Não excluir o banco para atualizar.

Rollback: preservar as duas tabelas e usar uma versão compatível com a estrutura e os registros existentes. Não apagar hashes/auditoria ou executar downgrade destrutivo. A credencial antiga do envio e sua outbox continuam independentes.

Após emitir tokens permanentes na revisão 0006, manter uma versão do backend que reconheça `expira_em=null`. Para recuar a opção visual, ocultá-la mantendo esse suporte; a versão anterior que exigia data não é compatível com os novos registros. Não atribuir prazos artificiais, remover tokens ou mudar sua revogação automaticamente para viabilizar rollback.

## Verificação e limites do aceite

Testes cobrem criação/exibição única, hash persistido, RBAC, CSRF/origem, confirmação da senha e limites, expiração, rotação e revogação, isolamento do token, exportação congelada, retirada, 101 ações em duas páginas, exportação vazia, vinculação ao token e cota compartilhada. O navegador testa cópia, criação/rotação/revogação, acesso administrativo recusado e Axe em desktop/celular.

Uma verificação adicional usa PostgreSQL **local descartável**: aplica 0005/0006, confirma que a migração preserva o prazo/hash de um token existente, verifica grants, cria token sem expiração, exporta vazio, executa 70 consultas com 12 trabalhadores — 60 aceitas e 10 limitadas — e confere revogação. Um teste adicional verifica a migração do SQLite legado com backup e preservação dos registros. Não carrega `.env` nem acessa produção:

```powershell
backend\.venv\Scripts\python.exe scripts/check_integration_postgres.py --bin 'CAMINHO_DOS_BINARIOS_POSTGRESQL'
```

O script deixa o cluster fictício encerrado em `tmp/`, ignorado pelo Git. Somente o binário PostgreSQL é externo; o cluster é criado dentro deste workspace. Comandos gerais: `npm.cmd run lint`, `npm.cmd run typecheck`, `npm.cmd run build`, `npm.cmd run test:backend`, `npm.cmd run test:e2e` e Ruff com a configuração de `backend/pyproject.toml`.

Os controles técnicos desta alteração são verificáveis. A integração do consumidor na Plataforma/Portal, a política institucional de retenção/publicação, monitoramento contínuo e restauração integral continuam nos respectivos planos de aceite. Testes não permitem afirmar conformidade absoluta, certificação jurídica ou inexistência de falhas em toda a aplicação.
