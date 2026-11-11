"""Regra compartilhada por migração, provisionamento e teste PostgreSQL local."""

IMMUTABLE_INSTITUTIONAL_GRANTS = """DO $$ BEGIN
  IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='ac_actions_map_runtime') THEN
    REVOKE UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER
      ON actions_map.acoes_map_marcas, actions_map.acoes_map_revisoes_institucionais
      FROM ac_actions_map_runtime;
    GRANT SELECT,INSERT
      ON actions_map.acoes_map_marcas, actions_map.acoes_map_revisoes_institucionais
      TO ac_actions_map_runtime;
  END IF;
END $$"""
