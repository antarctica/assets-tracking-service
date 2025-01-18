CREATE OR REPLACE FUNCTION are_labels_v1_valid_asset(jsonb_labels jsonb) RETURNS boolean AS $$
DECLARE
    element jsonb;
    prefLabel_count INTEGER := 0;
BEGIN
    FOR element IN SELECT * FROM jsonb_array_elements(jsonb_labels -> 'values')
    LOOP
        -- must have exactly one label with scheme 'skos:prefLabel'
        IF element ->> 'scheme' = 'skos:prefLabel' THEN
            prefLabel_count := prefLabel_count + 1;
        END IF;
    END LOOP;

    IF prefLabel_count != 1 THEN
        RETURN FALSE;
    END IF;

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

CREATE TABLE IF NOT EXISTS public.asset
(
    pk integer GENERATED ALWAYS AS IDENTITY
    CONSTRAINT asset_pk PRIMARY KEY,
    id uuid NOT NULL UNIQUE DEFAULT generate_ulid(),
    labels jsonb NOT NULL
    CONSTRAINT asset_labels_valid_base CHECK (are_labels_v1_valid(labels))
    CONSTRAINT asset_labels_valid_asset CHECK (are_labels_v1_valid_asset(labels)),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS asset_id_idx ON public.asset USING hash (id);
