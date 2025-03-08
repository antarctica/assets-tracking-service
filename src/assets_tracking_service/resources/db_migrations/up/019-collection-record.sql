-- https://gitlab.data.bas.ac.uk/MAGIC/assets-tracking-service/-/issues/128

-- to handle `extent_view` being dropped in future migration and so error if migrations are re-applied to a migrated DB
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'record'
        AND column_name = 'extent_view'
    ) THEN
        INSERT INTO public.record (slug, edition, title, summary, update_frequency, gitlab_issue, extent_view)
        VALUES (
            'ats_collection',
            '2',
            'BAS Assets Tracking Service',
            'Resources pertaining to the [BAS Assets Tracking Service](https://github.com/antarctica/assets-tracking-service), a service to track the location of BAS assets, including ships, aircraft, and vehicles.',
            'asNeeded',
            'https://gitlab.data.bas.ac.uk/MAGIC/assets-tracking-service/-/issues/128',
            '-'
        )
        ON CONFLICT (slug)
        DO NOTHING;
    ELSE
        INSERT INTO public.record (slug, edition, title, summary, update_frequency, gitlab_issue)
        VALUES (
            'ats_collection',
            '2',
            'BAS Assets Tracking Service',
            'Resources pertaining to the [BAS Assets Tracking Service](https://github.com/antarctica/assets-tracking-service), a service to track the location of BAS assets, including ships, aircraft, and vehicles.',
            'asNeeded',
            'https://gitlab.data.bas.ac.uk/MAGIC/assets-tracking-service/-/issues/128'
        )
        ON CONFLICT (slug)
        DO NOTHING;
    END IF;
END $$;

INSERT INTO public.layer (slug, source_view)
VALUES (
    'ats_latest_assets_position',
    'v_latest_assets_pos_geojson'
)
ON CONFLICT (slug)
DO NOTHING;

-- record latest migration
UPDATE public.meta_migration
SET migration_id = 19, migration_label = '019-collection-record'
WHERE pk = 1;
