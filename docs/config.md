# BAS Assets Tracking Service - Configuration

The application configuration is defined by the [`Config`](../src/assets_tracking_service/config.py) class.

Configuration options can be defined using environment variables and/or an `.env` file. Where an option is set by both
an environment variable and in an `.env` file, the environment variable takes precedence.

All environment variables (whether defined directly or in an `.env` file) are prefixed with `ASSETS_TRACKING_SERVICE_`.
I.e. An option `FOO` should be set as `ASSETS_TRACKING_SERVICE_FOO`.

## Config options

| Option                                       | Type            | Configurable | Required | Sensitive | Summary                                                             | Default       | Example                                                   |
|----------------------------------------------|-----------------|--------------|----------|-----------|---------------------------------------------------------------------|---------------|-----------------------------------------------------------|
| `DB_DSN`                                     | String          | Yes          | Yes      | Yes       | Postgres connection string                                          | *N/A*         | 'postgresql://username:password@$db.example.com/database' |
| `DB_DSN_SAFE`                                | String          | No           | -        | -         | `DB_DSN` with sensitive elements redacted                           | *N/A*         | 'postgresql://username:REDACTED@$db.example.com/database' |
| `DB_DATABASE`                                | String          | Yes          | No       | No        | Optional override for database in `DB_DSN`                          | *None*        | 'database_test'                                           |
| `ENABLE_EXPORTER_ARCGIS`                     | Boolean         | Yes          | No       | No        | Enables ArcGIS exporter if true                                     | *True*        | *True*                                                    |
| `ENABLE_EXPORTER_DATA_CATALOGUE`             | Boolean         | Yes          | No       | No        | Enables Data Catalogue exporter if true                             | *True*        | *True*                                                    |
| `ENABLE_EXPORTER_GEOJSON`                    | Boolean         | Yes          | No       | No        | Enables GeoJSON exporter if true                                    | *True*        | *True*                                                    |
| `ENABLE_PROVIDER_AIRCRAFT_TRACKING`          | Boolean         | Yes          | No       | No        | Enables Aircraft Tracking provider if true                          | *True*        | *True*                                                    |
| `ENABLE_PROVIDER_GEOTAB`                     | Boolean         | Yes          | No       | No        | Enables Geotab provider if true                                     | *True*        | *True*                                                    |
| `ENABLE_FEATURE_SENTRY`                      | Boolean         | Yes          | No       | No        | Enables Sentry monitoring if true                                   | *True*        | *True*                                                    |
| `ENABLED_EXPORTERS`                          | List of Strings | No           | --       | --        | Derived list of enabled exporter names                              | *N/A*         | '['arcgis', 'geojson]'                                    |
| `ENABLED_PROVIDERS`                          | List of Strings | No           | --       | --        | Derived list of enabled provider names                              | *N/A*         | '['geotab']'                                              |
| `EXPORTER_ARCGIS_USERNAME`                   | String          | Yes          | Yes [1]  | No        | See relevant exporter configuration                                 | *None*        | 'x'                                                       |
| `EXPORTER_ARCGIS_PASSWORD`                   | String          | Yes          | Yes [1]  | Yes       | See relevant exporter configuration                                 | *None*        | 'x'                                                       |
| `EXPORTER_ARCGIS_ITEM_ID`                    | String          | Yes          | Yes [1]  | No        | See relevant exporter configuration                                 | *None*        | 'x'                                                       |
| `EXPORTER_DATA_CATALOGUE_OUTPUT_PATH`        | Path            | Yes          | Yes [1]  | No        | See relevant exporter configuration                                 | *None*        | '/data/exports/record.json'                               |
| `EXPORTER_DATA_CATALOGUE_RECORD_ID`          | String          | Yes          | Yes [1]  | No        | See relevant exporter configuration                                 | *None*        | 'x'                                                       |
| `EXPORTER_GEOJSON_OUTPUT_PATH`               | Path            | Yes          | Yes [1]  | No        | See relevant exporter configuration                                 | *None*        | '/data/exports/output.geojson'                            |
| `LOG_LEVEL`                                  | Number          | Yes          | No       | No        | Application logging level                                           | 30            | 20                                                        |
| `LOG_LEVEL_NAME`                             | String          | No           | No       | Non       | Application logging level name                                      | 'WARNING'     | 'INFO'                                                    |
| `PROVIDER_AIRCRAFT_TRACKING_USERNAME`        | String          | Yes          | Yes [1]  | No        | See relevant provider configuration                                 | *None*        | 'x'                                                       |
| `PROVIDER_AIRCRAFT_TRACKING_PASSWORD`        | String          | Yes          | Yes [1]  | Yes       | See relevant provider configuration                                 | *None*        | 'x'                                                       |
| `PROVIDER_AIRCRAFT_TRACKING_PASSWORD_SAFE`   | String          | No           | -        | -         | `PROVIDER_AIRCRAFT_TRACKING_PASSWORD` with sensitive value redacted | *N/A*         | 'REDACTED'                                                |
| `PROVIDER_AIRCRAFT_TRACKING_API_KEY`         | String          | Yes          | Yes [1]  | Yes       | See relevant provider configuration                                 | *None*        | 'x'                                                       |
| `PROVIDER_AIRCRAFT_TRACKING_API_KEY_SAFE`    | String          | No           | -        | -         | `PROVIDER_AIRCRAFT_TRACKING_API_KEY` with sensitive value redacted  | *N/A*         | 'REDACTED'                                                |
| `PROVIDER_GEOTAB_USERNAME`                   | String          | Yes          | Yes [1]  | No        | See relevant provider configuration                                 | *None*        | 'x'                                                       |
| `PROVIDER_GEOTAB_PASSWORD`                   | String          | Yes          | Yes [1]  | Yes       | See relevant provider configuration                                 | *None*        | 'x'                                                       |
| `PROVIDER_GEOTAB_PASSWORD_SAFE`              | String          | No           | -        | -         | `PROVIDER_GEOTAB_PASSWORD` with sensitive value redacted            | *N/A*         | 'REDACTED'                                                |
| `PROVIDER_GEOTAB_DATABASE`                   | String          | Yes          | Yes [1]  | No        | See relevant provider configuration                                 | *None*        | 'x'                                                       |
| `PROVIDER_GEOTAB_GROUP_NVS_L06_CODE_MAPPING` | Dictionary      | No           | -        | -         | See relevant provider configuration                                 | *N/A*         | -                                                         |
| `SENTRY_DSN`                                 | String          | No           | -        | -         | Sentry connection string (not considered sensitive)                 | *N/A*         | 'https://123@123.ingest.us.sentry.io/123'                 |
| `SENTRY_ENVIRONMENT`                         | String          | Yes          | No       | No        | [2]                                                                 | 'development' | 'production'                                              |
| `SENTRY_MONITOR_SLUG_ATS_RUN`                | String          | No           | -        | -         | Name of the relevant sentry cron monitor for tracking data refresh  | *N/A*         | 'ats-run'                                                 |
| `VERSION`                                    | String          | No           | -        | -         | Application package version                                         | *N/A*         | '0.3.0'                                                   |

[1] If associated exporter, provider or feature is enabled.

- see [Exporters](./exporters.md) documentation for relevant exporter configuration options
- see [Providers](./providers.md) documentation for relevant provider configuration options

[2] Sets Sentry [environment](https://docs.sentry.io/platforms/python/configuration/environments/) name

[3] Sets Python logging level. May be set as either a numeric value or it's label (e.g. 'INFO' instead of 20).

### Config option types

All configuration options (whether defined as an environment variable or in an `.env` file) are read as string values.
The type column in the above shows the data type each option will be parsed as, and cast to, by the
[`Config`](../src/assets_tracking_service/config.py) class.

E.g. a boolean option of `'true'`, `'True'`, etc. will be parsed as `True` in Python.

## Config validation

The `validate()` method performs basic validation of configurable options. This is limited to whether required options
are set and can be parsed. It does not check connection details can be used to connect to a service for example, as
this will be caught as a runtime error elsewhere in the application.

See the [CLI Reference](./cli-reference.md#config-commands) documentation for how to validate the current configuration.

## Config listing

The `dumps_safe()` method returns a typed dict of configurable and unconfigurable options. Where an option is
sensitive, a 'safe' version will be returned with sensitive values substituted.

See the [CLI Reference](./cli-reference.md#config-commands) documentation for how to display the current configuration.

## Adding configuration options

See the [Developing](./dev.md#adding-configuration-options) documentation.
