DELETE FROM public.record
WHERE slug = 'ats_collection';

-- record latest migration
UPDATE public.meta_migration
SET migration_id = 18, migration_label = '018-latest-asset-position'
WHERE pk = 1;
