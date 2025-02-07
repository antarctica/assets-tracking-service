DROP VIEW IF EXISTS v_latest_asset_pos_geojson;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_views WHERE viewname = 'v_latest_asset_pos')
       AND NOT EXISTS (SELECT 1 FROM pg_views WHERE viewname = 'summary_export') THEN
        ALTER VIEW public.v_latest_asset_pos RENAME TO summary_export;
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_views WHERE viewname = 'v_util_basic')
       AND NOT EXISTS (SELECT 1 FROM pg_views WHERE viewname = 'summary_basic') THEN
        ALTER VIEW public.v_util_basic RENAME TO summary_basic;
    END IF;
END $$;

CREATE VIEW summary_geojson AS
SELECT
    json_build_object(
        'type', 'FeatureCollection',
        'features', json_agg(feature)
    ) AS geojson_feature_collection
FROM (
    SELECT
        json_build_object(
            'type', 'Feature',
            'id', position_id,
            'geometry', st_asgeojson(geom_2d)::jsonb,
            'properties', json_build_object(
                'asset_id', asset_id,
                'position_id', position_id,
                'name', asset_pref_label,
                'type_code', asset_type_code,
                'type_label', asset_type_label,
                'time_utc', time_utc,
                'last_fetched_utc', last_fetched_utc,
                'lat_dd', lat_dd,
                'lon_dd', lon_dd,
                'lat_dms', lat_dms,
                'lon_dms', lon_dms,
                'elv_m', elv_m,
                'elv_ft', elv_ft,
                'speed_ms', velocity_ms,
                'speed_kmh', velocity_kmh,
                'speed_kn', velocity_kn,
                'heading_d', heading_d
            )
        ) AS feature
    FROM summary_export
) AS features;

CREATE VIEW summary_latest AS
WITH latest_p_by_asset AS (
    SELECT
        asset_id,
        max(time_utc) AS max_time
    FROM
        position
    GROUP BY
        asset_id
)

SELECT
    uuid_to_ulid(a.id) AS asset_id,
    jsonb_extract_path_text(asset_name.label, 'value') AS asset_pref_label,
    l06.label AS asset_type_label,
    jsonb_extract_path_text(asset_provider.label, 'value') AS asset_provider,

    uuid_to_ulid(p.id) AS position_id,
    p.time_utc::timestamptz (0) AS time_utc,
    st_y(p.geom) AS lat_dd,
    st_x(p.geom) AS lon_dd,
    CASE
        WHEN p.geom_dimensions = 2 THEN NULL
        ELSE round(st_z(p.geom)::numeric)
    END AS elv_m,
    CASE
        WHEN p.velocity_ms IS NULL THEN NULL
        ELSE round(p.velocity_ms::numeric * 3.6, 2)
    END AS velocity_kmh,
    p.heading AS heading_d,

    round(extract(EPOCH FROM (now() - time_utc::timestamptz))::numeric, 0) AS since_s,
    to_timestamp(
        jsonb_extract_path_text(
            asset_last_fetched.label,
            'value'
        )
        ::numeric
    )
    ::timestamptz (0) AS last_fetched_utc,
    now()::timestamptz (0) AS now_utc
FROM position AS p
INNER JOIN
    latest_p_by_asset
    ON
        p.asset_id = latest_p_by_asset.asset_id
        AND p.time_utc = latest_p_by_asset.max_time

INNER JOIN asset AS a ON p.asset_id = a.id
INNER JOIN LATERAL (
    SELECT elem.label
    FROM jsonb_array_elements(a.labels -> 'values') AS elem (label)
    WHERE elem.label ->> 'scheme' = 'skos:prefLabel'
) AS asset_name ON TRUE

INNER JOIN LATERAL (
    SELECT elem.label
    FROM jsonb_array_elements(a.labels -> 'values') AS elem (label)
    WHERE elem.label ->> 'scheme' = 'nvs:L06'
) AS l06_label ON TRUE
INNER JOIN LATERAL (
    SELECT
        nvs_l06_lookup.code,
        nvs_l06_lookup.label
    FROM nvs_l06_lookup
    WHERE nvs_l06_lookup.code = jsonb_extract_path_text(l06_label.label, 'value')
) AS l06 ON TRUE

INNER JOIN LATERAL (
    SELECT elem.label
    FROM jsonb_array_elements(a.labels -> 'values') AS elem (label)
    WHERE elem.label ->> 'scheme' = 'ats:provider_id'
) AS asset_provider ON TRUE

INNER JOIN LATERAL (
    SELECT elem.label
    FROM jsonb_array_elements(a.labels -> 'values') AS elem (label)
    WHERE elem.label ->> 'scheme' = 'ats:last_fetched'
) AS asset_last_fetched ON TRUE;

-- prevent old views being left behind if migrations are ran again
DROP VIEW IF EXISTS public.v_latest_asset_pos;
DROP VIEW IF EXISTS public.v_util_basic;

-- record latest migration
UPDATE public.meta_migration
SET migration_id = 14, migration_label = '014-migrations-tracking'
WHERE pk = 1;
