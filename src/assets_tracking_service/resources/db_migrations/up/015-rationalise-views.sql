-- https://gitlab.data.bas.ac.uk/MAGIC/assets-tracking-service/-/issues/125

DROP VIEW IF EXISTS public.summary_latest;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_views WHERE viewname = 'summary_basic')
       AND NOT EXISTS (SELECT 1 FROM pg_views WHERE viewname = 'v_util_basic') THEN
        ALTER VIEW public.summary_basic RENAME TO v_util_basic;
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_views WHERE viewname = 'summary_export')
       AND NOT EXISTS (SELECT 1 FROM pg_views WHERE viewname = 'v_latest_asset_pos') THEN
        ALTER VIEW public.summary_export RENAME TO v_latest_asset_pos;
    END IF;
END $$;

-- rename and update view references
DROP VIEW IF EXISTS summary_geojson;
DROP VIEW IF EXISTS v_latest_asset_pos_geojson;
CREATE VIEW v_latest_asset_pos_geojson AS
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
    FROM v_latest_asset_pos
) AS features;

-- prevent old views being left behind if migrations are ran again
DROP VIEW IF EXISTS public.summary_basic;
DROP VIEW IF EXISTS public.summary_export;

-- record latest migration
UPDATE public.meta_migration
SET migration_id = 15, migration_label = '015-rationalise-views'
WHERE pk = 1;
