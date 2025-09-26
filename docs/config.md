# BAS Assets Tracking Service - Configuration

Application configuration is managed by the `assets_tracking_service.Config` class.

<!-- pyml disable md028 -->
> [!TIP]
> User configurable options can be defined using environment variables and/or an `.env` file, with environment
> variables taking precedence. Variables are prefixed with `ASSETS_TRACKING_SERVICE_` to avoid conflicts with other
> applications.
>
> E.g. use `ASSETS_TRACKING_SERVICE_FOO` to set a `FOO` option.

> [!NOTE]
> Config option values may be [Overridden](/docs/dev.md#pytest-env) in application tests.
<!-- pyml enable md028 -->

## Config options

<!-- pyml disable md013 -->
| Option                                            | Type            | Configurable | Required | Sensitive | Since Version | Summary                                                             | Default                                           | Example                                                   |
|---------------------------------------------------|-----------------|--------------|----------|-----------|---------------|---------------------------------------------------------------------|---------------------------------------------------|-----------------------------------------------------------|
| `DB_DSN`                                          | String          | Yes          | Yes      | Yes       | v0.3.x        | Postgres connection string                                          | *N/A*                                             | 'postgresql://username:password@$db.example.com/database' |
| `DB_DSN_SAFE`                                     | String          | No           | -        | -         | v0.3.x        | `DB_DSN` with sensitive elements redacted                           | *N/A*                                             | 'postgresql://username:REDACTED@$db.example.com/database' |
| `DB_DATABASE`                                     | String          | Yes          | No       | No        | v0.3.x        | Optional override for database in `DB_DSN`                          | *None*                                            | 'database_test'                                           |
| `ENABLE_EXPORTER_ARCGIS`                          | Boolean         | Yes          | No       | No        | v0.3.x        | Enables ArcGIS exporter if true                                     | *True*                                            | *True*                                                    |
| `ENABLE_EXPORTER_DATA_CATALOGUE`                  | Boolean         | Yes          | No       | No        | v0.5.x        | Enables Data Catalogue exporter if true                             | *True*                                            | *True*                                                    |
| `ENABLE_PROVIDER_AIRCRAFT_TRACKING`               | Boolean         | Yes          | No       | No        | v0.3.x        | Enables Aircraft Tracking provider if true                          | *True*                                            | *True*                                                    |
| `ENABLE_PROVIDER_GEOTAB`                          | Boolean         | Yes          | No       | No        | v0.3.x        | Enables Geotab provider if true                                     | *True*                                            | *True*                                                    |
| `ENABLE_PROVIDER_RVDAS`                           | Boolean         | Yes          | No       | No        | v0.6.x        | Enables RVDAS provider if true                                      | *True*                                            | *True*                                                    |
| `ENABLE_FEATURE_SENTRY`                           | Boolean         | Yes          | No       | No        | v0.4.x        | Enables Sentry monitoring if true                                   | *True*                                            | *True*                                                    |
| `ENABLED_EXPORTERS`                               | List of Strings | No           | -        | -         | v0.3.x        | Derived list of enabled exporter names                              | *N/A*                                             | '['arcgis']'                                              |
| `ENABLED_PROVIDERS`                               | List of Strings | No           | -        | -         | v0.3.x        | Derived list of enabled provider names                              | *N/A*                                             | '['geotab']'                                              |
| `EXPORTER_ARCGIS_USERNAME`                        | String          | Yes          | Yes [1]  | No        | v0.3.x        | See relevant exporter configuration                                 | *None*                                            | 'x'                                                       |
| `EXPORTER_ARCGIS_PASSWORD`                        | String          | Yes          | Yes [1]  | Yes       | v0.3.x        | See relevant exporter configuration                                 | *None*                                            | 'x'                                                       |
| `EXPORTER_ARCGIS_BASE_ENDPOINT_PORTAL`            | String          | Yes          | Yes [1]  | No        | v0.5.x        | See relevant exporter configuration                                 | *None*                                            | 'https://example.com'                                     |
| `EXPORTER_ARCGIS_BASE_ENDPOINT_SERVER`            | String          | Yes          | Yes [1]  | No        | v0.5.x        | See relevant exporter configuration                                 | *None*                                            | 'https://example.com/arcgis'                              |
| `EXPORTER_ARCGIS_FOLDER_NAME`                     | String          | No           | -        | -         | v0.5.x        | See relevant exporter configuration                                 | *N/A*                                             | 'example'                                                 |
| `EXPORTER_ARCGIS_GROUP_INFO`                      | Dictionary      | No           | -        | -         | v0.5.x        | See relevant exporter configuration                                 | *N/A*                                             | -                                                         |
| `EXPORTER_DATA_CATALOGUE_OUTPUT_PATH`             | Path            | Yes          | Yes [1]  | No        | v0.5.x        | See relevant exporter configuration                                 | *None*                                            | '/data/exports/records'                                   |
| `LOG_LEVEL`                                       | Number          | Yes          | No       | No        | v0.4.x        | Application logging level                                           | 30                                                | 20                                                        |
| `LOG_LEVEL_NAME`                                  | String          | No           | No       | Non       | v0.4.x        | Application logging level name                                      | 'WARNING'                                         | 'INFO'                                                    |
| `PROVIDER_AIRCRAFT_TRACKING_USERNAME`             | String          | Yes          | Yes [1]  | No        | v0.3.x        | See relevant provider configuration                                 | *None*                                            | 'x'                                                       |
| `PROVIDER_AIRCRAFT_TRACKING_PASSWORD`             | String          | Yes          | Yes [1]  | Yes       | v0.3.x        | See relevant provider configuration                                 | *None*                                            | 'x'                                                       |
| `PROVIDER_AIRCRAFT_TRACKING_PASSWORD_SAFE`        | String          | No           | -        | -         | v0.3.x        | `PROVIDER_AIRCRAFT_TRACKING_PASSWORD` with sensitive value redacted | *N/A*                                             | 'REDACTED'                                                |
| `PROVIDER_AIRCRAFT_TRACKING_API_KEY`              | String          | Yes          | Yes [1]  | Yes       | v0.3.x        | See relevant provider configuration                                 | *None*                                            | 'x'                                                       |
| `PROVIDER_AIRCRAFT_TRACKING_API_KEY_SAFE`         | String          | No           | -        | -         | v0.3.x        | `PROVIDER_AIRCRAFT_TRACKING_API_KEY` with sensitive value redacted  | *N/A*                                             | 'REDACTED'                                                |
| `PROVIDER_GEOTAB_USERNAME`                        | String          | Yes          | Yes [1]  | No        | v0.3.x        | See relevant provider configuration                                 | *None*                                            | 'x'                                                       |
| `PROVIDER_GEOTAB_PASSWORD`                        | String          | Yes          | Yes [1]  | Yes       | v0.3.x        | See relevant provider configuration                                 | *None*                                            | 'x'                                                       |
| `PROVIDER_GEOTAB_PASSWORD_SAFE`                   | String          | No           | -        | -         | v0.3.x        | `PROVIDER_GEOTAB_PASSWORD` with sensitive value redacted            | *N/A*                                             | 'REDACTED'                                                |
| `PROVIDER_GEOTAB_DATABASE`                        | String          | Yes          | Yes [1]  | No        | v0.3.x        | See relevant provider configuration                                 | *None*                                            | 'x'                                                       |
| `PROVIDER_GEOTAB_GROUP_NVS_L06_CODE_MAPPING`      | Dictionary      | No           | -        | -         | v0.3.x        | See relevant provider configuration                                 | *N/A*                                             | -                                                         |
| `PROVIDER_RVDAS_URL`                              | String          | Yes          | Yes [1]  | No        | v0.6.x        | See relevant provider configuration                                 | *None*                                            | 'https://example.com'                                     |
| `SENTRY_DSN`                                      | String          | No           | -        | -         | v0.4.x        | Sentry connection string (not considered sensitive)                 | *N/A*                                             | 'https://123@123.ingest.us.sentry.io/123'                 |
| `SENTRY_ENVIRONMENT`                              | String          | Yes          | No       | No        | v0.4.x        | [2]                                                                 | 'development'                                     | 'production'                                              |
| `SENTRY_MONITOR_SLUG_ATS_RUN`                     | String          | No           | -        | -         | v0.4.x        | Name of the relevant sentry cron monitor for tracking data refresh  | *N/A*                                             | 'ats-run'                                                 |
| `VERSION`                                         | String          | No           | -        | -         | v0.3.x        | Application package version                                         | *N/A*                                             | '0.3.0'                                                   |
<!-- pyml enable md013 -->

[1] If associated exporter, provider or feature is enabled.

- see [Exporters](/docs/exporters.md) documentation for relevant exporter configuration options
- see [Providers](/docs/providers.md) documentation for relevant provider configuration options

[2] Sets Sentry [environment](https://docs.sentry.io/platforms/python/configuration/environments/) name

[3] Sets Python logging level. May be set as either a numeric value or it's label (e.g. 'INFO' instead of 20).

## Config option types

All [Config Options](#config-options) are read as string values. They will then be parsed and cast to the listed type
by the `Config` class. E.g. `'true'` and `'True'` will be parsed as Python's `True` constant for a boolean option.

## Config validation

The `Config.validate()` method performs limited validation of configurable [Config Options](#config-options), raising
an exception if invalid.

This checks whether required options are set and can be parsed, it does not check whether access credentials work with
a remote service for example. These sorts of errors SHOULD be caught elsewhere in the application.

> [!TIP]
> Run the `config check` [CLI Command](/docs/cli-reference.md#config-commands) to validate the current configuration.

## Config listing

> [!TIP]
> Run the `config show` [CLI Command](/docs/cli-reference.md#config-commands) to display the current configuration.

## Generate an environment config file

Run the `config-init` [Development Task](/docs/dev.md#development-tasks) to generate a new `.env` file from the
`resources/env/.env.tpl` template.

> [!IMPORTANT]
> This uses the [1Password CLI](https://developer.1password.com/docs/cli/) to inject relevant secrets. You must have
> access to the MAGIC 1Password vault to run this task.

## Adding configuration options

See the [Development](/docs/dev.md#adding-configuration-options) documentation.
