# Privacidade, retenção e migração

## Tratamento local

Por decisão posterior do responsável, o módulo armazena os dados gerais da ficha: nome, telefone, CPF validado ou documental pendente, nascimento, data/município da ficha, responsável, observações gerais e confirmação de recebimento, além do município de residência e vínculo à ação. Os novos campos ficam no envelope cifrado existente; a listagem permanece resumida e a consulta completa é individual, privada e auditada. [Inventário, validação e complementação autorizada](CADASTRO_BENEFICIARIOS_E_SEGUNDA_VIA.md). Nome/CPF não criam identidade compartilhada nem deduplicação automática. Não copiar prontuários, receitas, dados oculares, assinaturas ou chaves de outros sistemas. Auditoria guarda ator, operação, entidade e horário; não guarda o conteúdo pessoal. O pipeline contém só IDs técnicos de ações e totais.

A segunda via usa os dados atuais e deixa espaço para nova assinatura, sem copiar biometria da fonte. Sua emissão auditada não comprova impressão física ou recebimento. A instituição controla a guarda e o destino dos impressos. Consultas individuais são descartadas do cache ao fechar o diálogo; não há armazenamento nominal em localStorage. Transcrições e manifestos privados da complementação ficam cifrados e fora do Git. A página do mapa foi removida; não existe nova consulta à Plataforma neste fluxo.

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
