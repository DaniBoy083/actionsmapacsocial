# Mapa consolidado dentro do Actions Map — 27/10/2026

> **Histórico — recurso removido em 28/10/2026.** Por solicitação posterior do responsável, foram excluídos página, navegação, API, adaptadores, configuração e contratos do mapa dentro desta aplicação. As instruções abaixo descrevem o commit anterior e não devem ser usadas para configurar ou reativar o recurso. [Estado atual](CADASTRO_BENEFICIARIOS_E_SEGUNDA_VIA.md) e [auditoria](AUDITORIA_APLICACAO_E_PRINCIPIOS.md). O anexo original permanece preservado como referência.

## Decisão e escopo

O responsável confirmou nesta revisão: **“Neste Actions Map: adaptar o escopo do documento”**.
O [anexo original](plano_integracao_mapa_acoes_portal_institucional.md) foi preservado.
SHA-256: `AAED668E8E9008F9B42B2E9FBB5C557B54A9162773EB6E5A9903B8D1F0D1D074`.
Sua restrição original ao Portal foi substituída por essa decisão para esta implementação.
A nova página **Mapa de ações**, `/mapa-acoes`, é uma consulta interna autenticada
à Plataforma Consolidada. Não substitui o cadastro operacional em `/acoes` nem
transforma o Actions Map em uma página pública do Portal.

O fluxo de escrita continua Map → Agenda → Plataforma. A nova consulta é
Plataforma → visualização interna do Map. Não existe escrita circular,
consulta direta às tabelas da Plataforma ou fallback para os cadastros locais.
Nenhum outro repositório foi modificado. Não houve deploy, migração, importação,
alteração de credenciais existentes ou gravação institucional nesta revisão.

## Contrato conferido

Endpoint existente: `GET https://plataforma-consolidada-de-analise-d.vercel.app/api/v1/analytics`.
Headers privados: `Authorization: Bearer <credencial>` e `x-api-key`.
Contrato: envelope `versao="1"`, bloco `acoesInstitucionais`, `versaoCalculo="1.0"`.
A implementação de referência foi conferida nos arquivos locais do Portal
`backend/app/infrastructure/actions_contract.py`, `analytics.py`, suas fixtures/testes
e `docs/mapa-acoes-municipios-api.md` (documenta OpenAPI 1.2.0).
Isso comprova a compatibilidade com o contrato implementado localmente; a nova
instância do Actions Map ainda precisa de sua própria consulta real configurada.

Não existe coleção de títulos, descrições ou coordenadas individuais nesse contrato.
Portanto, o modelo sugerido `MapAction` foi adaptado a **agregados municipais**.
Nenhum título, endereço, localização individual ou data foi fabricado. A malha
SVG oficial do IBGE foi reutilizada do Portal em `src/data/paraiba-map.json`,
com origem, data de referência, URLs e hashes preservados. Um teste compara
todos os 223 códigos/nomes com o catálogo já usado pelo Actions Map.

| Origem | Saída privada / significado |
| --- | --- |
| `quantidadeAcoes` | `summary.action_count`, total global recebido |
| `quantidadeParticipacoes` | `participation_count`, separado de pessoas |
| `quantidadePessoasContempladas` | `people_count`, sem deduplicação entre ações |
| `quantidadeMunicipios` / `acoesSemData` | cobertura territorial e datas desconhecidas |
| `semDistribuicaoMunicipal` | ações/pessoas/participações sem distribuição por cidade |
| `municipios[].ibge/nome/uf` | código PB e nome conferidos no catálogo oficial |
| `municipios[].quantidadeAcoes` | presenças da ação em cada município; não somadas ao global |
| `acoesSemDistribuicao` | ações com vários municípios incluídas naquela cidade |
| `participacoesMunicipioUnico` / `pessoasContempladasMunicipioUnico` | somente subtotais atribuíveis a uma cidade |
| `geracao` | string decimal; inteiro Python/BigInt preservam precisão |
| `capturadoEmIso` / `expiraEmIso` | validade da exportação; não são datas das ações |

Exemplo exclusivamente sintético: duas ações globais podem produzir três presenças
municipais. Dez pessoas em ações de município único e sete sem distribuição
produzem 17 pessoas contempladas nas ações, sem duplicar as sete entre cidades.
Não são pessoas únicas entre ações ou fontes; não se somam aos atendimentos clínicos.

## Camadas e segurança

- Domínio: `PublishedMap`, seus DTOs e a porta `PublishedMapSource`.
- Aplicação: `ReadPublishedMap`, dependente somente da porta.
- Infraestrutura: contrato estrito em `platform_contract.py` e cliente HTTP/cache
  em `published_map.py`; nenhuma dependência de SQL ou acesso a tabelas clínicas.
- API: `GET /api/v1/mapa-acoes`, com revalidação institucional por
  `current_professional`, para Administração/Tecnologia. O endpoint não é anônimo.
- Next: BFF existente `/api/backend/mapa-acoes`; sem chaves da Plataforma no browser.
- Interface: MUI/TanStack Query, validação Zod da resposta, malha local, seleção por
  teclado, tabela, busca sem acentos, paginação e mensagens em português.

O cliente aceita somente HTTPS, hostname aprovado e caminho exato, sem query,
fragmento, usuário/senha embutidos, porta alternativa ou redirects. Token somente
em headers no backend. Deadline total de 20 segundos, resposta JSON descomprimida
até 2 MiB e rejeição de chaves JSON duplicadas. O BFF conserva orçamento de 30s;
a consulta do browser usa 25s e cancelamento.

O bloco de ações recusa campos extras, versões desconhecidas, dados pessoais,
inteiros negativos/fracionários/booleanos/strings ou acima de `2**53-1`, municípios
desconhecidos/repetidos, divergência de nome/UF, totais inconsistentes e datas
sem fuso, futuras ou expiradas. A saída é construída campo a campo; outros blocos
do envelope não são encaminhados ao navegador. Erros registram somente evento
e status HTTP, sem mensagem privada, corpo de resposta ou credencial.

Durante a revisão, respostas locais de erro da BFF (403/404/413/503) também foram
padronizadas com `Cache-Control: no-store`, `nosniff` e `no-referrer`, assim como
as respostas encaminhadas. Fixtures e servidores de testes desabilitam a nova
integração externa para não usar acidentalmente configuração real.

Contratos reproduzíveis em `docs/contracts/published-map.schema.json`,
`platform-actions-block.schema.json` e OpenAPI atualizado. Regeneração:

```powershell
.\backend\.venv\Scripts\python.exe scripts/export_contracts.py
```

## Atualização e falhas

Há cache em memória por processo, com uma consulta simultânea por instância do
adaptador. Sucesso: até 60s, limitado também à expiração da fonte. Falha comum:
30s. HTTP 429/503 respeita `Retry-After` em segundos ou data HTTP, entre 30s e
24h; na ausência de valor válido, 60s. Não há retry infinito na mesma requisição.
Uma geração inferior é rejeitada; conteúdo diferente na mesma geração também.
A referência de geração é mantida somente em memória, sem coordenação entre
instâncias ou persistência após reinícios.

O navegador atualiza periodicamente no intervalo indicado pela API e ao voltar
à aba, pausa o polling em segundo plano e permite atualização manual. Expiração
remove os dados da visualização; falha de atualização não conserva mapa antigo
como se fosse válido. Abas congeladas pelo navegador só podem atualizar a tela
quando voltarem a executar. A proteção de geração do navegador dura a montagem
do componente. Não há gravação em localStorage ou cache persistente de projeções.

A paginação limita a página selecionada ao novo tamanho da lista a cada atualização,
inclusive após retirada de municípios. O navegador também rejeita conteúdo
conflitante na mesma geração e usa intervalo de 30s após erro de rede.

`empty` significa exportação válida, comprovadamente vazia. Ausência de contrato,
configuração, autorização, timeout e dados inválidos são estados separados, com
totais indisponíveis, sem conversão para zero. Selecionar uma cidade sem registros
informa ausência **na exportação consultada**, sem afirmar ausência histórica.

A captura é apresentada em pt-BR, horário de Brasília. Busca municipal não altera
os totais globais. Não se promete tempo real: coleta da produtora, seu próprio
cache, até 60s de cache local, polling, rede e backoff compõem a latência.

## Configuração e operação

Acrescentar ao ambiente privado do **backend**, preservando os valores existentes:

```dotenv
CONSOLIDATED_ANALYTICS_API_BASE_URL=https://plataforma-consolidada-de-analise-d.vercel.app/api/v1/analytics
CONSOLIDATED_ANALYTICS_API_TOKEN=
```

Obter uma credencial de leitura própria com Tecnologia e preencher somente no
ambiente privado; não reutilizar a chave de envio à Agenda. Nunca usar prefixo
`NEXT_PUBLIC_`. Reiniciar o backend após configurar ou rotacionar a credencial:
a instância e seu cache são criados por processo. Não é necessária nova migração.

Diagnóstico somente leitura, sem imprimir chaves ou payload bruto:

```powershell
.\backend\.venv\Scripts\python.exe scripts/check_published_map.py
```

Código de saída 0: `available`/`empty`; 1: configuração, autorização, contrato
ou fonte indisponível. Imprime status, instante da consulta, geração e quantidade
de municípios. Resultado desta execução: **`ready=false`, `not_configured`**.
Não foi copiada credencial de outro sistema nem alterado `.env`/`.env.local`.

Homologação após configuração: iniciar backend/frontend conforme README; entrar
com perfil permitido; conferir dados e captura; comparar os totais com a API
aprovada; acompanhar uma alteração real pelo fluxo Map → Agenda → Plataforma;
confirmar retirada e expiração. Não arquivar ações reais para executar testes.
Deploy/ativação produtiva não fazem parte do commit solicitado nesta revisão.

Rollback do código: reverter o commit e remover a configuração opcional da consulta.
Sem nova tabela ou alteração de dados para desfazer. Falha na consulta não deve
reabrir o CRUD antigo do Portal nem ativar fallback para fonte não consolidada.

## Aceite adaptado e verificação

Implementados: leitura exclusiva da Plataforma; contrato/normalização; mapa municipal;
malha e design institucionais; cache/polling; loading/empty/error; ausência de dados
sem localização inventada; credencial privada; allowlist de saída; teclado/lista;
testes de contrato, rede, acesso e interface. Detalhes individuais de ações não se
aplicam ao contrato agregado e não foram simulados.

Resultados finais e limitações da revisão geral:
[Auditoria da aplicação e princípios](AUDITORIA_APLICACAO_E_PRINCIPIOS.md).
Pendente de ambiente externo: credencial própria, leitura real deste consumidor,
homologação institucional e comprovação de propagação ponta a ponta após deploy.

Os testes de navegador usam, por padrão, portas próprias **3310/8310**, configuráveis
por `ACTIONS_E2E_FRONTEND_PORT` e `ACTIONS_E2E_BACKEND_PORT`. A antiga porta 3100
estava ocupada por outra aplicação nesta máquina; nenhum processo externo foi
encerrado. O arquivo novo de testes do mapa reutiliza uma sessão obtida por login
real da identidade sintética em cada worker/projeto, evitando logins redundantes.
O limite de autenticação produtivo e suas verificações não foram alterados.
