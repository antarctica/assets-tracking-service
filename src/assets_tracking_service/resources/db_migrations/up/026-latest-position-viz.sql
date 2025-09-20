DROP VIEW IF EXISTS public.v_latest_assets_pos_viz;
CREATE OR REPLACE VIEW public.v_latest_assets_pos_viz AS
SELECT
    asset_id,
    position_id,
    asset_pref_label AS name,  -- noqa: RF04
    asset_type_code AS type_code,
    asset_type_label AS type_label,
    time_utc,
    last_fetched_utc,
    geom_2d,
    lat_dd,
    lon_dd,
    lat_ddm,
    lon_ddm,
    elv_m,
    elv_ft,
    velocity_ms AS speed_ms,
    velocity_kmh AS speed_kmh,
    velocity_kn AS speed_kn,
    heading_d,
    fake_object_id
FROM v_latest_assets_pos;

GRANT SELECT ON public.v_latest_assets_pos_geojson TO assets_tracking_service_ro;
GRANT SELECT ON public.v_latest_assets_pos_viz TO assets_tracking_service_ro;

-- record latest migration
UPDATE public.meta_migration
SET migration_id = 26, migration_label = '026-latest-position-viz'
WHERE pk = 1;
