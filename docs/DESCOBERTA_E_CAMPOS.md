# Descoberta e inventário — 26/10/2026

A especificação `AC_ACTIONS_MAP_DOCUMENTACAO_AGENT.md` prevalece quando diverge do planejamento anterior: cadastro próprio de beneficiários, sem `usuario_id` clínico, sem tracking assistencial, N locais por ação. O pedido de desenvolvimento autoriza esta implementação local; não autoriza migrar/importar produção.

**Atualização posterior:** o responsável autorizou o deploy conjunto, a persistência isolada e a carga inicial de 32 fichas do Programa Melhor Visão. Depois aprovou as 18 fichas restantes e definiu Mamanguape para os municípios ausentes: o lote final tem 50 registros e nenhum município em branco, com backup e auditoria. O preenchimento dos campos ausentes decorreu da orientação expressa do responsável. Os limites da descoberta inicial abaixo registram aquele momento, sem substituir essas autorizações posteriores. Consulte [deploy](DEPLOY_PRODUCAO.md) e [revisão atual](REVISAO_PRINCIPIOS_2026-10-26.md).

## Fontes realmente verificadas

- Três documentos Markdown do projeto e as duas capturas em `docs/references/`. Login e shell seguem a paleta, composição, sidebar e footer dessas referências. Logotipo real reutilizado do repositório da Agenda Digital.
- PDF privado em `docs/data/`: 50 páginas digitalizadas, zero páginas com camada de texto. Título impresso: **Programa “Melhor VISÃO”**. Todas as páginas conferidas visualmente em folhas de contato; páginas inicial e final ampliadas. Isso não constitui transcrição nem validação nominal. Há páginas giradas, grafias manuscritas e campos ausentes; nenhuma pessoa foi importada nesta entrega.
- Agenda Digital: `src/app/api/auth/login/route.ts`, `src/modules/auth/application/authenticateUser.ts`, `src/modules/profissionais/application/credentials.ts` e exportação em `src/app/api/analytics/atendimentos/route.ts`.
- Portal: domínio, persistência e API de ações, identidade e verificador de senhas; `docs/mapa-acoes.md` e `docs/beneficiarios-melhor-visao.md`.
- Plataforma Consolidada: guia `docs/integracao-aplicacao-cliente.md`. A integração externa documentada é de **consulta GET**; não é um receptor de resumos de ações.
- PostgreSQL configurado: `SELECT 1` e metadados de `information_schema` em transação somente leitura, timeout de oito segundos. Nenhum registro pessoal lido pela descoberta; nenhuma estrutura ou dado alterado.
- Guias locais do Next 16.4.3: layouts, páginas, route handlers, error/not-found e autenticação com Cache Components. Esta versão usa `retry()` nos boundaries e admite `instant = false` no layout autenticado.

## Identidade real

`public.profissionais_cadastrados`: `id`, `email`, `password`, `display_name`, `user_type`. Equipes em `public.equipes_profissionais`: `name`, `professional_ids_json` (JSONB com IDs). Tipo administrativo real: `administracao`. Nomes de equipe normalizados: `administracao` e `tecnologia`. Não existe coluna `ativo` nessas tabelas verificadas: existência da conta e vínculo atual são revalidados em toda requisição. Revogação por mudança de tipo/equipe ou remoção da conta bloqueia a sessão.

Senha: scrypt da Agenda, sal hexadecimal usado como texto UTF-8, N=16384/r=8/p=1, chave de 64 bytes, comparação constante. Credenciais legadas sem hash não são aceitas neste módulo: atualizar na Agenda. Não se criam senhas ou profissionais locais. O servidor exclusivo de E2E injeta identidades sintéticas somente nos testes.

## Inventário de campos do PDF

| Origem | Destino nesta etapa | Necessidade / validação | Visibilidade / retenção |
| --- | --- | --- | --- |
| Programa | Ação selecionada pelo operador | Não inferir ação/local a partir de uma ficha | Metadado interno; resumo editorial separado |
| Nome | Beneficiário próprio do módulo | Transcrição conferida, 2–160 caracteres; ilegível aguarda revisão | Privado, cifrado; prazo institucional pendente |
| Município | Município de residência opcional | Código do catálogo PB/IBGE; ausência não é preenchida por inferência | Privado; nunca determina o local da ação |
| Data da ficha | Não transcrita automaticamente | Pode indicar entrega/exame, sem semântica confirmada | Pendente de definição institucional |
| Telefone, CPF, nascimento | Fora do cadastro inicial | Constam do PDF, mas finalidade/necessidade não aprovadas | Permanecem somente na fonte privada |
| OD/OE, esférico, cilíndrico, eixo, DP, adição, lentes | Excluídos do modelo genérico | Conteúdo óptico, sem finalidade neste domínio | Não estruturados nem transportados |
| Observações manuscritas, assinatura, responsável | Não importados | Podem conter dados clínicos/privados | Somente documento original privado |
| Arquivo + página | Hash SHA-256 + página + ação | Idempotência exata; não une pessoas por nome | Metadado de origem restrito, sem valor nominal na auditoria |

## Legado do Portal

`portal.institutional_actions` contém `id`, `version`, `draft` e `published` em JSON. O CRUD atual admite um município por ação; versões públicas e rascunhos são distintos. `portal.beneficiaries` guarda conteúdo e imagem cifrados com chave própria do Portal. **Não importar nem copiar essa chave**; o mapeamento de registros e sua eventual transferência precisam de autorização e conciliação.

| Legado | Novo módulo (proposta local) | Tratamento na migração futura |
| --- | --- | --- |
| `id` | ID próprio + correspondência legada | Preservar tabela de correspondência e origem |
| `version` | `versao` | Não reutilizar como se fosse versão do novo registro |
| `draft.name` | `nome` | Conferir nome sem criar restrição de unicidade |
| `draft.municipality_code` | Primeiro item de `locais` | Expandir para N locais sem inferência histórica |
| `published` | Snapshot público revisado | Reaprovar; não publicar por mera cópia |
| Anexos do acervo | Referências futuras ao storage institucional | Sem cópia automática ou acesso público a fichas |

## Limites da descoberta

Não foram inspecionados todos os registros, permissões efetivas do usuário SQL, backups ou infraestrutura de deploy. O guia de branding referencia uma auditoria ausente neste repositório. Nenhum contrato receptor de ações na Agenda foi encontrado. Migração, ingestão em produção e substituição do escritor do Portal continuam pendentes de revisão e homologação.

Catálogo local: 223 municípios, reutilizado do Portal, que registra origem na [API oficial do IBGE](https://servicodados.ibge.gov.br/api/docs/localidades). A aplicação não depende de consulta externa durante cadastro/build; uma atualização do catálogo exige conferência explícita.
