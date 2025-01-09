-- https://gitlab.data.bas.ac.uk/MAGIC/assets-tracking-service/-/issues/48

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT FROM pg_catalog.pg_roles
        WHERE rolname = 'assets_tracking_service_ro') THEN

        CREATE ROLE assets_tracking_service_ro;
    END IF;
END
$$;

GRANT SELECT ON ALL TABLES IN SCHEMA public TO assets_tracking_service_ro;
