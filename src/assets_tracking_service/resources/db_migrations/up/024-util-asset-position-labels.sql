DROP VIEW IF EXISTS v_util_asset_label CASCADE;
DROP VIEW IF EXISTS v_util_position_label CASCADE;

CREATE OR REPLACE VIEW v_util_asset_label AS
SELECT
    a.id AS asset_id,
    l.value ->> 'rel' AS rel,
    l.value ->> 'value' AS val,
    l.value ->> 'scheme' AS scheme,
    l.value ->> 'creation' AS creation,
    TO_TIMESTAMP((l.value ->> 'creation')::bigint) AS creation_ts,
    l.value ->> 'expiration' AS expiration,
    TO_TIMESTAMP((l.value ->> 'expiration')::bigint) AS expiration_ts,
    CASE
        WHEN l.value ->> 'expiration' IS NULL THEN FALSE
        WHEN TO_TIMESTAMP((l.value ->> 'expiration')::bigint) < NOW() THEN TRUE
        ELSE FALSE
    END AS is_expired,
    l.value ->> 'value_uri' AS value_uri,
    l.value ->> 'scheme_uri' AS scheme_uri
FROM
    asset AS a,
    JSONB_ARRAY_ELEMENTS(a.labels -> 'values') AS l (value);

CREATE OR REPLACE VIEW v_util_position_label AS
SELECT
    p.id AS position_id,
    p.asset_id,
    l.value ->> 'rel' AS rel,
    l.value ->> 'value' AS val,
    l.value ->> 'scheme' AS scheme,
    l.value ->> 'creation' AS creation,
    TO_TIMESTAMP((l.value ->> 'creation')::bigint) AS creation_ts,
    l.value ->> 'expiration' AS expiration,
    TO_TIMESTAMP((l.value ->> 'expiration')::bigint) AS expiration_ts,
    CASE
        WHEN l.value ->> 'expiration' IS NULL THEN FALSE
        WHEN TO_TIMESTAMP((l.value ->> 'expiration')::bigint) < NOW() THEN TRUE
        ELSE FALSE
    END AS is_expired,
    l.value ->> 'value_uri' AS value_uri,
    l.value ->> 'scheme_uri' AS scheme_uri
FROM
    position AS p,
    JSONB_ARRAY_ELEMENTS(p.labels -> 'values') AS l (value);

-- record latest migration
UPDATE public.meta_migration
SET migration_id = 24, migration_label = '024-util-asset-position-labels'
WHERE pk = 1;
