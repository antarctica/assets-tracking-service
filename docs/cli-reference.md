# BAS Assets Tracking Service - CLI Reference

## global commands

- `--version`: displays the installed application version
- `--help`: displays contextual information (available commands, subcommands or command parameters)

## `config` commands

- `ods-ctl config check`: [validates](./config.md#config-validation) configurable configuration options
- `ods-ctl config show`: displays the current application configuration with sensitive values redacted

## `data` commands

- `ats-ctl data fetch` - fetch active assets and last known positions

## `db` commands

- `ods-ctl db check`: verifies application database can be accessed
- `ods-ctl db migrate`: runs all [Database Migrations](./implementation.md#database-migrations) to configure database
- `ods-ctl db rollback`: reverts all [Database Migrations](./implementation.md#database-migrations) to reset database

## Adding CLI commands

See the [Developing](./dev.md#adding-cli-commands) documentation.
