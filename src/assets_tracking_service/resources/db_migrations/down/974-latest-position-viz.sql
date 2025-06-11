DROP VIEW IF EXISTS public.v_latest_assets_pos_viz;

-- record latest migration
UPDATE public.meta_migration
SET migration_id = 25, migration_label = '025-fake-objectid'
WHERE pk = 1;
