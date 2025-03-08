ALTER TABLE public.layer
DROP CONSTRAINT IF EXISTS layer_record_slug_fk;

DROP TRIGGER IF EXISTS record_updated_at_trigger ON public.record;

DROP TABLE IF EXISTS public.record;

-- record latest migration
UPDATE public.meta_migration
SET migration_id = 16, migration_label = '016-layer'
WHERE pk = 1;
