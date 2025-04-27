-- https://gitlab.data.bas.ac.uk/MAGIC/assets-tracking-service/-/issues/119

CREATE TABLE IF NOT EXISTS public.meta_migration
(
    pk INTEGER
    CONSTRAINT meta_migration_pk PRIMARY KEY,
    migration_id INTEGER NOT NULL,
    migration_label TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE OR REPLACE TRIGGER meta_migration_updated_at_trigger
BEFORE INSERT OR UPDATE
ON public.meta_migration
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

-- record latest migration
INSERT INTO public.meta_migration (pk, migration_id, migration_label)
OVERRIDING SYSTEM VALUE
VALUES (1, 14, '014-migrations-tracking')
ON CONFLICT DO NOTHING;
