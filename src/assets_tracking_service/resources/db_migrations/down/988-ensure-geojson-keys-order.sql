DROP VIEW summary_geojson;

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
