CREATE OR REPLACE FUNCTION actions_map.authentication_identity(
    lookup_value text,
    lookup_by_id boolean
)
RETURNS TABLE (
    id text,
    display_name text,
    password text,
    user_type text,
    teams text[]
)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $authentication$
    SELECT p.id, p.display_name, p.password, p.user_type,
        coalesce(array_agg(e.name) FILTER (WHERE e.name IS NOT NULL), '{}'::text[])
    FROM public.profissionais_cadastrados p
    LEFT JOIN public.equipes_profissionais e
        ON e.professional_ids_json @> jsonb_build_array(p.id)
    WHERE CASE WHEN lookup_by_id
        THEN p.id = lookup_value
        ELSE lower(trim(p.email)) = lookup_value
    END
    GROUP BY p.id
    LIMIT 2;
$authentication$;
