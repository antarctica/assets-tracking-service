-- https://gitlab.data.bas.ac.uk/MAGIC/assets-tracking-service/-/issues/38

CREATE TABLE IF NOT EXISTS public.layer
(
    pk INTEGER GENERATED ALWAYS AS IDENTITY
    CONSTRAINT layer_pk PRIMARY KEY,
    slug TEXT NOT NULL UNIQUE,
    source_view TEXT NOT NULL,
    agol_id_geojson TEXT UNIQUE,
    agol_id_feature TEXT UNIQUE,
    agol_id_feature_ogc TEXT UNIQUE,
    data_last_refreshed TIMESTAMPTZ,
    metadata_last_refreshed TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE OR REPLACE TRIGGER layer_updated_at_trigger
BEFORE INSERT OR UPDATE
ON public.layer
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

-- record latest migration
UPDATE public.meta_migration
SET migration_id = 16, migration_label = '016-layer'
WHERE pk = 1;
