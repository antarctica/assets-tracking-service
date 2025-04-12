INSERT INTO public.nvs_l06_lookup (code, label)
VALUES ('97', 'SNOWCAT'), ('98', 'SNOWMOBILE')
ON CONFLICT DO NOTHING;

-- record latest migration
UPDATE public.meta_migration
SET migration_id = 22, migration_label = '022-nvs-l06-update-1'
WHERE pk = 1;
