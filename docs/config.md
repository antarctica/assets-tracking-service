# BAS Assets Tracking Service - Configuration

The application configuration is defined by the [`Config`](../src/assets_tracking_service/config.py) class.

Configuration options can be defined using environment variables and/or an `.env` file. Where an option is set by both
an environment variable and in an `.env` file, the environment variable takes precedence.

All environment variables (whether defined directly or in an `.env` file) are prefixed with `ASSETS_TRACKING_SERVICE_`.
I.e. An option `FOO` should be set as `ASSETS_TRACKING_SERVICE_FOO`.

## Configurable options

| Option                                | Type    | Required | Sensitive | Summary                                    | Default | Example                                                   |
|---------------------------------------|---------|----------|-----------|--------------------------------------------|---------|-----------------------------------------------------------|
| `DB_DSN`                              | String  | Yes      | Yes       | Postgres connection string                 | *N/A*   | `postgresql://username:password@$db.example.com/database` |
| `DB_DATABASE`                         | String  | No       | No        | Optional override for database in `DB_DSN` | *None*  | `database_test`                                           |
| `ENABLE_PROVIDER_AIRCRAFT_TRACKING`   | Boolean | No       | No        | Enables Aircraft Tracking provider if true | 'True'  | 'True'                                                    |
| `ENABLE_PROVIDER_GEOTAB`              | Boolean | No       | No        | Enables Geotab provider if true            | 'True'  | 'True'                                                    |
| `PROVIDER_AIRCRAFT_TRACKING_USERNAME` | String  | Yes [1]  | No        | See relevant provider configuration        | *None*  | 'x'                                                       |
| `PROVIDER_AIRCRAFT_TRACKING_PASSWORD` | String  | Yes [1]  | Yes       | See relevant provider configuration        | *None*  | 'x'                                                       |
| `PROVIDER_AIRCRAFT_TRACKING_API_KEY`  | String  | Yes [1]  | Yes       | See relevant provider configuration        | *None*  | 'x'                                                       |
| `PROVIDER_GEOTAB_USERNAME`            | String  | Yes [1]  | No        | See relevant provider configuration        | *None*  | 'x'                                                       |
| `PROVIDER_GEOTAB_PASSWORD`            | String  | Yes [1]  | Yes       | See relevant provider configuration        | *None*  | 'x'                                                       |
| `PROVIDER_GEOTAB_DATABASE`            | String  | Yes [1]  | No        | See relevant provider configuration        | *None*  | 'x'                                                       |

[1] If associated provider is enabled.

### Configurable option types

All configuration options (whether defined as an environment variable or in an `.env` file) are read as
string values. The type column in the above show shows the data type each option will be parsed as and cast to within
the [`Config`](../src/assets_tracking_service/config.py) class.

E.g. a boolean option will be read as `'true'`, `'True'`, etc. and parsed as `True` in Python.

## Unconfigurable options

| Option                                       | Type            | Summary                                                             | Example                                                   |
|----------------------------------------------|-----------------|---------------------------------------------------------------------|-----------------------------------------------------------|
| `db_dsn_safe`                                | String          | `DB_DSN` with sensitive elements redacted                           | 'postgresql://username:REDACTED@$db.example.com/database' |
| `enabled_providers`                          | List of Strings | Derived list of enabled provider names                              | '['geotab']'                                              |
| `provider_aircraft_tracking_password_safe`   | String          | `PROVIDER_AIRCRAFT_TRACKING_PASSWORD` with sensitive value redacted | 'REDACTED'                                                |
| `provider_aircraft_tracking_api_key_safe`    | String          | `PROVIDER_AIRCRAFT_TRACKING_API_KEY` with sensitive value redacted  | 'REDACTED'                                                |
| `provider_geotab_password_safe`              | String          | `PROVIDER_GEOTAB_PASSWORD` with sensitive value redacted            | 'REDACTED'                                                |
| `provider_geotab_group_nvs_l06_code_mapping` | Dictionary      | See relevant provider configuration                                 | -                                                         |
| `version`                                    | String          | Application package version                                         | '0.3.0'                                                   |

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

See the [Developing](./dev.md#adding-configuration-options) documentation for how to add a new configuration option.
