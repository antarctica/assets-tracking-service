CREATE TABLE IF NOT EXISTS public.position
(
    pk              INTEGER  GENERATED ALWAYS AS IDENTITY
        CONSTRAINT position_pk PRIMARY KEY,
    id              UUID NOT NULL UNIQUE DEFAULT generate_ulid(),
    asset_id        UUID NOT NULL,
        CONSTRAINT position_asset_id_fk
            FOREIGN KEY (asset_id)
            REFERENCES public.asset (id)
            ON DELETE CASCADE,
    geom            GEOMETRY(PointZ, 4326) NOT NULL,
    geom_dimensions INTEGER NOT NULL DEFAULT 2 CHECK (geom_dimensions IN (2, 3)),
    time_utc        timestamptz NOT NULL,
    velocity_ms     FLOAT,
    heading         FLOAT,
    labels          JSONB NOT NULL
        CONSTRAINT positions_labels_valid CHECK (are_labels_v1_valid(labels)),
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS position_id_idx ON public.position USING hash (id);
CREATE INDEX IF NOT EXISTS position_geom_idx ON public.position USING GIST (geom);
