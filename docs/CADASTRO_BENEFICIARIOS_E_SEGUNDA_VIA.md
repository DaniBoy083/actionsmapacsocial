# Cadastro completo, segunda via e retirada do mapa — 28/10/2026

> **Limite de “completo” em 30/10:** refere-se ao cadastro geral autorizado em
> 28/10, não à ficha clínica do novo plano v2.1. A leitura da planilha identificou
> campos adicionais e um bloco profissional distinto. Esta segunda via continua
> sendo cadastro geral dos dados atuais; não é prescrição nem ficha clínica
> versionada. [Matriz atual da fonte](FASE_0_DESCOBERTA_2026-10-30.md).

## Decisões do responsável

Esta revisão atende à solicitação de coletar/exibir os dados gerais completos da
ficha de referência, excluindo graus e dados oculares, permitir segunda via e
**remover totalmente a página do mapa** do Actions Map. A solicitação posterior
autorizou expressamente completar os dados faltantes do PDF no banco institucional.

Estas decisões substituem o cadastro mínimo anterior e a inclusão do mapa no commit
`d361873`. Não alteram a finalidade de gestão de ações nem autorizam tracking
clínico, associação automática entre pessoas ou divulgação pública de cadastros.

O modelo real do PDF foi inspecionado visualmente. As 50 fichas foram conferidas
em imagens locais; não houve OCR externo, transmissão do PDF a terceiros ou
inferência de graus, dados oculares, nomes ou DDD ausente. Logos de apoiadores
e dados profissionais oculares do modelo não foram transformados em atributos de beneficiários.

## Campos e origem

| Campo do documento | Cadastro privado | Regra |
| --- | --- | --- |
| Programa | Ação associada | Identificação na ficha e na segunda via, sem duplicar cadastro da ação |
| Nome | `nome` | Obrigatório, 2–160 caracteres; cadastro existente preservado |
| Telefone | `telefone` | Opcional, 7–13 dígitos; pontuação removida, sem inventar DDD |
| CPF | `cpf` | Opcional; 11 dígitos e verificadores válidos, sem pesquisa/deduplicação automática |
| CPF legível que exige conferência | `cpf_documento` | Campo separado, 11 dígitos transcritos; sempre identificado como pendente, sem afirmar identidade válida |
| Nascimento | `data_nascimento` | Data válida, sem nascimento futuro; anterior ou igual à data da ficha, quando ambas existem |
| Data | `data_ficha` | Data do documento, independente da data da ação/importação |
| Município | `municipio_ficha_ibge` | Código PB conferido no catálogo; não determina automaticamente residência/local da ação |
| Responsável | `responsavel` | Texto privado, até 160 caracteres, somente quando legível |
| Observações | `observacoes` | Observações gerais, até 1.000 caracteres; sem transcrever conteúdo ocular |
| Declaração de recebimento | `recebimento_confirmado` | Confirmado, não confirmado ou não informado; impressão não altera esse valor |
| Assinatura | Espaço para assinar a via impressa | Não se copia assinatura/biometria da imagem nem se cria assinatura digital em nome da pessoa |
| Residência/local da participação | Campos operacionais anteriores | Mantidos separados do município escrito na ficha |

Ausência permanece `null`, apresentada como **Não informado**. Nenhum valor foi
fabricado para tornar um cadastro aparentemente completo. O responsável autorizou
normalizar anos abreviados como 77/84/89 para 1977/1984/1989 e o ano 26 da ficha
para 2026. Casos ainda ambíguos mantêm revisão pendente. Datas completas foram
preservadas como escritas, inclusive quando diferem das outras fichas.

Campos estruturados de olho, OD/OE, esférico, cilíndrico, eixo, DP/DNP, adição,
lentes e receita não são aceitos pela API/importação e não aparecem na segunda via.
Observações livres continuam dependendo da revisão do operador: o sistema não
promete classificar automaticamente o significado de cada texto digitado.

## Uso na aplicação

1. Abra uma ação e use **Registrar beneficiário**. O formulário apresenta os campos
   gerais da ficha e permite deixar sem preenchimento o que não consta da fonte.
2. Na tabela de beneficiários, **Ver ficha** mostra o cadastro completo em uma
   consulta privada individual. A listagem mantém somente o resumo necessário.
3. **Editar** permite corrigir/completar um cadastro existente. A versão impede
   sobrescrever silenciosamente a alteração de outro operador; em 409, reabra a ficha.
4. **Segunda via** consulta os dados atuais, registra a emissão na auditoria e
   apresenta a ficha com programa, campos gerais, declaração, espaço para nova
   assinatura, revisão e horário de emissão em Brasília.
5. Use **Imprimir segunda via** para abrir o diálogo de impressão do navegador.
   A folha A4 oculta navegação, botões e o restante da aplicação. Pode ser impressa
   ou salva em PDF pelo navegador. A emissão não comprova impressão física ou entrega.

A segunda via é uma representação dos **dados atuais**, sem fac-símile da imagem,
campos oculares ou reprodução da assinatura original. A instituição controla o
destino e a guarda das vias impressas. Fechar os diálogos descarta a consulta
individual do cache do frontend; nenhum cadastro é salvo em localStorage.

## Importação PDF, CSV e JSON

O mesmo conjunto de campos/validações é reutilizado no cadastro manual e na revisão
de importações. PDF continua exigindo transcrição/revisão: abrir uma prévia não
grava beneficiários. CSV UTF-8 e JSON aceitam os campos gerais acima, exceto o
vínculo operacional `local_indice`. O nome é obrigatório; demais valores podem faltar.
CSV usa datas `AAAA-MM-DD` e recebimento `sim`, `nao`/`não` ou vazio; JSON usa
booleano ou `null`. A tela oferece modelo CSV atualizado. Campos desconhecidos,
oculares e assinatura em base64 são rejeitados.

Continuam vigentes tamanho de 8 MiB, 200 páginas/registros, ownership, quota,
storage temporário cifrado, revisão por registro, CSRF e confirmação produtiva.
Fonte/ação/página idênticas com dados diferentes continuam retornando conflito;
complementar uma ficha existente não deve ser feito reenviando uma versão antiga
do manifesto com campos vazios.

## Persistência e arquitetura

Todos os novos campos pessoais ficam no envelope Fernet já existente em
`acoes_map_beneficiarios.dados_cifrados`, vinculado ao ID e com versão própria.
Não há coluna nova de CPF, tabela de pessoas compartilhada, índice de busca nominal,
alteração de chave ou migração estrutural. O município de residência anterior
continua na coluna existente e é conferido contra o envelope nos registros novos.

Cadastros antigos contendo somente ID/nome são lidos com versão inicial 1 e
demais dados ausentes. A primeira edição/complementação os atualiza sem perda do
nome, vínculo, origem ou dados existentes. Compare-and-swap sobre o envelope
anterior protege a escrita concorrente; auditoria e alteração usam a mesma transação.

DTOs/regras estão no domínio; `BeneficiaryService` depende da porta
`BeneficiaryRepository`; SQL, cifragem e auditoria ficam nos adaptadores. A API
compõe as dependências. O frontend reutiliza schema Zod e campos RHF/MUI entre
cadastro, edição e importação. Os guias locais do Next 16.4.3 foram consultados.

| Método/rota sob `/api/v1` | Proteção/efeito |
| --- | --- |
| `POST /acoes/{acao}/beneficiarios` | Sessão, origem e CSRF; cadastro cifrado |
| `GET /acoes/{acao}/beneficiarios` | Sessão revalidada, resumo paginado e auditoria |
| `GET /acoes/{acao}/beneficiarios/{pessoa}` | Ficha completa da pessoa vinculada à ação, com auditoria |
| `PATCH /acoes/{acao}/beneficiarios/{pessoa}` | Sessão, origem, CSRF e versão atual; correção privada auditada |
| `GET /acoes/{acao}/beneficiarios/{pessoa}/segunda-via` | Sessão revalidada e auditoria de emissão; nenhuma confirmação automática de recebimento |

Administração/Tecnologia continuam dependendo do tipo administrativo institucional.
Ausência/revogação de acesso bloqueia também as APIs diretas. Respostas usam
`no-store`, `nosniff` e `no-referrer`; consultas individuais só ficam em memória
enquanto o diálogo está aberto. Atualizar dados privados não altera contagens,
estado editorial da ação ou resumos já aprovados. Esses dados não seguem no
outbox, exportação de integrações, Agenda, Plataforma ou Portal.

## Complementação autorizada no banco

O procedimento usa hash exato do PDF + página + ação para localizar o vínculo
existente; nunca associa por nome ou CPF. O lote inteiro passa por prévia com
rollback. A aplicação cria/verifica backup cifrado antes de gravar, usa transação,
lock, versão e auditoria com ator técnico explícito
`operacao-assistida:complemento-pdf`, sem forjar sessão de funcionário.

Somente campos vazios são preenchidos. Conflitos preservam o valor existente e
são relatados sem dados pessoais. Página sem origem interrompe o lote. Ação,
participações e resumos são comparados por hash antes/depois e a transação é
cancelada se esses dados operacionais mudarem. Repetir o mesmo lote não duplica
beneficiários, vínculos ou efeitos de auditoria.

```powershell
# Prévia, sem gravação definitiva; o manifesto é privado e pode estar cifrado.
.\backend\.venv\Scripts\python.exe scripts/complete_beneficiaries_from_pdf.py --manifest CAMINHO_PRIVADO --source CAMINHO_PDF --production-config CAMINHO_CONFIG_PRIVADA
# Somente com autorização do lote, revisão e backup verificado:
.\backend\.venv\Scripts\python.exe scripts/complete_beneficiaries_from_pdf.py --manifest CAMINHO_PRIVADO --source CAMINHO_PDF --production-config CAMINHO_CONFIG_PRIVADA --apply --confirm-production
```

Resultado confirmado nesta execução: **50 cadastros atualizados, 294 campos**, sem
conflitos e sem alteração de ações/participações/resumos. Leitura posterior:
**294/294 campos iguais à revisão**, sem erro de codificação. Distribuição: 48
telefones, 40 CPFs validados, cinco CPFs documentais pendentes, 48 nascimentos,
32 datas de ficha, 30 municípios escritos nas fichas, 41 responsáveis e 50
confirmações de recebimento. Esses totais não são novos beneficiários.

Nova execução em prévia com o manifesto cifrado conferiu 50 cadastros e retornou
zero atualizações/zero conflitos, com rollback; o lote não precisa ser reenviado.

Houve uma falha de acentuação no transporte do PowerShell em 41 responsáveis;
foi identificada na conferência, corrigida especificamente com novo backup/CAS
e nova auditoria, e a leitura posterior confirmou zero ocorrências restantes.
Os seletores dos testes passaram a usar o nome exato da célula para distingui-lo
dos novos botões acessíveis que também identificam a pessoa.

Dados ausentes/ilegíveis permanecem pendentes. Dois CPFs e dois telefones exigem
conferência da grafia, além dos campos em branco e dados de responsável parcialmente
ocultos por carimbo/assinatura. Os dois nascimentos com século ainda não confirmado
não foram presumidos. A ficha com rótulos de CPF/telefone trocados foi tratada na
revisão privada; o CPF transcrito permanece documental/pendente por não passar
nos verificadores. Não houve preenchimento de observações com conteúdo ocular.

PDFs, imagens, transcrições, manifestos, resultados detalhados e backups ficam em
armazenamento privado ignorado pelo Git. O commit contém somente código, contratos,
fixtures sintéticas e evidências agregadas. Backups foram verificados por decifragem;
isso não equivale a homologação integral de restauração do serviço.

## Remoção do mapa

Removidos página `/mapa-acoes`, item da sidebar, endpoint privado/BFF, adaptadores,
DTOs, cache HTTP, malha cartográfica, configuração opcional, diagnóstico e contratos
específicos do mapa. Testes antigos do recurso foram substituídos por verificações
de ausência da navegação e respostas 404. Nenhuma consulta à Plataforma é feita
por essa funcionalidade removida. Documentos anteriores permanecem apenas como
histórico sinalizado. A gestão de ações e a exportação agregada para Agenda permanecem.

## Verificação e limites

Comandos e resultados finais em [auditoria atual](AUDITORIA_APLICACAO_E_PRINCIPIOS.md).
Testes usam identidades/documentos sintéticos e SQLite descartável. A conferência
produtiva foi limitada ao lote autorizado e seus metadados agregados. Nenhum novo
deploy foi executado: a aplicação publicada precisa receber este commit para
expor os novos formulários/segunda via e retirar a página antiga.

Não se afirma conformidade absoluta de toda a instituição: políticas de retenção,
guarda de impressos, aceite humano, restauração integral e validação independente
continuam exigindo evidência própria. Isso não impede concluir e verificar os
controles técnicos e a atualização do lote descritos acima.
