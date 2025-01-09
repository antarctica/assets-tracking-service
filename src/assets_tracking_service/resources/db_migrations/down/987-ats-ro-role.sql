REVOKE SELECT ON ALL TABLES IN SCHEMA public FROM assets_tracking_service_ro;
---- disabled as IT databases don't allow us to manage roles
-- DROP USER IF EXISTS assets_tracking_service_ro;
