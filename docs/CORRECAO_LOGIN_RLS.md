# Correção do login e RLS — 26/10/2026

**Estado:** alteração de privilégios expressamente autorizada pelo responsável e aplicada em produção. A credencial de runtime passou a encontrar a conta informada por e-mail e ID, com perfil permitido e formato de senha suportado. RLS preservado e SELECT direto do digest revogado. Nenhuma senha foi utilizada ou alterada na verificação.

## Diagnóstico

O backend retornava 401 no POST de login, antes de criar uma sessão. A interface substituía toda resposta 401 pela mensagem de sessão expirada e escondia o motivo correto. A interface passa a preservar o detalhe seguro recebido do backend.

Na verificação restrita à conta informada pelo responsável, o cadastro existe para o proprietário da tabela e usa o scrypt já suportado. A credencial de runtime não consegue enxergar essa mesma conta: `public.profissionais_cadastrados` tem RLS habilitado e nenhuma política de leitura para esse papel. A existência de GRANT SELECT nas colunas não supera o RLS. Não é necessário trocar senha nem criar conta paralela.

## Alteração revisada e aplicada

- Migração Alembic `0002_authentication_lookup`, no schema próprio `actions_map`.
- Função SQL `authentication_identity(text, boolean)` com SECURITY DEFINER e STABLE, busca parametrizada por e-mail ou ID e limite de dois resultados para detectar ambiguidade.
- Retorna somente ID profissional, nome de exibição, digest, tipo e equipes necessários ao backend para autenticar/revalidar sessão. O digest não é devolvido ao navegador nem registrado em logs.
- `search_path` fixo em `pg_catalog, pg_temp`; tabelas qualificadas com schema; sem SQL dinâmico.
- EXECUTE revogado de PUBLIC e concedido somente ao papel `ac_actions_map_runtime`.
- SELECTs diretos desse papel nas colunas de profissionais/equipes são revogados.
- RLS permanece habilitado, políticas existentes e dados não são alterados. O papel não recebe BYPASSRLS, superusuário ou escrita em profissionais.
- Senha, tipo administrativo e equipe continuam sendo verificados pela aplicação. A função não cria sessões nem concede acesso por si só.

Essa delegação permite ao backend consultar uma identidade usando o contexto do proprietário da função, em vez de ampliar políticas gerais de leitura. A revisão automática inicialmente bloqueou a execução por exigir autorização específica para alteração de privilégios; o responsável concedeu essa autorização antes da aplicação. O script administrativo `scripts/migrate_authentication_access.py` aplicou a migração em transação e conferiu que os flags de RLS não mudaram.

## Verificação

Testes backend cobrem a seleção da consulta delegada, parâmetros vinculados, contrato da função, permissões, senha e sessão. Testes de navegador cobrem a mensagem de credenciais recusadas e impedem apresentá-la como expiração. A verificação real de senha depende do próprio titular: não se solicita nem se utiliza sua senha no diagnóstico.

Validação: 41 testes backend e 12 cenários de navegador aprovados. A consulta real com a credencial restrita confirmou existência da conta solicitada, perfil autorizado, revalidação por ID, formato scrypt suportado, RLS habilitado e ausência de SELECT direto no digest. A verificação não criou conta, alterou equipe ou utilizou senha real.
