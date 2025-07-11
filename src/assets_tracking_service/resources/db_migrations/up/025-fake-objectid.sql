DROP VIEW IF EXISTS public.v_latest_assets_pos_viz;
DROP VIEW IF EXISTS public.v_latest_assets_pos_geojson;
DROP VIEW IF EXISTS public.v_latest_assets_pos;

-- add fake_object_id column for ArcGIS compatibility
CREATE OR REPLACE VIEW public.v_latest_assets_pos AS
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
    l06.code AS asset_type_code,
    l06.label AS asset_type_label,

    uuid_to_ulid(p.id) AS position_id,
    p.time_utc::timestamptz (0) AS time_utc,
    to_timestamp(
        jsonb_extract_path_text(
            asset_last_fetched.label,
            'value'
        )::numeric
    )::timestamptz (0) AS last_fetched_utc,
    st_force2d(p.geom) AS geom_2d,
    st_y(p.geom) AS lat_dd,
    st_x(p.geom) AS lon_dd,
    (geom_as_ddm(p.geom)).y AS lat_ddm,
    (geom_as_ddm(p.geom)).x AS lon_ddm,
    CASE
        WHEN p.geom_dimensions = 2 THEN NULL
        ELSE round(st_z(p.geom)::numeric)
    END AS elv_m,
    CASE
        WHEN p.geom_dimensions = 2 THEN NULL
        ELSE round(st_z(p.geom)::numeric * 3.281)
    END AS elv_ft,
    CASE
        WHEN p.velocity_ms IS NULL THEN NULL
        ELSE round(p.velocity_ms::numeric, 1)
    END AS velocity_ms,
    CASE
        WHEN p.velocity_ms IS NULL THEN NULL
        ELSE round(p.velocity_ms::numeric * 3.6, 1)
    END AS velocity_kmh,
    CASE
        WHEN p.velocity_ms IS NULL THEN NULL
        ELSE round(p.velocity_ms::numeric * 1.944, 1)
    END AS velocity_kn,
    round(p.heading::numeric, 1) AS heading_d,
    ('x' || replace(a.id::text, '-', ''))::bit(64)::bigint AS fake_object_id
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
    WHERE elem.label ->> 'scheme' = 'skos:prefLabel' AND elem.label ->> 'expiration' IS NULL
    ORDER BY (elem.label ->> 'creation')::bigint DESC
    LIMIT 1
) AS asset_name ON TRUE

INNER JOIN LATERAL (
    SELECT elem.label
    FROM jsonb_array_elements(a.labels -> 'values') AS elem (label)
    WHERE elem.label ->> 'scheme' = 'nvs:L06' AND elem.label ->> 'expiration' IS NULL
    ORDER BY (elem.label ->> 'creation')::bigint DESC
    LIMIT 1
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
    WHERE elem.label ->> 'scheme' = 'ats:last_fetched'
) AS asset_last_fetched ON TRUE;

GRANT SELECT ON public.v_latest_assets_pos TO assets_tracking_service_ro;

-- no change to this view
CREATE VIEW v_latest_assets_pos_geojson AS
SELECT
    json_build_object(
        'type', 'FeatureCollection',
        'features', json_agg(feature)
    ) AS geojson
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
                'lat_ddm', lat_ddm,
                'lon_ddm', lon_ddm,
                'elv_m', elv_m,
                'elv_ft', elv_ft,
                'speed_ms', velocity_ms,
                'speed_kmh', velocity_kmh,
                'speed_kn', velocity_kn,
                'heading_d', heading_d
            )
        ) AS feature
    FROM v_latest_assets_pos
) AS features;

GRANT SELECT ON public.v_latest_assets_pos_geojson TO assets_tracking_service_ro;

-- record latest migration
UPDATE public.meta_migration
SET migration_id = 25, migration_label = '025-fake-objectid'
WHERE pk = 1;
