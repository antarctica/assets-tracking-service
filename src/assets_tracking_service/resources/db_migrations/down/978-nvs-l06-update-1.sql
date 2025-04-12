DELETE FROM public.nvs_l06_lookup
WHERE code IN ('97', '98');

-- record latest migration
UPDATE public.meta_migration
SET migration_id = 21, migration_label = '021-fix-dms-ddm-typo'
WHERE pk = 1;
