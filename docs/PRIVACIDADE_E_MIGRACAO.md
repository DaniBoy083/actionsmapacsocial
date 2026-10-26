# Privacidade, retenção e migração

## Tratamento local

O módulo armazena somente nome cifrado, município opcional e vínculo geral à ação. Nome não é critério de identidade única. Não copiar prontuários, CPF, contatos, receitas, assinaturas ou chaves de outros sistemas. Auditoria guarda profissional, operação, entidade e horário; não guarda o conteúdo pessoal. A API nominal é privada e auditada; o pipeline contém só IDs técnicos de ações e totais.

O PDF original permanece no disco sob proteção institucional; não é copiado para `/public`, storage público, serviços de OCR/IA ou fixtures. Arquivos selecionados na nova interface ficam temporariamente cifrados em tabelas privadas do módulo, com acesso apenas ao remetente, expiração técnica e quotas, conforme [importação por arquivos](IMPORTACAO_ARQUIVOS.md). Diretórios de dados, bancos, fontes, transcrições e imagens temporárias ficam ignorados pelo Git. O PDF grande foi retirado dos commits que ainda não haviam sido publicados; a cópia local foi preservada.

A instituição precisa definir finalidade, necessidade, base legal, transparência, responsáveis, prazos de retenção, atendimento a titulares e resposta a incidentes. Nenhum prazo jurídico foi presumido. Antes de usar dados reais em novos ambientes, aprovar tratamento, permissões e proteção do storage; usar dados sintéticos em testes.

Não perder `BENEFICIARIES_KEY`: sem ela os cadastros locais ficam ilegíveis. Backup do banco e da chave deve ter controles separados e restauração testada. Alterar a chave sem recifrar o conteúdo não é rotação válida. O script de preparação preserva os valores já existentes e nunca imprime segredos.

## Plano de migração institucional (não executado)

1. Validar schema próprio e FKs com os metadados já descobertos; aprovar constraints/índices e grants mínimos. Criar migração aditiva Alembic revisada, sem alterar tabelas de autenticação.
2. Backup consistente das ações, pessoas privadas, mídias, chaves e auditoria do Portal; testar restauração. Não assumir que a aplicação local tem autorização/chave para descriptografar beneficiários do Portal.
3. Mapear IDs legados, versões editoriais, município único → lista de locais e anexos. Registrar origem e pendências, sem inferir município ou identidade por nome.
4. Executar em staging um importador idempotente com relatório de contagens/checksums e rollback. Revisar os dados por responsável autorizado.
5. Homologar receptor Agenda → Plataforma → Portal, incluindo eventos fora de ordem, duplicatas, arquivamento e risco de identificação em pequenos grupos.
6. Virada com único escritor: retirar permissão de CRUD no Portal, trocar origem de leitura por configuração e ativar o novo módulo somente após conciliação. Não manter dois painéis escrevendo em paralelo.
7. Para rollback, restaurar a origem de leitura validada. Reabrir edição no sistema antigo somente após reconciliação explícita; preservar novos registros e fila para retomada.

## Gate de produção

Autenticação, sessão PostgreSQL multi-instância, credencial SQL restrita, migrações, storage cifrado de uploads, limites do parser/quotas e confirmação administrativa de importação estão implementados. Publicação permanece bloqueada até a integração institucional. Monitoramento operacional, decisões de retenção/publicação, agendamento protegido do expurgo e ensaio integral de backup/restauração permanecem necessários para homologação. A expiração de 24 horas dos arquivos é um controle técnico temporário; não constitui prazo jurídico de retenção dos beneficiários.
