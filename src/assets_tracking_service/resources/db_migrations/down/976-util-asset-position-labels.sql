DROP VIEW IF EXISTS v_util_position_label;
DROP VIEW IF EXISTS v_util_asset_label;

-- record latest migration
UPDATE public.meta_migration
SET migration_id = 23, migration_label = '023-most-recent-l06'
WHERE pk = 1;
