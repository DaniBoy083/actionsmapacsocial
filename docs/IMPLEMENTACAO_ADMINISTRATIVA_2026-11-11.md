# Implementação administrativa e auditoria — 11/11/2026

## Alcance e estado do repositório

Solicitação: conferir/sincronizar com main, implementar os documentos do próprio
repositório, excluir AC Auth/AC Core, documentar, testar e deixar commit para push
do responsável. `git fetch origin` executado antes das edições. A branch `main`
estava limpa em `dda4712339a4e012d9c411d3dd1c80d76be1b278`, igual a `origin/main`
(divergência `0 0`); nenhuma mesclagem foi necessária.

Esta entrega executa uma etapa administrativa do plano v2.1: ação, emenda/convênio,
marcas, histórico, propagação para a segunda via **geral existente** e filtros dos
indicadores existentes. Não equivale à implementação de todas as fases nem à
homologação do MVP ocular. As regras de fase única, segurança clínica e contratos
coordenados continuam vinculantes. Nenhuma alteração de AC Auth, AC Core, adaptador
institucional de identidade, sessão ou novo login local foi realizada.

**Resultado de conformidade global: PARCIAL. Piloto clínico NÃO LIBERADO.**
As pendências abaixo são requisitos reais; não foram marcadas como concluídas para
atender uma declaração de “100%”.

## Evidência da fonte antes das mudanças dependentes

- Fonte localizada e aberta: `docs/references/FICHA MELHOR VISÃO PARA ANALISTA.xlsx`.
  Uma aba `Planilha1`, área `A1:X25`, 39 mesclas, uma imagem incorporada; A4 paisagem,
  sem versão/data de aprovação visível. SHA-256 confirmado nesta execução:
  `74adf57b5d200d353dac5ae3626ce79a8b7c0a6a78cb8563c339785760f1f074`.
- O XML da aba foi percorrido integralmente para estrutura; a saída conservou
  somente células de rótulos permitidos. Conferência visual da prévia sanitizada
  `tmp/fase0/ficha-rotulos.png`, área completa. Valores preenchidos e imagem
  incorporada não foram enviados ao contexto nem reutilizados. Essa imagem não
  constitui branding aprovado. O original permaneceu intacto e fora do Git.
- Seções confirmadas: identificação do programa; dados do beneficiado (nome, CPF,
  nascimento, mãe, fone, escolaridade); exames complementares (glicose, pressão,
  sangue); exame ocular (OD/OE, esférico, cilíndrico, eixo, DP, adição e lentes);
  termo (data, município, identidade/registro/CPF do profissional, declaração,
  carimbo/assinaturas); resumo nominal `O1:X3`.
- A [matriz literal por célula](FASE_0_DESCOBERTA_2026-10-30.md#2-matriz-literal-de-campos)
  continua a referência de origem, responsável, sensibilidade, destino e lacunas.
  Não se confundem mãe/responsável, CPF profissional/paciente, DP/DNP ou município
  de residência/evento/termo. Saúde permanece de preenchimento profissional,
  sem nova coleta neste incremento; não foi adicionada ao DTO geral.
- O acervo `docs/data/ilovepdf_merged.pdf` foi localizado. A evidência histórica
  de 30/10 descreve 50 páginas sem camada textual e a pendência da página 34.
  **O PDF não foi reprocessado nesta etapa administrativa**, nem se afirma nova
  revisão integral dos valores, assinatura, imagem incorporada ou documento físico.
  Esta entrega não usa o acervo para implementar campos clínicos.
- Pesquisados `docs/` recursivamente, incluindo `docs/references/` e `docs/data/`;
  `docs/reference/`, `data/` e pastas de anexos na raiz não foram encontradas.
  O usuário confirmou os documentos do repositório e o uso da ficha localizada.
  Isso não forneceu unidades/faixas, competências ou dimensões de etiquetas que
  não constam da fonte. Não se substituiu essa lacuna por dados inventados.

## Comportamento implementado e origem dos campos

| Campo/objeto | Origem, responsável e regra | Destino e privacidade |
| --- | --- | --- |
| Modalidade de apoio | Adendo 30/10; Administração/Tecnologia; TOTAL/PARCIAL ou nulo quando desconhecido | Ação, histórico, comprovante geral; não inferir valores de verba |
| Instrumento: tipo, nome/título, número, autor | Adendo 30/10; cadastro uma vez na ação; texto limitado a 160/80/160; número preserva zeros; autor opcional | API privada, histórico e segunda via; não pedir redigitação por beneficiário |
| Ausência de instrumento | NAO_INFORMADO com dados vazios e divulgação desativada; tipo explícito quando há dados; campos ausentes não são inventados | Relatórios distinguem ação sem instrumento identificado |
| Órgão e clínica | Adendo 30/10; nomes opcionais, até 160 caracteres cada; mesmos dois slots em TOTAL/PARCIAL/nulo | Administração/Tecnologia e comprovante geral privado; não representa cadastro N:N completo de parceiros |
| Uso e divulgação de marcas | Permissões separadas, estritamente booleanas e desativadas por padrão; imagem exige parceiro nomeado e uso autorizado | Ator/data vinculados à revisão; autorização declarada pela equipe, sem supor verificação jurídica automática |
| Divulgação do instrumento | Opt-in distinto de aprovação/publicação da ação; exige nome do instrumento | Registro privado para futura revisão; não ativa contrato 1.2 nem publica campos novos |
| Logo AC Social | `public/logo-ac-social.png`, asset oficial do projeto | Fixo no cabeçalho do comprovante geral; não substituível pelo formulário |
| Logos opcionais | PNG/JPEG estático, 64–2048 px por lado, entrada e PNG saneado até 256 KiB; rejeita SVG/HTML, arquivos inválidos, animados e dimensões excessivas | Derivada PNG reencodada sem EXIF/comentários/perfis/conteúdo após o arquivo; privada no banco do Map, sem URL arbitrária ou original publicado |
| Identificação da segunda via | Capturada automaticamente na primeira emissão após este incremento; ID/nome/revisão da ação e metadados | `acoes_map_participacoes.documento_institucional`; reimpressão preserva emenda e IDs das marcas anteriores, sem nova participação |

Os três campos do instrumento são **institucionais**, não extraídos de uma pessoa
da ficha XLSX. Logo/autor podem identificar instituições/pessoas profissionais;
devem conter apenas conteúdo administrativo autorizado, nunca cadastros nominais
de beneficiários. A allowlist de chaves não classifica automaticamente texto livre.

### Persistência e autorização

- `Action.institucional`: JSON validado pelos DTOs estritos em
  `backend/app/domain/institutional.py`. Campos extras aninhados são rejeitados.
- `acoes_map_marcas`: PNG privado imutável, ação/slot, SHA-256 e dimensões.
  Apenas SELECT/INSERT concedidos ao runtime na migração PostgreSQL.
- `acoes_map_revisoes_institucionais`: ação + versão, metadados/IDs das marcas,
  ator que registrou a captura e data. Também apenas SELECT/INSERT no runtime.
  Operações que só mudam status/participações não geram uma edição administrativa;
  versões registradas são listadas explicitamente, sem inventar versões ausentes.
- A regra de privilégios é compartilhada pela revisão 0007 e pelo provisionamento.
  Revoga alteração/exclusão/truncate e outros privilégios de escrita indevidos nas
  duas tabelas novas, inclusive após concessões gerais/default privileges. O script
  de provisionamento foi corrigido no código, mas não executado contra produção.
- Edições com versão desatualizada recebem 409. Dados e imagens são transacionais:
  imagem inválida desfaz a criação/edição inteira. PATCH de cliente anterior que
  omite `institucional` preserva os metadados existentes; `{}` os limpa explicitamente.
- `GET /api/v1/acoes/{id}/marcas/{logo_id}` valida ação/posse no servidor, retorna
  PNG e `no-store`, com auditoria. Não há endpoint anônimo ou URL de storage pública.
- `GET /api/v1/acoes/{id}/institucional/versoes/{versao}` consulta histórico privado.
  O BFF permite somente esses caminhos adicionais, com os controles existentes.
- Rotas continuam restritas às duas equipes institucionais validadas pelo backend.
  Recepção/profissional ainda sem identidade operacional validada recebem negação;
  **não foram habilitados** mediante permissão administrativa genérica.
- A segunda via conserva somente o snapshot **administrativo**. Dados pessoais
  continuam representando a revisão atual corrigível do cadastro, com indicação
  explícita no impresso. Não é snapshot clínico, prescrição ou documento assinado.
  Emissões anteriores à migração não têm histórico reconstruído por suposição.
- A impressão espera as três imagens carregarem; falha de marca impede imprimir
  silenciosamente um cabeçalho incompleto. Abrir/reabrir não registra entrega nem
  comprova impressão física.

### Indicadores e contratos

Listagem: filtros por nome/número de instrumento, autor, órgão, clínica e apoio,
combinados aos filtros anteriores. Painel: também ID de ação, município/local do
evento e período do **início da ação**, inclusive limites. Ações sem data ficam
fora de recorte temporal; sem filtro continuam incluídas. Arquivadas ficam fora
do painel. Filtros textuais institucionais são parametrizados com escape literal
de curingas SQL. O filtro de local compara o nome normalizado (acentos/caixa).

Ações contam uma vez no total e uma vez por município elegível; soma municipal
pode superar o total. Participações de ação multilocal só entram no recorte
territorial quando o índice do local corresponde. Participações sem local são
informadas separadamente e excluídas ao filtrar município/local. Cadastros distintos
contam IDs de beneficiários no recorte; **não comprovam pessoas únicas conciliadas
entre ações**. Não se unifica por nome/CPF. Não há contagem clínica fabricada como zero.

OpenAPI e `docs/contracts/action-registration.schema.json` foram gerados dos DTOs.
As respostas privadas de ficha geral acrescentam a identificação institucional.
O item de integração **1.1** e o envelope de exportação anterior não foram ampliados.
Nenhum nome de instrumento, marca, paciente ou conteúdo de cadastro é acrescentado
à outbox por este incremento, mesmo quando a flag de divulgação é verdadeira.
O pipeline permanece Actions Map → Agenda → Plataforma → Portal. A versão 1.2
continua dependendo de leitores compatíveis e homologação coordenada; flags de
autorização locais não fazem a Agenda aceitar campos extras.

## Migração, operação e rollback

Nenhum banco real/local de beneficiários, produção, migração definitiva, importação,
segredo ou configuração institucional foi alterado nesta execução. Só bancos
descartáveis de teste receberam o novo schema. Não houve deploy nem push.

1. Instalar as dependências atualizadas, incluindo Pillow 13.0.0, antes de executar
   o backend. Os manifests `requirements.txt` e `pyproject.toml` estão alinhados.
2. SQLite de desenvolvimento existente: parar os escritores. A prévia
   `.\backend\.venv\Scripts\python.exe scripts/migrate_institutional_metadata.py`
   não grava. O mesmo comando com `--apply` faz backup cifrado verificado e migração
   aditiva/idempotente exclusivamente do banco local dentro do workspace. Obter
   a chave pelo processo institucional, nunca publicá-la junto ao backup.
   Este comando de aplicação **não foi executado contra o banco real**.
3. PostgreSQL: foi preparada `0007_institutional_metadata`, após 0006. Requer backup
   consistente, revisão de privilégios, teste em staging e liberação de produção
   próprios. **Aplicar 0007 antes de servir este código no banco existente**.
   Não há DDL no startup de produção; este documento não autoriza executá-lo.
4. Não retropreencher instrumentos, autoria ou logos em ações antigas. Ausências
   permanecem explícitas. Primeiro comprovante geral emitido após a migração
   captura os metadados então existentes; não recupera conteúdo anterior perdido.
5. Rollback: pausar mudanças/emissões que dependam dos novos metadados, retornar a
   código compatível e preservar colunas, marcas, revisões e snapshots. O downgrade
   automático destrutivo é recusado. Código anterior ignora os novos metadados e
   não deve reemitir comprovantes prometendo o novo cabeçalho/histórico. Restaurar
   backup somente com reconciliação de gravações e decisão operacional própria.

## Validação nesta execução

- Backend completo: **139 aprovados** (114 anteriores + 25 novos); dados sintéticos.
  Cobertura nova: slots nas três situações de apoio, opcionais ausentes, número
  textual, permissões, CSRF, IDOR de marca/slot, validação estrita, formatos e
  dimensões, saneamento, rollback de transação, edição legada, revisões, snapshots,
  reemissão sem duplicação, filtros/ausências e migração SQLite idempotente.
- SQLite: backup cifrado decifrado e restaurado em banco sintético de memória;
  nome anterior e ausência das novas colunas conferidos no backup, dados
  preservados após aplicação e uma só cópia em duas execuções.
- PostgreSQL 18 local descartável:
  `scripts/check_institutional_postgres.py --bin "C:/Program Files/PostgreSQL/18/bin"`.
  Revisão 0007 aplicada duas vezes, CRUD/CAS/JSON/histórico sob runtime e
  UPDATE/DELETE das duas tabelas imutáveis recusados. A primeira tentativa
  de initdb foi impedida pelo sandbox Windows; teste concluído em execução
  autorizada fora dele, com servidor temporário encerrado ao final.
- Lint, TypeScript, build, Ruff e `pip check` aprovados na execução. TestClient
  apresenta aviso de depreciação de httpx/Starlette já existente; nenhum erro.
- E2E completos: **26 aprovados**, desktop e celular, incluindo seis novos cenários
  de cadastro TOTAL/PARCIAL, duas marcas opcionais, segunda via/snapshot e filtros.
  A primeira rodada teve 25 aprovados e uma falha por acumular logins/reauthorizações
  dos testes no limite do mesmo IP sintético. O servidor exclusivo de testes agora
  simula um cliente por contexto de navegador via cookie efêmero; preserva o rate
  limit real dentro de cada cenário. Nenhum controle de produção foi afrouxado.
  A repetição completa terminou com código 0. No sandbox Windows, os processos
  próprios dos servidores E2E precisaram ser encerrados explicitamente após os
  cenários para concluir o teardown do Playwright.
- Capturas sintéticas `artifacts/institutional-Total-desktop.png` e
  `artifacts/institutional-Parcial-mobile.png` conferidas visualmente em mídia de
  impressão simulada: marcas, campos, quebra dos textos e assinatura legíveis,
  sem cortes observados. Não comprova paginação A4 física, impressão real,
  acessibilidade por tecnologia assistiva humana ou qualquer etiqueta.
- Gate de privacidade do staging e de todos os caminhos rastreados: **PRIVACY_OK**.
  `git diff --cached --check` aprovado. Originais privados, capturas, bases e backups
  continuam ignorados; nenhum deles entrou no commit. O gate de segredos locais
  complementa a revisão do diff, sem prometer detecção universal de conteúdo privado.
- Referência técnica do saneamento:
  [documentação oficial de Pillow](https://pillow.readthedocs.io/en/stable/reference/Image.html).

## Pendências que impedem concluir o pedido integral e liberar o piloto

| Requisito do plano | Estado e dependência concreta |
| --- | --- |
| Cadastro/atribuição e habilitação de profissionais | Não implementados; contas operacionais existentes/escopos precisam ser definidos e validados sem abrir novo login em standby |
| Triagem, atendimento e ficha clínica segregada | Não implementados; fonte disponível, mas unidades, faixas, obrigatoriedade, finalidade e competências continuam sem definição na ficha/matriz |
| Ficha clínica + etiqueta, impressão conjunta e entrega | Não implementadas; precisa atendimento clínico seguro, layout/conteúdo e dimensões da etiqueta aprovados, validação física e fluxo profissional |
| Pessoas únicas conciliadas e ranking emenda/autor | Não implementados; exige identidade/instrumentos estáveis, reconciliação e denominadores aprovados; somar participações não resolve |
| Indicadores clínicos, fichas, etiquetas e entregas | Não existem no domínio atual; não se anunciou valor zero ou cobertura completa |
| Novos metadados no pipeline completo | Contrato 1.2 não ativado; os repositórios/serviços consumidores não foram alterados nem homologados nesta tarefa |
| Banco independente e privilégios do ambiente real | Modelo e testes locais não comprovam a topologia/grants produtivos; nenhuma inspeção produtiva nesta execução |
| Retenção, restore do serviço real, papel e aceite institucional | Pendentes de responsáveis/ambiente próprios; teste de backup sintético não é homologação operacional |
| AC Auth, AC Core, assinatura digital, gov.br e login local avançado | Fora do escopo por instrução expressa e/ou standby do plano |

Próxima etapa: concluir as definições de modelagem/segurança e autorizar a fase
clínica delimitada, com a ficha original e matriz aprovadas, identidade mínima
validada por ação/caso, sem importar beneficiários nem publicar dados como atalho.
