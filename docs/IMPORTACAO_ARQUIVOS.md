# Importação por arquivos

Decisão de produto de 26/10/2026: **Visão geral** reúne todos os indicadores. A página redundante `/indicadores` foi removida; a API de indicadores permanece para alimentar o painel. **Importar dados**, em `/importacoes`, substitui Dados iniciais. O endereço antigo `/dados-iniciais` redireciona permanentemente para o novo.

## Uso

1. Abra **Importar dados** e selecione PDF, CSV ou JSON. O envio prepara uma prévia e ainda não cadastra beneficiários.
2. Escolha uma ação existente ou cadastre uma nova. A busca encontra destinos além dos primeiros 100 resultados.
3. Confira cada registro. PDF permite girar a página e transcrever somente nome e município de residência. CSV/JSON preenchem os campos para revisão; nomes repetidos geram aviso. Cada registro precisa ser selecionado após conferência.
4. Revise o lote e a ação de destino. Em produção, marque a autorização expressa antes de confirmar. A gravação é transacional: uma falha desfaz o lote inteiro.
5. Confira incluídos, já associados e pendentes. É possível revisar outras páginas ou remover o arquivo temporário sem excluir beneficiários já cadastrados.

As transcrições são mantidas em memória enquanto se navega entre páginas; não são salvas em localStorage. Fechar/recarregar a página perde a revisão ainda não confirmada. O arquivo deve ser reenviado para iniciar outra revisão. O banco conserva a proveniência para reconhecer reenvios.

## Formatos e limites

- Até **8 MiB** por arquivo, **200 páginas** de PDF ou **200 registros** estruturados. Planilhas Excel precisam ser exportadas como CSV UTF-8. Não há execução de fórmulas, macros ou OCR externo.
- CSV UTF-8, com ou sem BOM, separado por vírgula ou ponto e vírgula. Cabeçalhos: `nome` obrigatório e `municipio_residencia_ibge` opcional. Outros campos são recusados. A tela oferece um modelo sintético para download.
- JSON: lista de objetos com os mesmos dois campos. Nome entre 2 e 160 caracteres; município opcional, validado no catálogo IBGE da Paraíba. Valores ausentes não são inferidos.
- PDF: assinatura real `%PDF-`, parser isolado, limite de objetos e páginas, timeout e limites de CPU/memória no Linux. Documentos cifrados, anexos e ações/JavaScript são recusados. A prévia privada é JPEG com resolução limitada.
- A imagem integral da ficha só aparece ao operador autorizado para revisão; campos clínicos não viram colunas do cadastro. O local da ação e a residência da pessoa continuam distintos.

Exemplo exclusivamente sintético:

```csv
nome;municipio_residencia_ibge
Pessoa de exemplo;2508901
Outra pessoa de exemplo;
```

```json
[{"nome":"Pessoa de exemplo","municipio_residencia_ibge":"2508901"}]
```

O acervo original de aproximadamente 241 MB excede o limite da interface. Ele permanece local; sua carga assistida usa `scripts/import_historical_pdf.py`, manifesto privado revisado, hash da fonte, backup cifrado e confirmação explícita de produção. Não basta renomear ou dividir arquivos para preservar idempotência: fontes diferentes têm hashes diferentes e exigem conciliação humana. Não enviar o acervo para Git, `/public` ou serviços públicos de OCR.

## Persistência, privacidade e transação

Migração aditiva `0003_private_file_import`: duas tabelas próprias no schema `actions_map`. Partes e arquivo completo são cifrados com a chave já existente do módulo. O nome original do arquivo não é persistido. O serviço tem privilégios apenas nas tabelas próprias e consulta delegada da identidade, preservando RLS.

O envio usa partes de 512 KiB, verificadas por tamanho e SHA-256 antes de preparar a prévia. A BFF preserva bytes binários, limita cada requisição a 1 MiB e valida origem/CSRF. Isso respeita o [limite de payload das funções Vercel](https://vercel.com/docs/functions/limitations). Cookies e respostas privadas nunca passam por cache público.

Somente o profissional que enviou o arquivo pode consultar, transcrever ou removê-lo. A política administrativa e o vínculo de equipe são revalidados em cada chamada. Não existe URL pública de download. A API de confirmação exige registros revisados e autorização explícita de produção; cadastro, auditoria e outbox ficam na mesma transação.

Idempotência: SHA-256 do arquivo + número da página/registro + ação de destino. Repetição idêntica retorna existente; tentativa de alterar os dados de uma origem já importada retorna 409 e exige correção supervisionada. Nomes iguais não unem pessoas. Importar participações retira aprovação editorial anterior; o resumo continua `publicavel=false` e sem dados pessoais.

Arquivos têm expiração técnica de **24 horas**, com bloqueio imediato de acesso após o prazo. São apagados ao iniciar novo envio ou pelo expurgo operacional; metadados de proveniência e auditoria permanecem. Quotas: 20 arquivos/32 MiB por operador e 256 MiB globalmente, contados pelo tamanho original. A cifragem adiciona espaço físico. As quotas são serializadas no PostgreSQL. O prazo temporário não substitui a definição institucional de retenção dos cadastros definitivos.

## Operação

Comandos partem da raiz e usam as configurações privadas já provisionadas, sem imprimir segredos:

```powershell
.\backend\.venv\Scripts\python.exe scripts/migrate_file_import.py
.\backend\.venv\Scripts\python.exe scripts/migrate_file_import.py --apply
.\backend\.venv\Scripts\python.exe scripts/purge_expired_imports.py
```

A migração verifica backup cifrado e preservação das ações e do RLS. O expurgo não apaga ações, beneficiários, participações ou auditoria. A operação institucional deve agendá-lo em executor protegido; não se criou endpoint público de manutenção. A remoção de conteúdo expirado é oportunista enquanto esse agendamento não estiver configurado.

Importação assistida do acervo local: prévia é o padrão; `--apply --confirm-production` só após revisão e autorização do lote. `--action-only` permite criar o metadado da ação enquanto os nomes aguardam conferência. IDs derivados da fonte impedem repetir a ação; cadastros manuais com o mesmo nome bloqueiam a carga até conciliação.

```powershell
.\backend\.venv\Scripts\python.exe scripts/import_historical_pdf.py --manifest artifacts/private-import/manifesto-revisado.json --source docs/data/ilovepdf_merged.pdf --operator-email EMAIL_INSTITUCIONAL
```

Os backups em `artifacts/private-import/backups/*.fernet` foram verificados por decifragem antes das operações administrativas. Preservar cópia protegida do banco e da chave em controles separados. Isso não equivale a um ensaio integral de restauração do serviço: esse ensaio, governança de retenção e correções nominais continuam sendo pendências documentadas.

## Contratos privados

| Método e rota sob `/api/v1/importacoes` | Uso |
| --- | --- |
| `POST /arquivos` | Reservar envio e quota |
| `PUT /{id}/partes/{indice}` | Enviar bytes; reenvio idêntico é aceito |
| `POST /{id}/preparar` | Validar hash/formato e preparar a prévia |
| `GET /{id}` | Consultar prévia do próprio arquivo |
| `GET /{id}/paginas/{pagina}?rotacao=90` | Revisar imagem privada de PDF |
| `POST /confirmar` | Gravar registros revisados na ação selecionada |
| `DELETE /{id}` | Remover o arquivo temporário |

O contrato executável atualizado está em [OpenAPI](contracts/actions-map.openapi.json). As rotas antigas de documento local permanecem apenas para desenvolvimento; a interface usa os arquivos selecionados pelo operador.
