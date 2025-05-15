ASSETS_TRACKING_SERVICE_LOG_LEVEL="INFO"

ASSETS_TRACKING_SERVICE_DB_DSN="postgresql://[username]:[password]@[host]/[database]"

ASSETS_TRACKING_SERVICE_ENABLE_FEATURE_SENTRY="true"
ASSETS_TRACKING_SERVICE_SENTRY_ENVIRONMENT="development"

ASSETS_TRACKING_SERVICE_ENABLE_PROVIDER_GEOTAB="true"
ASSETS_TRACKING_SERVICE_ENABLE_PROVIDER_AIRCRAFT_TRACKING="true"
ASSETS_TRACKING_SERVICE_ENABLE_PROVIDER_RVDAS="true"

ASSETS_TRACKING_SERVICE_ENABLE_EXPORTER_ARCGIS="true"
ASSETS_TRACKING_SERVICE_ENABLE_EXPORTER_DATA_CATALOGUE="true"

ASSETS_TRACKING_SERVICE_PROVIDER_GEOTAB_USERNAME="op://Infrastructure/Assets Tracking Service - Geotab User/username"
ASSETS_TRACKING_SERVICE_PROVIDER_GEOTAB_PASSWORD="op://Infrastructure/Assets Tracking Service - Geotab User/password"
ASSETS_TRACKING_SERVICE_PROVIDER_GEOTAB_DATABASE="op://Infrastructure/Assets Tracking Service - Geotab User/database"

ASSETS_TRACKING_SERVICE_PROVIDER_AIRCRAFT_TRACKING_USERNAME="op://Infrastructure/vgyikhtrssx4h23vordfqduvuy/username"
ASSETS_TRACKING_SERVICE_PROVIDER_AIRCRAFT_TRACKING_PASSWORD="op://Infrastructure/vgyikhtrssx4h23vordfqduvuy/password"
ASSETS_TRACKING_SERVICE_PROVIDER_AIRCRAFT_TRACKING_API_KEY="op://Infrastructure/vgyikhtrssx4h23vordfqduvuy/API/API Key"

ASSETS_TRACKING_SERVICE_PROVIDER_RVDAS_URL="op://Infrastructure/Assets Tracking - SDA RVDAS OGC endpoint/password"

ASSETS_TRACKING_SERVICE_EXPORTER_GEOJSON_OUTPUT_PATH="./exports/file.geojson"  # set to local file

ASSETS_TRACKING_SERVICE_EXPORTER_DATA_CATALOGUE_OUTPUT_PATH="./exports/site"  # set to local dir
ASSETS_TRACKING_SERVICE_EXPORTER_DATA_CATALOGUE_AWS_ACCESS_ID="op://Infrastructure/Assets Tracking Service - Catalogue Test/username"
ASSETS_TRACKING_SERVICE_EXPORTER_DATA_CATALOGUE_AWS_ACCESS_SECRET="op://Infrastructure/Assets Tracking Service - Catalogue Test/credential"
ASSETS_TRACKING_SERVICE_EXPORTER_DATA_CATALOGUE_AWS_S3_BUCKET="op://Infrastructure/Assets Tracking Service - Catalogue Test/bucket"
ASSETS_TRACKING_SERVICE_EXPORTER_DATA_CATALOGUE_ITEM_CONTACT_ENDPOINT="op://Shared/SCAR ADD Metadata Toolbox - Power Automate item feedback flow/password"
ASSETS_TRACKING_SERVICE_EXPORTER_DATA_CATALOGUE_PLAUSIBLE_DOMAIN="op://Infrastructure/SCAR ADD Metadata Toolbox - Plausible domain/password"
ASSETS_TRACKING_SERVICE_EXPORTER_DATA_CATALOGUE_SENTRY_SRC="op://Infrastructure/SCAR ADD Metadata Toolbox - Sentry JS CDN URL/password"

ASSETS_TRACKING_SERVICE_EXPORTER_ARCGIS_USERNAME="op://Infrastructure/vcadxkix3qwguf4trgspkcdxr4/username"
ASSETS_TRACKING_SERVICE_EXPORTER_ARCGIS_PASSWORD="op://Infrastructure/vcadxkix3qwguf4trgspkcdxr4/password"
ASSETS_TRACKING_SERVICE_EXPORTER_ARCGIS_BASE_ENDPOINT_PORTAL="op://Infrastructure/vcadxkix3qwguf4trgspkcdxr4/Endpoints/Portal base endpoint"
ASSETS_TRACKING_SERVICE_EXPORTER_ARCGIS_BASE_ENDPOINT_SERVER="op://Infrastructure/vcadxkix3qwguf4trgspkcdxr4/Endpoints/Server base endpoint"
