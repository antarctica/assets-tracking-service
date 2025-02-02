ASSETS_TRACKING_SERVICE_LOG_LEVEL="INFO"

ASSETS_TRACKING_SERVICE_DB_DSN="postgresql://[username]:[password]@[host]/[database]"

ASSETS_TRACKING_SERVICE_ENABLE_FEATURE_SENTRY="true"
ASSETS_TRACKING_SERVICE_SENTRY_ENVIRONMENT="development"

ASSETS_TRACKING_SERVICE_ENABLE_PROVIDER_GEOTAB="true"
ASSETS_TRACKING_SERVICE_ENABLE_PROVIDER_AIRCRAFT_TRACKING="true"

ASSETS_TRACKING_SERVICE_ENABLE_EXPORTER_ARCGIS="true"
ASSETS_TRACKING_SERVICE_ENABLE_EXPORTER_GEOJSON="true"

ASSETS_TRACKING_SERVICE_EXPORTER_ARCGIS_USERNAME="op://Infrastructure/vcadxkix3qwguf4trgspkcdxr4/username"
ASSETS_TRACKING_SERVICE_EXPORTER_ARCGIS_PASSWORD="op://Infrastructure/vcadxkix3qwguf4trgspkcdxr4/password"
ASSETS_TRACKING_SERVICE_EXPORTER_ARCGIS_ITEM_ID="op://Infrastructure/Assets Tracking Service - ArcGIS Layers/production summary export layer ID"  # not sensitive

ASSETS_TRACKING_SERVICE_PROVIDER_GEOTAB_USERNAME="op://Infrastructure/Assets Tracking Service - Geotab User/username"
ASSETS_TRACKING_SERVICE_PROVIDER_GEOTAB_PASSWORD="op://Infrastructure/Assets Tracking Service - Geotab User/password"
ASSETS_TRACKING_SERVICE_PROVIDER_GEOTAB_DATABASE="op://Infrastructure/Assets Tracking Service - Geotab User/database"

ASSETS_TRACKING_SERVICE_PROVIDER_AIRCRAFT_TRACKING_USERNAME="op://Infrastructure/vgyikhtrssx4h23vordfqduvuy/username"
ASSETS_TRACKING_SERVICE_PROVIDER_AIRCRAFT_TRACKING_PASSWORD="op://Infrastructure/vgyikhtrssx4h23vordfqduvuy/password"
ASSETS_TRACKING_SERVICE_PROVIDER_AIRCRAFT_TRACKING_API_KEY="op://Infrastructure/vgyikhtrssx4h23vordfqduvuy/API/API Key"

ASSETS_TRACKING_SERVICE_EXPORTER_GEOJSON_OUTPUT_PATH="/path/to/file.geojson"  # set to local path
