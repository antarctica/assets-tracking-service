# BAS Assets Tracking Service - CLI Reference

## global commands

- `--version`: displays the installed application version
- `--help`: displays contextual information (available commands, subcommands or command parameters)

## `config` commands

- `ats-ctl config check`: [Validates](/docs/config.md#config-validation) configurable configuration options
- `ats-ctl config show`: displays the current application configuration with sensitive values redacted

## `data` commands

- `ats-ctl data fetch` - fetch active assets and their last known positions
- `ats-ctl data export` - export summary data for assets and their last known positions
- `ats-ctl data run` - combines the `data fetch` and `data export` commands

## `db` commands

- `ats-ctl db check`: verifies the application database can be accessed and all migrations have been applied
- `ats-ctl db migrate`: applies [Database Migrations](/docs/implementation.md#database-migrations) to the database
- `ats-ctl db rollback`: reverts [Database Migrations](/docs/implementation.md#database-migrations) to reset the database

## Adding CLI commands

See the [Developing](/docs/dev.md#adding-cli-command-groups) documentation.
