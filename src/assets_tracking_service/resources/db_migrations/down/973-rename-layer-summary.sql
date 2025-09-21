UPDATE public.record
SET
    summary
    = 'Resources pertaining to the '
    || '[BAS Assets Tracking Service](https://github.com/antarctica/assets-tracking-service), a service to track the '
    || 'location of BAS assets, including ships, aircraft, and vehicles.'
WHERE slug = 'ats_collection';

-- record latest migration
UPDATE public.meta_migration
SET migration_id = 26, migration_label = '026-latest-position-viz'
WHERE pk = 1;
