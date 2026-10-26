# Privacidade, retenção e migração

## Tratamento local

O módulo armazena somente nome cifrado, município opcional e vínculo geral à ação. Nome não é critério de identidade única. Não copiar prontuários, CPF, contatos, receitas, assinaturas ou chaves de outros sistemas. Auditoria guarda profissional, operação, entidade e horário; não guarda o conteúdo pessoal. A API nominal é privada e auditada; o pipeline contém só IDs técnicos de ações e totais.

O PDF original permanece no disco sob proteção institucional; não é copiado para `/public`, storage público, serviços de OCR/IA ou fixtures. Diretórios de dados, bancos, fontes e imagens temporárias ficam ignorados pelo Git. Um arquivo já presente em commit anterior continua no histórico até eventual limpeza autorizada; removê-lo do índice atual não reescreve histórico.

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

Exige autenticação e revogação homologadas, credenciais SQL restritas, sessão/storage multi-instância, revisão da migração, upload/storage privado, limites do parser/quotas, monitoramento, política de retenção/publicação e testes de backup/restauração. Esta primeira entrega bloqueia persistência/importação/publicação produtivas até essas implementações.
