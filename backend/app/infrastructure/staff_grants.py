STAFF_GRANTS = """DO $$ BEGIN
  IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='ac_actions_map_runtime') THEN
    REVOKE ALL ON actions_map.acoes_map_profissionais,
      actions_map.acoes_map_atribuicoes, actions_map.acoes_map_profissionais_historico
      FROM ac_actions_map_runtime;
    GRANT SELECT,INSERT,UPDATE ON actions_map.acoes_map_profissionais,
      actions_map.acoes_map_atribuicoes TO ac_actions_map_runtime;
    GRANT SELECT,INSERT ON actions_map.acoes_map_profissionais_historico
      TO ac_actions_map_runtime;
  END IF;
END $$"""
