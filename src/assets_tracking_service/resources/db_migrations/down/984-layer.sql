DROP TRIGGER IF EXISTS layer_updated_at_trigger ON public.layer;

DROP TABLE IF EXISTS public.layer;

-- record latest migration
UPDATE public.meta_migration
SET migration_id = 15, migration_label = '015-rationalise-views'
WHERE pk = 1;
