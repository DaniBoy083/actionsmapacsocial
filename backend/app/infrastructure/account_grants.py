"""Mínimo privilégio das contas locais, inclusive após defaults legados permissivos."""

ACCOUNT_GRANTS = """DO $$ BEGIN
  IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='ac_actions_map_runtime')
    AND to_regclass('actions_map.acoes_map_contas_operacionais') IS NOT NULL THEN
    REVOKE ALL ON actions_map.acoes_map_contas_operacionais,
      actions_map.acoes_map_sessoes_operacionais FROM ac_actions_map_runtime;
    GRANT SELECT,INSERT ON actions_map.acoes_map_contas_operacionais TO ac_actions_map_runtime;
    GRANT UPDATE(usuario,senha_hash,ativo,versao,atualizado_por,atualizado_em)
      ON actions_map.acoes_map_contas_operacionais TO ac_actions_map_runtime;
    GRANT SELECT,INSERT,DELETE ON actions_map.acoes_map_sessoes_operacionais TO ac_actions_map_runtime;
  END IF;
END $$"""
