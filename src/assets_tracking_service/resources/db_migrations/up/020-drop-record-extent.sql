-- https://gitlab.data.bas.ac.uk/MAGIC/assets-tracking-service/-/issues/127

DROP VIEW public.v_latest_assets_pos_extent;

ALTER TABLE public.record DROP COLUMN IF EXISTS extent_view;

-- record latest migration
UPDATE public.meta_migration
SET migration_id = 20, migration_label = '020-drop-record-extent'
WHERE pk = 1;
