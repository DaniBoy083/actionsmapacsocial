# Fase 0 — descoberta da ficha e do sistema

Data: 30/10/2026. Base inicial: `df84320`. Fontes vinculantes: `../AGENTS.md`,
`../PROMPT_INICIAL_SOL.md` e o adendo de 30/10 do
[plano v2.1](PLANO_ACTIONS_MAP_GPT61_SOL.md).

## Resultado e alcance

A ficha foi localizada e seus campos foram lidos. O sistema atual implementa o
cadastro geral anterior; **não implementa o MVP ocular de 30/10 por completo**.
O prompt inicial determina “apenas na Fase 0” e “Não executar implementação”.
Esta entrega produz descoberta, auditoria, proposta e critérios de aceite.
Não implementa o domínio clínico, não altera produção e não importa pessoas.
A correção independente de privacidade retira uma fonte preenchida do índice Git,
preserva o original no disco e acrescenta um gate verificável.

Não há declaração de conformidade absoluta. Leitura de formulário, testes de
software e homologação clínica/institucional são evidências distintas. Veja o
[plano de execução e aceite](PLANO_MVP_E_ACEITE_2026-10-30.md) e a
[auditoria atual](AUDITORIA_APLICACAO_E_PRINCIPIOS.md).

## 1. Evidência de leitura dos anexos

### Ficha para analista

- Caminho real relativo à raiz: `docs/references/FICHA MELHOR VISÃO PARA ANALISTA.xlsx`.
- Formato: XLSX, 41.860 bytes; uma aba, `Planilha1`; área utilizada `A1:X25`.
- SHA-256: `74adf57b5d200d353dac5ae3626ce79a8b7c0a6a78cb8563c339785760f1f074`.
- Identificação visível: “MELHOR VISÃO”. Não há versão/data de aprovação visível
  no formulário; a data de um exemplo preenchido não é versão do modelo.
- Ficha em `A1:N25`; resumo nominal em `O1:X3`, com cabeçalhos em `O2:X2`.
  A aba contém 382 células serializadas, 56 strings compartilhadas, uma imagem
  incorporada e 39 intervalos mesclados. Não foram encontradas outras abas.
- `pageSetup`: papel A4, orientação paisagem; não há área de impressão definida
  em `definedNames`. Isso não comprova que a ficha e o resumo caibam em uma página.
- Inspeção: leitura do XML da aba inteira, strings, mesclas, configuração de
  página e desenhos; renderização da área completa após ocultar todos os valores
  preenchidos e a imagem incorporada. Os rótulos e sua posição foram conferidos
  visualmente. Nenhum nome, CPF, resultado de exame ou assinatura foi transcrito
  para esta documentação.
- Os valores de exemplo não são uma autorização para migração nem fixtures.
  O arquivo estava versionado; esta revisão o retira do índice e o mantém no mesmo
  caminho local, com o mesmo hash. Um novo clone precisa obter a fonte por canal
  institucional privado. O histórico Git anterior ainda precisa de avaliação pelo
  responsável; este commit não reescreve o histórico nem comprova exclusão remota.
- A imagem incorporada é um JPEG de 776×497 (25.722 bytes), diferente do PNG
  oficial do projeto. Seu conteúdo foi ocultado na revisão para evitar divulgar
  um anexo não aprovado; **não foi homologado como logo nem reutilizado**. A
  conferência privada dessa imagem permanece no aceite da versão oficial.

### Acervo digitalizado

- Caminho real: `docs/data/ilovepdf_merged.pdf`.
- PDF, 252.680.759 bytes; SHA-256
  `9a9ede3f068533540aa600eae2d5f6310832ccc432949788d48cce5947066ac6`.
- 50 páginas, uma imagem por página, **nenhuma página com camada textual**.
- Identificação impressa: Programa “Melhor VISÃO”. Trata-se de fichas preenchidas,
  com disposição diferente da planilha; não há versão oficial comum comprovada.
- Todas as 50 páginas foram abertas/renderizadas localmente. OCR do Windows
  (`pt-BR`) foi executado localmente; apenas palavras de uma lista de rótulos
  permitidos foram conservadas para inspeção visual em cinco folhas de contato,
  páginas 1–10, 11–20, 21–30, 31–40 e 41–50. Os demais pixels foram ocultados.
- Houve correção de orientação para reconhecer rótulos nas páginas 1, 27–33,
  35 e 36. A página 34 forneceu somente três palavras permitidas; **sua leitura
  literal integral permanece pendente de revisão humana privada**. OCR incompleto
  não prova inexistência de campo. Não se afirma conferência nominal nem dos
  valores clínicos, carimbos ou assinaturas das 50 pessoas.
- Rótulos reconhecidos incluem nome, telefone, CPF, nascimento, data, olho,
  esférico, cilíndrico, eixo, lentes e recebimento/assinatura. A matriz abaixo usa
  a planilha legível como fonte precisa dos campos novos; não presume que glicose,
  pressão, sangue, escolaridade ou nome da mãe constem de todas as fichas antigas.

Diretórios pesquisados: `docs/` recursivamente, incluindo `docs/data/` e
`docs/references/`. `docs/reference/`, `data/`, `anexos/`, `attachments/`,
`reference/` e `references/` na raiz não existem. Não foi identificado outro
modelo original ou verso nesses caminhos. Isso não comprova a inexistência de
verso no documento físico. Os originais não foram modificados.

`PLANEJAMENTO_ACTIONS_MAP_BENEFICIARIOS.md`, citado pelo plano como fonte da
Biblioteca, não foi localizado no workspace. Não se presumiram regras adicionais
desse documento ausente; os campos/permissões acima vêm das fontes acessíveis.

Os temporários de inspeção usaram `tmp/fase0/`, ignorado pelo Git. As imagens
brutas/rotacionadas e os recortes do acervo foram descartados após a leitura;
ficam apenas a prévia sanitizada do XLSX e evidências de estrutura/rótulos.
O relatório registra estrutura e rótulos, sem valores de pacientes. O responsável
deve confirmar qual modelo/versão será aprovado para a próxima ação.

## 2. Matriz literal de campos

Legenda de destino proposto: `P` cadastro pessoal privado; `C` registro clínico
segregado; `D` versão de documento privado; `A` metadado de ação; `E` etiqueta
mínima; `I` exportação agregada aprovada. Nenhuma proposta é schema já executado.
Pessoal/saúde são classificações de engenharia para restrição de acesso, não uma
decisão sobre base legal. Obrigatoriedade nova, unidades e faixas clínicas
dependem de aprovação profissional; a ficha não explicita essas regras.

| Rótulo literal e origem em `Planilha1` | Tipo, validação e obrigatoriedade | Responsável proposto / finalidade | Sensibilidade e destino |
| --- | --- | --- | --- |
| “MELHOR VISÃO”, `A1:N1` | Identificação do programa; selecionar ação existente | Administração/Tecnologia cadastra uma vez | Institucional; A/D; I somente aprovado |
| “NOME”, `A8`, valor `B8:F8` | Texto; atual exige 2–160 caracteres; sem deduplicar por nome | Recepção; identificar a pessoa | Pessoal; P/D; E apenas mínimo aprovado |
| “CPF”, `G8`, valor `H8:J8` | Atual opcional com verificadores; transcrição inválida fica documental pendente | Recepção; finalidade e necessidade devem ser confirmadas | Pessoal; P/D privado; nunca CPF completo em E/I |
| “DAT. NASC.”, `K8`, valor `L8:N8` | Data real, sem futuro; não presumir século; obrigatoriedade pendente | Recepção; identificação e contexto autorizado | Pessoal; P/D; não I/E |
| “NOME DA MÃE”, `A9`, valor `B9:F9` | Texto; **não equivale a responsável**; necessidade/obrigatoriedade pendentes | Recepção; identificação somente se justificada | Pessoal da pessoa e de terceiro; P/D, não E/I |
| “FONE”, `G9`, valor `H9:J9` | Atual opcional, 7–13 dígitos após normalização; sem DDD inventado | Recepção; contato operacional | Pessoal; P privado; impressão só se necessária; não E/I |
| “ESCOLARIDADE”, `K9:L9`, valor `M9:N9` | Categoria/texto; vocabulário e necessidade pendentes; não inferir | Recepção, se aprovado | Pessoal; P/D restrito; não I por padrão |
| “GLICOSE”, `A12`, valor `B12:C12` | Medida; unidade, método, momento e faixa **não especificados** | Profissional habilitado; recepção só se houver atribuição formal aprovada | Saúde; C/D; não E/I nominal |
| “PRESSÃO”, `D12:E12`, valor `F12:I12` | Medida; confirmar arterial/outra, componentes e unidade; não inventar | Profissional habilitado | Saúde; C/D; não E/I nominal |
| “TIPO DE SANGUE”, `J12:K12`, valor `L12:N12` | ABO/Rh somente após confirmar finalidade, origem e valores permitidos; ausência explícita | Profissional autorizado; sem exigência automática porque existe no modelo | Saúde; C/D; eventual estatística privada aprovada; não E |
| “PARA LONGE”, `A15:A17`, e “OLHO”, `B15` | Contexto do quadro; linhas “O.D.” (`B16`) e “O.E.” (`B17`) | Profissional habilitado; não é seleção feita pela recepção | Saúde; C/D |
| “ESFÉRICO”, `C15`, valores `C16/C17` | Medidas por olho; unidade, sinal, precisão e limites pendentes de validação clínica | Profissional habilitado | Saúde; C/D; nunca E/I |
| “CILINDRICO”, `D15`, valores `D16/D17` | Medidas por olho; convenção de sinal e faixas pendentes | Profissional habilitado | Saúde; C/D; nunca E/I |
| “EIXO”, `E15`, valores `E16/E17` | Medidas por olho; domínio e unidade aprovados antes de implementar | Profissional habilitado | Saúde; C/D; nunca E/I |
| “DP”, `F15`, valores `F16/F17` | Medidas por olho no layout; confirmar significado/unidade; **não renomear para DNP por suposição** | Profissional habilitado | Saúde; C/D; nunca E/I |
| “OBSERVAÇÕES”, `H15:N15` | Cabeçalho do bloco com adição/lentes; não há área livre separada inequivocamente definida | Responsável clínico define interpretação | Pode conter saúde; C/D; diferente de observações gerais atuais |
| “ADIÇÃO”, `H16`, valor `I16:N16` | Medida; escopo, unidade e faixas pendentes | Profissional habilitado | Saúde; C/D; nunca E/I |
| “LENTES”, `H17`, valor `I17:N17` | Texto/categoria; vocabulário, comprimento e relação com pedido pendentes | Profissional habilitado | Saúde; C/D; nunca E/I |
| “DATA”, `A20`, valor `B20:C20` | Data do termo; confirmar se entrega/exame/emissão; separar os eventos | Operação registra o evento real | Pessoal no documento; D; não usar como data da ação por inferência |
| “NOME OPTOMETRISTA”, `D20:F20`, valor `G20:N20` | Identidade profissional com versão/habilitação; não transformar em médico automaticamente | Administração autoriza profissional; profissional valida o documento | Identificação profissional; D/C; I só opt-in aprovado |
| “MUNICÍPIO”, `A21`, valor `B21:C21` | Catálogo IBGE; semântica do município do termo pendente | Recepção/operador autorizado; não confundir com residência nem local da ação | P/D; agregado territorial somente com semântica comprovada |
| “Nº REGISTRO”, `D21:F21`, valor `G21:I21` | Tipo de registro/órgão depende da habilitação confirmada; não supor CRM | Administração/profissional | Profissional; D; I apenas dados aprovados |
| “CPF”, `J21:K21`, valor `L21:N21` | **CPF do bloco profissional**, distinto do CPF do beneficiado em `G8`; necessidade pendente | Administração/profissional, nunca preencher com CPF do paciente por repetição do rótulo | Pessoal profissional; D restrito, não E/I |
| “DECLARAÇÃO / ASSINATURA”, `A22:F22`, texto `A23:F25` | Declaração de benefício e assinatura física; não digitalizar/copiar assinatura nesta etapa | Beneficiário/responsável no fluxo físico aprovado | Documento pessoal; D privado; não E/I |
| “CARIMBO / OPTOMETRISTA / ASSINATURA”, `G22:N22`, área `G23:N25` | Espaço físico; revisar competência e validade do documento | Profissional habilitado | Documento profissional/saúde; D privado; assinatura eletrônica em standby |
| Resumo, `O2:X2`: “NOME”, “CPF”, “NASC.”, “ESCOLARIDADE”, “GLICOSE”, “PESSÃO”, “SANGUE”, “LOCAL”, “DATA”, “RESPONS.” | Resumo **nominal**, não analytics público. “PESSÃO” é grafia literal; significado de LOCAL/RESPONS. pendente | Consulta operacional somente com permissão por finalidade | P/C privado; nunca exportar a linha do resumo |

Não foram identificados na planilha campos separados de endereço, sexo, RG,
acuidade visual, diagnóstico codificado ou triagem adicional. Não criá-los como
“extraídos da ficha”. `responsavel`, observações gerais e município de residência
já existentes vêm da especificação/legado, sem equivalência automática com mãe,
observação oftalmológica ou profissional do termo.

### Metadados novos definidos pelo responsável, não extraídos de paciente

| Campo | Origem e regra | Destino e histórico |
| --- | --- | --- |
| Nome/título da emenda ou convênio | Administração/Tecnologia no cadastro da ação; não aparece como campo pessoal na ficha lida | A; recepção em leitura; D por snapshot; I após aprovação |
| Número da emenda/convênio | Identificador textual, preserva zeros e formatação; política de ausência pendente | A/D/I aprovado; não redigitar por atendimento |
| Autor da emenda | Metadado institucional; opcional quando não aplicável; não inventar autor | A/D/I aprovado; nenhuma lista beneficiário ↔ autor |
| Tipo do instrumento | Proposta EMENDA/CONVÊNIO/OUTRO/NÃO INFORMADO, a confirmar | A, independente de apoio TOTAL/PARCIAL |
| Marca AC Social | Asset real `public/logo-ac-social.png`; uso atual em login/shell | Fixa em D; verificar aplicação também na etiqueta aprovada |
| Logo de órgão e logo de clínica | Uploads opcionais para todas as ações, TOTAL e PARCIAL; autorização de uso distinta de publicação | A/D privados; I somente após aprovação e saneamento |

Retenção de cadastros, registros clínicos, documentos, auditoria e impressos:
**PENDENTE de definição institucional por finalidade**, sem prazo jurídico
inventado. A expiração técnica atual de uploads em 24h não resolve essa decisão.

## 3. Inventário real do sistema

| Arquivos existentes | Comportamento confirmado |
| --- | --- |
| `package.json`, `src/app/`, `src/components/providers.tsx` | Next 16.4.3, React 19.3, TS estrito, MUI 9, RHF/Zod, TanStack Query/Axios; sem necessidade de atualização de stack nesta fase |
| `src/features/actions/action-dialog.tsx`, `actions-list.tsx`, `action-detail.tsx` | Modal, listagem/filtros, detalhes, beneficiários e estados editoriais; não há cadastro de emenda, apoio, parceiros ou uploads de logos |
| `backend/app/domain/contracts.py`, `application/actions.py`, `domain/ports.py`, `infrastructure/actions.py` | DTO estrito, serviço/porta/adaptador; cadastro, versão/CAS, transições, auditoria e outbox |
| `backend/app/security/session.py`, `infrastructure/identity.py`, `api/routes.py` | Sessão opaca por hash, oito horas, origem/CSRF, scrypt institucional, revalidação de tipo/equipe e rate limit persistido |
| `src/app/(app)/layout.tsx`, `src/app/login/page.tsx`, `src/components/app-shell.tsx` | Login e shell institucional; tipo/equipe vêm do backend; link da Agenda para o público administrativo atual |
| `src/features/beneficiaries/`, `api/beneficiaries.py`, `application/beneficiaries.py`, `infrastructure/beneficiaries.py` | Cadastro geral, leitura individual, correção versionada e segunda via dos dados atuais; não é ficha clínica nem snapshot imutável de prescrição |
| `src/features/beneficiaries/beneficiary-sheet.css` | Segunda via em A4, margem 14mm, impressão via navegador; cabeçalho usa texto institucional, não as três logos exigidas para o novo documento |
| `src/features/imports/`, `api/import_files.py`, `infrastructure/import_files.py`, `pdf_worker.py` | Upload PDF/CSV/JSON, revisão, ownership, cifragem, limites e parser em subprocesso; a prévia do PDF original pode conter saúde, embora DTOs estruturados antigos a rejeitem |
| `src/features/dashboard/overview.tsx`, `api/routes.py:indicators` | Ações não arquivadas, participações, municípios e revisões de todo o período; sem filtros clínicos/emenda/parceiro nem pessoas únicas globais |
| `api/integrations.py`, `application/integrations.py`, `infrastructure/integrations.py`, `outbox.py` | Tokens de leitura hash/escopo, senha reforçada, cota, exportação congelada e envio 1.1/ACK/retries; gestão exclusiva Tecnologia |
| `src/app/api/backend/[...path]/route.ts`, `src/lib/backend.ts`, `integration-proxy.ts` | BFF com allowlist, origem/CSRF, limite de bytes, no-store; proxy Bearer separado, sem converter token de serviço em sessão |
| `backend/alembic/versions/0001*` a `0006*`, `backend/alembic/env.py` | Migrações administrativas próprias, função delegada de autenticação, imports privados, retirada de rascunho, tokens e expiração opcional; não foram aplicadas nesta execução |
| `docs/branding-guidelines.md`, `public/logo-ac-social.png` | Marca oficial existente, PNG 225×225, 4.836 bytes, SHA-256 `59a31277b1a93693d0c481bb4b2f1e5648128dda4570d87d423394a2d63e65a1`; paleta vermelho/vinho, footer e padrões MUI; uploads parceiros ausentes |

Guias locais consultados antes de alterações: `node_modules/next/dist/docs/01-app/`
`01-getting-started/15-route-handlers.md` e `02-guides/authentication.md`.
Rotas usam App Router e parâmetros assíncronos; APIs revalidam autorização.

### Esquema existente, não proposto

`backend/private/actions.sqlite3` foi aberto **em modo somente leitura** para
inspecionar metadados, sem consultar linhas pessoais. As 12 tabelas abaixo
correspondem aos modelos de `backend/app/infrastructure/models.py`.

| Tabela | Campos/restrições relevantes |
| --- | --- |
| `acoes_map_acoes` | ID/versão, nome/categoria/descrição/resumo, início/fim, status, `locais JSON`, autores e horários. Status: em_revisao/validada/publicada/arquivada |
| `acoes_map_beneficiarios` | UUID, `dados_cifrados`, município de residência. Envelope Fernet com ID/versão e dados gerais |
| `acoes_map_participacoes` | UUID, FKs ação/beneficiário, `local_indice`, origem única; UNIQUE(acao_id, beneficiario_id) |
| `acoes_map_auditoria` | UUID, profissional, operação, entidade, horário; sem conteúdo nominal do recurso |
| `acoes_map_sessoes` | Hash do token, profissional, expiração |
| `acoes_map_login_limites` | Chave HMAC, tentativas, expiração |
| `acoes_map_importacoes` | Hash da fonte, páginas, autor, horário |
| `acoes_map_documentos_importacao` | FK lote, formato, tamanho, estado, conteúdo cifrado, expiração |
| `acoes_map_partes_importacao` | PK(documento_id, indice), conteúdo cifrado |
| `acoes_map_integracoes_outbox` | Evento, chave idempotente única, payload agregado, estado, tentativas/horários/erro seguro |
| `acoes_map_credenciais_integracao` | Hash único, prefixo/sufixo, escopo fixo, ator, validade nullable, revogação/uso/cota |
| `acoes_map_exportacoes_integracao` | FK credencial, payload agregado congelado, criação/expiração |

Não há tabelas atuais de profissional operacional, atribuição por ação, avaliação
clínica, parceiro, logo, documento clínico versionado, etiqueta ou evento de entrega.
`local_indice` é posição em JSON, não FK para uma tabela de locais. A API impede
remapear locais com participações vinculadas; substituir por IDs exige migração.
Uma participação única por ação/pessoa não permite modelar várias consultas na
mesma ação. Não reutilizá-la como contador clínico sem definir essa semântica.

Em desenvolvimento, o adaptador usa SQLite próprio. Em produção, o código atual
usa a mesma URL lógica para identidade e persistência, schema `actions_map` com
TLS; a identidade é delegada a `actions_map.authentication_identity`. Isso é
isolamento por schema, **não prova banco lógico independente**. Sem conexão a
produção nesta execução, topologia, grants, revisão aplicada e backups atuais
continuam não confirmados. Não foram lidos host, senha ou registros institucionais.

### APIs atuais principais

- Sessão: `/api/v1/auth/login`, `/auth/me`, `/auth/logout`.
- Ações: `/api/v1/acoes`, `/acoes/{id}`, transições `/revisar`, `/aprovar`, `/publicar`.
- Pessoas: `/api/v1/acoes/{id}/beneficiarios`, `/{pessoa}` e `/{pessoa}/segunda-via`.
- Importação: `/api/v1/importacoes/arquivos`, partes, preparo, prévia, páginas e confirmação.
- Indicadores: `/api/v1/indicadores`; tecnologia: `/api/v1/tecnologia/saude`,
  `/sincronizar-agenda` e `/tokens` sob o mesmo prefixo técnico.
- Serviço: `/api/v1/integracoes/health` e `/integracoes/acoes/resumos`, expostos
  pelo Next como `/api/integracoes/v1/health` e `/api/integracoes/v1/acoes/resumos`.

OpenAPI executável em `docs/contracts/actions-map.openapi.json`. Não há rotas
clínicas, recepção, impressão de etiqueta ou analytics por emenda. `/mapa-acoes`
continua removido; o mapa público pertence ao Portal.

## 4. Matriz de acesso: realidade e alvo

| Recurso | Administração hoje | Tecnologia hoje | Recepção/profissional hoje | Alvo do piloto |
| --- | --- | --- | --- | --- |
| Cadastro de ação/beneficiário geral | Permitido com tipo administrativo | Permitido com tipo administrativo | Login recusado | Gestão Admin/Tech; recepção só identificação na ação atribuída |
| Ficha clínica | Não existe DTO/tela; prévia histórica pode mostrar imagem clínica | Mesmo limite | Sem acesso | Profissional habilitado e atribuído; Admin/Tech sem acesso clínico irrestrito |
| Ficha geral/segunda via | Consulta privada com vínculo ação/pessoa | Idem | Sem acesso | Manter comprovante geral separado de documento clínico |
| Dashboard | Permitido | Permitido | Sem acesso | Continuar exclusivo Admin/Tech; testes negativos também nas novas APIs |
| Integrações/tokens | Negado no servidor | Permitido com reforço de senha em gestão | Sem acesso | Exclusivo Tecnologia |
| Dados de outra ação/profissional | Acesso administrativo global aos dados gerais | Idem | Não há atribuições | Checar ação, profissional, finalidade e status no servidor antes de clínica |

A propriedade `Professional.allowed` aceita somente tipo `administracao` com
equipe `administracao` ou `tecnologia`. Portanto **não existe mecanismo operacional
validado para recepção/médico no piloto**. Colocar novos profissionais na equipe
administrativa liberaria dados globais e dashboards, contrariando o alvo.
É necessário definir a autorização mínima com a identidade existente antes de
ativar o fluxo; novo login local avançado continua em standby. Não usar acesso
anônimo, credencial compartilhada ou apenas ocultação de menu como solução.

## 5. Pipeline e contratos conferidos

Fluxo obrigatório: **Actions Map → Agenda Digital → Plataforma Consolidada de
Análise de Dados → Portal Institucional**. Nenhuma alteração nos outros projetos.

| Salto/fonte | Evidência lida e limite |
| --- | --- |
| Map → Agenda | `Summary` 1.1, `enqueue` e worker local; POST da Agenda em `../agenda-digital/src/app/api/integracoes/v1/acoes/resumos/route.ts`, validador `src/modules/actions-map/domain/summary.ts` e handlers `application/routes.ts`. Exige Bearer/Idempotency-Key; ACK accepted/duplicate |
| Agenda → Plataforma | Rotas reais `../agenda-digital/src/app/api/analytics/acoes/route.ts` e `analytics/v2/acoes/route.ts`. A v2 **já existe no código vizinho**, com `domain/frozenExport.ts` e repositório próprio; o plano antigo daqui que a chama de inexistente está desatualizado |
| Consumidor Plataforma | Não foram localizados os módulos propostos `frontend/src/domain/acoes` e `frontend/src/server/acoes`; busca em frontend/backend/contracts não localizou `ac-actions-map` nem `acoesInstitucionais` no código pesquisado. Isso não equivale a prova de ausência em um deploy remoto |
| Plataforma → Portal | `../acsocialportal/backend/app/infrastructure/actions_contract.py` e `analytics.py` já têm validação do bloco `acoesInstitucionais`, envelope `versao="1"`, cálculo `1.0`, fonte ac-actions-map, validade/geração e agregados municipais. A leitura aponta à Plataforma, sem atalho ao Map. Disponibilidade real não testada |

Os repositórios vizinhos foram consultados somente para definições de contrato,
sem execução de seus scripts, leitura de segredos ou acesso HTTP/SQL produtivo.
A presença de código não comprova implantação, consentimento de publicação ou
propagação real. Não repetir relatos produtivos de 26/10 como teste novo.

O item 1.1 contém exatamente 14 campos: versão, evento, fonte, ação, revisão,
operação, categoria, início/fim, municípios, quantidades de ações/participações/
pessoas e elegibilidade pública. **Não contém título, número/autor da emenda,
parceiros ou logos**. O receptor rejeita campos extras: acrescentá-los ao Map
isoladamente quebra a integração. Proposta de evolução, sem ativação, no plano MVP.

As quantidades são por ação. A soma entre ações não prova pessoas únicas globais;
totais de envelope não se somam por página. Emenda/autor não têm denominador
confiável enquanto não houver associação aprovada e política de deduplicação.

## 6. Conflitos resolvidos por precedência

| Fonte anterior | Decisão de 30/10 | Impacto/migração |
| --- | --- | --- |
| Especificação de 26/10: nenhum dado ocular estruturado | Domínio ocular próprio, conforme ficha e autorização | Criar módulo segregado; preservar cadastro geral existente; não converter manifesto antigo em exame |
| Plano geral de 25/10: `usuario_id` de paciente compartilhado | Cadastro pessoal/saúde próprio do Actions Map | Não associar a outros prontuários nem copiar dados/chaves |
| Plano histórico: login local e assinatura como cadeia principal | Ambos em standby; papel + acesso mínimo seguro | Planejar RBAC viável; nenhum bloqueio artificial por assinatura digital |
| Cadastro antigo sem parceiros/financiamento | Três posições de marca + nome/número/autor da emenda/convênio | Migração aditiva; nulos honestos e snapshots históricos |
| Cadastro geral dito “completo” em 28/10 | Completude apenas do escopo anterior; XLSX tem campos adicionais | Não mapear mãe→responsável, CPF profissional→paciente ou observação clínica→geral |
| Segunda via lê cadastro atual | Documento clínico requer fidelidade da versão emitida | Manter tipo geral; criar emissão clínica versionada futura |
| Plano de Plataforma: v2 ainda não existe na Agenda | Rota v2 localizada no código da Agenda | Revalidar contrato/deploy antes de implementar consumidor; não criar segunda exportação concorrente |
| Relatos antigos de testes/deploy | Nova auditoria verifica somente o que executou | Guardar histórico datado, separar baseline de aprovação do piloto |

## 7. Lacunas que bloqueiam liberação do novo piloto

1. Modelo oficial/versão e revisão literal da página 34 do acervo; qual relação
   entre modelo XLSX e ficha antiga será aceita; quem valida a ficha final.
2. Habilitação profissional, interpretação/unidades/faixas dos exames, necessidade
   de mãe/escolaridade/sangue e responsáveis por preencher cada bloco.
3. Identidade existente utilizável por recepção/profissional e autorização por
   ação/caso, sem promovê-los a Administração e sem criar login avançado às pressas.
4. Topologia independente do banco operacional, grants mínimos, retenção por
   finalidade, guarda de papel, backup/restauração, auditoria e incidente.
5. Medida exata/modelo/margens da etiqueta, impressoras/drivers, modo de papel e
   operação em campo; não há especificação de hardware no workspace inspecionado.
6. Política para ações sem financiamento, direitos dos logos, publicação de
   emenda/autor/profissional, contagem pública e supressão de pequenos grupos.
7. Homologação da nova versão em todos os saltos, consumidor da Plataforma e
   verificação real do Portal, com responsáveis e rollback.

Não há necessidade de senha do usuário para resolver a descoberta. Essas decisões
devem ser registradas antes da fase afetada, mantendo funcionalidades existentes
e desenvolvimento com dados sintéticos. Os resultados executados nesta revisão
estão na [auditoria](AUDITORIA_APLICACAO_E_PRINCIPIOS.md).
