-- https://gitlab.data.bas.ac.uk/MAGIC/assets-tracking-service/-/issues/38

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

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'v_latest_assets_pos_geojson'
        AND column_name = 'geojson_feature_collection'
    ) THEN
        ALTER VIEW v_latest_assets_pos_geojson
        RENAME COLUMN geojson_feature_collection TO geojson;
    END IF;
END $$;

-- to handle `extent_view` being dropped in future migration and so error if migrations are re-applied to a migrated DB
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'record'
        AND column_name = 'extent_view'
    ) THEN
        INSERT INTO public.record (slug, edition, title, summary, update_frequency, gitlab_issue, extent_view)
        VALUES (
            'ats_latest_assets_position',
            '1',
            'Latest assets position - BAS Assets Tracking Service',
            'The last known position of all assets tracked by the BAS Assets Tracking Service.',
            'continual',
            'https://gitlab.data.bas.ac.uk/MAGIC/assets-tracking-service/-/issues/37',
            'v_latest_assets_pos_extent'
        )
        ON CONFLICT (slug)
        DO NOTHING;
    ELSE
        INSERT INTO public.record (slug, edition, title, summary, update_frequency, gitlab_issue)
        VALUES (
            'ats_latest_assets_position',
            '1',
            'Latest assets position - BAS Assets Tracking Service',
            'The last known position of all assets tracked by the BAS Assets Tracking Service.',
            'continual',
            'https://gitlab.data.bas.ac.uk/MAGIC/assets-tracking-service/-/issues/37'
        )
        ON CONFLICT (slug)
        DO NOTHING;
    END IF;
END $$;

INSERT INTO public.layer (slug, source_view)
VALUES (
    'ats_latest_assets_position',
    'v_latest_assets_pos'
)
ON CONFLICT (slug)
DO NOTHING;

-- record latest migration
UPDATE public.meta_migration
SET migration_id = 18, migration_label = '018-latest-asset-position'
WHERE pk = 1;
