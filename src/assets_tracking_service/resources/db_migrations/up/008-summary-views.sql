CREATE OR REPLACE VIEW summary_basic AS
SELECT
    uuid_to_ulid(a.id) as asset_id,
    uuid_to_ulid(p.id) as position_id,
    p.time_utc::timestamptz(0) as time_utc,
    p.geom as geom_3d,
    p.geom_dimensions as geom_dimensions,
    p.velocity_ms as velocity_ms,
    p.heading as heading_d
FROM position as p
JOIN
    (
        SELECT
            asset_id,
            MAX(time_utc) as max_time
        FROM
            position
        GROUP BY asset_id
    ) latest_p_by_asset
    ON
        p.asset_id = latest_p_by_asset.asset_id AND
        p.time_utc = latest_p_by_asset.max_time
INNER JOIN asset as a ON p.asset_id = a.id;

CREATE OR REPLACE VIEW summary_latest AS
SELECT
    uuid_to_ulid(a.id) as asset_id,
    jsonb_extract_path_text(asset_name.label, 'value') as asset_pref_label,
    l06.label AS asset_type_label,
    jsonb_extract_path_text(asset_provider.label, 'value') as asset_provider,

    uuid_to_ulid(p.id) as position_id,
    p.time_utc::timestamptz(0) as time_utc,
    st_y(p.geom) as lat_dd,
    st_x(p.geom) as lon_dd,
    CASE
        WHEN p.geom_dimensions = 2 THEN NULL
        ELSE ROUND(st_z(p.geom)::numeric)
    END as elv_m,
    CASE
        WHEN p.velocity_ms IS NULL THEN NULL
        ELSE ROUND(p.velocity_ms::numeric * 3.6, 2)
    END as velocity_kmh,
    p.heading as heading_d,

    ROUND(EXTRACT(EPOCH FROM (NOW() - time_utc::timestamptz))::numeric, 0) as since_s,
    to_timestamp(jsonb_extract_path_text(asset_last_fetched.label, 'value')::numeric)::timestamptz(0) as last_fetched_utc,
    NOW()::timestamptz(0) as now_utc
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
    WHERE elem.label->>'scheme' = 'ats:provider_id'
) as asset_provider ON TRUE

JOIN LATERAL (
    SELECT label
    FROM jsonb_array_elements(a.labels->'values') as elem(label)
    WHERE elem.label->>'scheme' = 'ats:last_fetched'
) as asset_last_fetched ON TRUE;

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
    CASE
        WHEN p.geom_dimensions = 2 THEN NULL
        ELSE ROUND(st_z(p.geom)::numeric)
    END as elv_m,
    CASE
        WHEN p.velocity_ms IS NULL THEN NULL
        ELSE ROUND(p.velocity_ms::numeric * 3.6, 2)
    END as velocity_kmh,
    p.heading as heading_d
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
            'time', time_utc,
            'last_fetched', last_fetched_utc,
            'lat', lat_dd,
            'lon', lon_dd,
            'elv', elv_m,
            'speed', velocity_kmh,
            'heading', heading_d
        )
    ) AS feature
    FROM summary_export
) AS features;
