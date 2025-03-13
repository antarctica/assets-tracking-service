-- https://gitlab.data.bas.ac.uk/MAGIC/assets-tracking-service/-/issues/135

DROP VIEW IF EXISTS v_latest_assets_pos_geojson;

ALTER VIEW v_latest_assets_pos RENAME COLUMN lat_dms TO lat_ddm;
ALTER VIEW v_latest_assets_pos RENAME COLUMN lon_dms TO lon_ddm;

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


-- record latest migration
UPDATE public.meta_migration
SET migration_id = 21, migration_label = '021-fix-dms-ddm-typo'
WHERE pk = 1;
