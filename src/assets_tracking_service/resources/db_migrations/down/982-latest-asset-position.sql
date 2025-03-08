DELETE FROM public.layer
WHERE slug = 'ats_latest_assets_position';

DELETE FROM public.record
WHERE slug = 'ats_latest_assets_position';

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'v_latest_assets_pos_geojson'
        AND column_name = 'geojson'
    ) THEN
        ALTER VIEW v_latest_assets_pos_geojson
        RENAME COLUMN geojson TO geojson_feature_collection;
    END IF;
END $$;

DROP VIEW IF EXISTS public.v_latest_assets_pos_extent;

-- record latest migration
UPDATE public.meta_migration
SET migration_id = 17, migration_label = '017-metadata-record'
WHERE pk = 1;
