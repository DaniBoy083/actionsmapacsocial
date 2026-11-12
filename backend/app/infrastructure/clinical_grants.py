CLINICAL_GRANTS = """DO $$ BEGIN
  IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='ac_actions_map_runtime') THEN
    REVOKE ALL ON actions_map.acoes_map_fichas_clinicas,
      actions_map.acoes_map_fichas_clinicas_versoes FROM ac_actions_map_runtime;
    GRANT SELECT,INSERT,UPDATE ON actions_map.acoes_map_fichas_clinicas TO ac_actions_map_runtime;
    GRANT SELECT,INSERT ON actions_map.acoes_map_fichas_clinicas_versoes TO ac_actions_map_runtime;
  END IF;
END $$"""
