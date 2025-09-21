UPDATE public.record
SET
    summary
    = 'Resources pertaining to the '
    || '[BAS Assets Tracking Service](https://www.bas.ac.uk/project/assets-tracking-service), a service tracking the '
    || 'location of BAS assets, including ships, aircraft, and vehicles.'
WHERE slug = 'ats_collection';

-- record latest migration
UPDATE public.meta_migration
SET migration_id = 27, migration_label = '027-rename-layer-summary'
WHERE pk = 1;
