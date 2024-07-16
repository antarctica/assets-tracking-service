-- see https://gitlab.data.bas.ac.uk/MAGIC/assets-tracking-service/-/issues/36 for background

DROP VIEW summary_geojson;
DROP VIEW summary_export;

CREATE OR REPLACE VIEW summary_export AS
SELECT
    uuid_to_ulid(a.id) as asset_id,
    jsonb_extract_path_text(asset_name.label, 'value') as asset_pref_label,
    l06.code AS asset_type_code,
    l06.label AS asset_type_label,

    uuid_to_ulid(p.id) as position_id,
    p.time_utc::timestamptz(0) as time_utc,
    to_timestamp(jsonb_extract_path_text(asset_last_fetched.label, 'value')::numeric)::timestamptz(0) as last_fetched_utc,

    st_force2d(p.geom) as geom_2d,
    st_y(p.geom) as lat_dd,
    st_x(p.geom) as lon_dd,
    (geom_as_ddm(geom)).y as lat_dms,
    (geom_as_ddm(geom)).x as lon_dms,
    CASE
        WHEN p.geom_dimensions = 2 THEN NULL
        ELSE ROUND(st_z(p.geom)::numeric)
    END as elv_m,
    CASE
        WHEN p.geom_dimensions = 2 THEN NULL
        ELSE ROUND(st_z(p.geom)::numeric * 3.281)
    END as elv_ft,
    CASE
        WHEN p.velocity_ms IS NULL THEN NULL
        ELSE ROUND(p.velocity_ms::numeric, 1)
    END as velocity_ms,
    CASE
        WHEN p.velocity_ms IS NULL THEN NULL
        ELSE ROUND(p.velocity_ms::numeric * 3.6, 1)
    END as velocity_kmh,
    CASE
        WHEN p.velocity_ms IS NULL THEN NULL
        ELSE ROUND(p.velocity_ms::numeric * 1.944, 1)
    END as velocity_kn,
    ROUND(p.heading::numeric, 1) as heading_d
FROM position as p
    JOIN
    (SELECT
        asset_id,
        MAX(time_utc) as max_time
     FROM
        position
     GROUP BY
        asset_id) latest_p_by_asset
ON
    p.asset_id = latest_p_by_asset.asset_id AND
    p.time_utc = latest_p_by_asset.max_time

INNER JOIN asset as a ON p.asset_id = a.id
    JOIN LATERAL (
    SELECT label
    FROM jsonb_array_elements(a.labels->'values') as elem(label)
    WHERE elem.label->>'scheme' = 'skos:prefLabel'
) as asset_name ON TRUE

JOIN LATERAL (
    SELECT label
    FROM jsonb_array_elements(a.labels->'values') as elem(label)
    WHERE elem.label->>'scheme' = 'nvs:L06'
) as l06_label ON TRUE
JOIN LATERAL (
    SELECT code, label
    FROM nvs_l06_lookup WHERE code = jsonb_extract_path_text(l06_label.label, 'value')
) as l06 ON TRUE

JOIN LATERAL (
    SELECT label
    FROM jsonb_array_elements(a.labels->'values') as elem(label)
    WHERE elem.label->>'scheme' = 'ats:last_fetched'
) as asset_last_fetched ON TRUE;

CREATE OR REPLACE VIEW summary_geojson AS
SELECT jsonb_build_object(
    'type', 'FeatureCollection',
    'features', jsonb_agg(feature)
) AS geojson_feature_collection
FROM (
    SELECT jsonb_build_object(
        'type', 'Feature',
        'id', position_id,
        'geometry', ST_AsGeoJSON(geom_2d)::jsonb,
        'properties', jsonb_build_object(
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
