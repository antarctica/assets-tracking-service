CREATE OR REPLACE VIEW v_latest_assets_pos_extent AS
WITH latest_p_by_asset_ext AS (
    SELECT
        ST_EXTENT(geom_2d) AS bbox,
        MIN(time_utc)::timestamptz (0) AS min_time,
        MAX(time_utc)::timestamptz (0) AS max_time
    FROM v_latest_assets_pos
)

SELECT
    ST_XMIN(bbox) AS min_x,
    ST_YMIN(bbox) AS min_y,
    ST_XMAX(bbox) AS max_x,
    ST_YMAX(bbox) AS max_y,
    min_time AS min_t,
    max_time AS max_t
FROM latest_p_by_asset_ext;

ALTER TABLE public.record ADD COLUMN IF NOT EXISTS extent_view text;

UPDATE public.record
SET extent_view = 'v_latest_assets_pos_extent'
WHERE slug = 'ats_latest_assets_position';

-- record latest migration
UPDATE public.meta_migration
SET migration_id = 19, migration_label = '019-collection-record'
WHERE pk = 1;
