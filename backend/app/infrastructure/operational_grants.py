"""Privilégios mínimos após a migração 0010, inclusive com defaults legados permissivos."""

OPERATIONAL_GRANTS = """DO $$ BEGIN
  IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='ac_actions_map_runtime')
    AND to_regclass('actions_map.acoes_map_instituicoes') IS NOT NULL THEN
    REVOKE ALL ON actions_map.acoes_map_instituicoes,
      actions_map.acoes_map_instituicoes_marcas, actions_map.acoes_map_acao_instituicoes,
      actions_map.acoes_map_designacoes_clinicas FROM ac_actions_map_runtime;
    GRANT SELECT,INSERT ON actions_map.acoes_map_instituicoes,
      actions_map.acoes_map_instituicoes_marcas TO ac_actions_map_runtime;
    GRANT SELECT,INSERT,DELETE ON actions_map.acoes_map_acao_instituicoes TO ac_actions_map_runtime;
    GRANT SELECT,INSERT,UPDATE ON actions_map.acoes_map_designacoes_clinicas TO ac_actions_map_runtime;
  END IF;
END $$"""
