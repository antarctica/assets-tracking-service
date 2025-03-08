-- https://gitlab.data.bas.ac.uk/MAGIC/assets-tracking-service/-/issues/38

CREATE TABLE IF NOT EXISTS public.record
(
    pk INTEGER GENERATED ALWAYS AS IDENTITY
    CONSTRAINT record_pk PRIMARY KEY,
    id UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),
    slug TEXT NOT NULL UNIQUE,
    edition TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    publication TIMESTAMPTZ NOT NULL DEFAULT now(),
    released TIMESTAMPTZ NOT NULL DEFAULT now(),
    update_frequency TEXT NOT NULL,
    gitlab_issue TEXT,
    extent_view TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE OR REPLACE TRIGGER record_updated_at_trigger
BEFORE INSERT OR UPDATE
ON public.record
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.table_constraints
        WHERE constraint_name = 'layer_record_slug_fk'
        AND table_name = 'layer'
    ) THEN
        ALTER TABLE public.layer
        ADD CONSTRAINT layer_record_slug_fk
        FOREIGN KEY (slug)
        REFERENCES public.record (slug)
        ON DELETE CASCADE;
    END IF;
END $$;

-- record latest migration
UPDATE public.meta_migration
SET migration_id = 17, migration_label = '017-metadata-record'
WHERE pk = 1;
