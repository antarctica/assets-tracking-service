# BAS Assets Tracking Service - Development

## Local development environment

Requirements:

- Git
- Postgres + PostGIS
- [UV](https://docs.astral.sh/uv/)
- [Pre-commit](https://pre-commit.com)
- [1Password CLI](https://developer.1password.com/docs/cli/get-started/)
- [`pysync`](https://github.com/ankane/pgsync) (optional for database syncing)

Setup:

1. install tools [1]
1. configure access [2]
1. clone and setup project [3]
1. configure app [4]
1. configure local databases [5]

[1]

```shell
# required
% brew install git uv pre-commit 1password-cli
# optional
% brew install pgsync
```

[2]

You will need a BAS GitLab access token to install privately published app dependencies set in `~/.netrc`:

```
machine gitlab.data.bas.ac.uk login __token__ password {{token}}
```

[3]

```
% git clone https://gitlab.data.bas.ac.uk/MAGIC/assets-tracking-service.git
% cd assets-tracking-service/
% pre-commit install
% uv sync --all-groups
```

[4]

```
% op inject --in-file tpl/.env.tpl --out-file .env
```

Set configuration in `.env` as per [Configuration](./config.md) documentation.

[5]

From `psql -d postgres`:

```sql
CREATE USER assets_tracking_owner WITH PASSWORD 'xxx';
CREATE USER assets_tracking_service_ro WITH PASSWORD 'xxx';

CREATE DATABASE assets_tracking_dev OWNER assets_tracking_owner;
CREATE DATABASE assets_tracking_test OWNER assets_tracking_owner;

\c assets_tracking_dev
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;

\c assets_tracking_test
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
```

Where `xxx` are placeholder values.

If needed, you can [Populate](#syncing-development-database) the database from production.

## Running control CLI locally

```
% uv run ats-ctl --help
```

See the [CLI Reference](./cli-reference.md) documentation for available commands.

## Contributing

All changes except minor tweaks (typos, comments, etc.) MUST:

- be associated with an issue (either directly or by reference)
- be included in the [Change Log](../CHANGELOG.md)

Conventions:

- all deployable code should be contained in the `assets-tracking-service` package
- use `Path.resolve()` if displaying or logging file/directory paths
- use logging to record how actions progress, using the app [`logger`](../src/assets_tracking_service/log.py)
  - (e.g. `logger = logging.getLogger('app')`)

## Python version

The Python version is limited to 3.11 due to the `arcgis` dependency.

## Dependencies

### Vulnerability scanning

The [Safety](https://pypi.org/project/safety/) package checks dependencies for known vulnerabilities.

**WARNING!** As with all security tools, Safety is an aid for spotting common mistakes, not a guarantee of secure code.
In particular this is using the free vulnerability database, which is updated less frequently than paid options.

Checks are run automatically in [Continuous Integration](#continuous-integration). To check locally:

```
% uv run safety scan --detailed-output
```

## Linting

### Ruff

[Ruff](https://docs.astral.sh/ruff/) is used to lint and format Python files. Specific checks and config options are
set in [`pyproject.toml`](../pyproject.toml). Linting checks are run automatically in
[Continuous Integration](#continuous-integration).

To check linting locally:

```
% uv run ruff check src/ tests/
```

To run formatting locally:

```
% uv run ruff format src/ tests/
```

### SQLFluff

[SQLFluff](https://www.sqlfluff.com) is used to lint and format SQL files. Specific checks and config options are set
in [`pyproject.toml`](../pyproject.toml). Linting checks are run automatically in
[Continuous Integration](#continuous-integration).

To check linting locally:

```
% uv run sqlfluff lint src/assets_tracking_service/resources/db_migrations/
```

#### SQLFluff disabled rules

- [`ST06`](https://docs.sqlfluff.com/en/stable/reference/rules.html#rule-ST06)
  - where select elements should be ordered by complexity rather than preference/opinion
- [`ST10`](https://docs.sqlfluff.com/en/stable/reference/rules.html#rule-ST10)
  - where a condition such as `WHERE elem.label ->> 'scheme' = 'ats:last_fetched'` is incorrectly seen as a constant

### Static security analysis

Ruff is configured to run [Bandit](https://github.com/PyCQA/bandit), a static analysis tool for Python.

**WARNING!** As with all security tools, Bandit is an aid for spotting common mistakes, not a guarantee of secure code.
In particular this tool can't check for issues that are only be detectable when running code.

### Editorconfig

For consistency, it's strongly recommended to configure your IDE or other editor to use the
[EditorConfig](https://editorconfig.org/) settings defined in [`.editorconfig`](../.editorconfig).

### Pre-commit hook

A [Pre-Commit](https://pre-commit.com) hook is configured in [`.pre-commit-config.yaml`](/.pre-commit-config.yaml).

To run pre-commit checks against all files manually:

```
% pre-commit run --all-files
```

## Testing

### Pytest

[pytest](https://docs.pytest.org) with a number of plugins is used to test the application. Config options are set in
[`pyproject.toml`](../pyproject.toml). Tests checks are run automatically in
[Continuous Integration](#continuous-integration).

Tests for the application are defined in the
[`tests/assets_tracking_service_tests`](../tests/assets_tracking_service_tests) module.

To run tests locally:

```
% uv run pytest
```

### Pytest fixtures

Fixtures should be defined in [conftest.py](../tests/conftest.py), prefixed with `fx_` to indicate they are a fixture,
e.g.:

```python
import pytest

@pytest.fixture()
def fx_test_foo() -> str:
    """Example of a test fixture."""
    return 'foo'
```

### Pytest-cov test coverage

[`pytest-cov`](https://pypi.org/project/pytest-cov/) checks test coverage. We aim for 100% coverage but exemptions are
fine with good justification:

- `# pragma: no cover` - for general exemptions
- `# pragma: no branch` - where a conditional branch can never be called

[Continuous Integration](#continuous-integration) will check coverage automatically.

To run tests with coverage locally:

```
% uv run pytest --cov --cov-report=html
```

Where tests are added to ensure coverage, use the `cov` [mark](https://docs.pytest.org/en/7.1.x/how-to/mark.html), e.g:

```python
import pytest

@pytest.mark.cov()
def test_foo():
    assert 'foo' == 'foo'
```

### Pytest-recording

[pytest-recording](https://github.com/kiwicom/pytest-recording) is used to mock HTTP calls to provider APIs (ensuring
known values are used in tests).

To (re-)record all responses:

- update test fixtures to use real credentials
- run tests in record mode [1]
- update test fixtures to use fake/safe credentials
- review captured requests/responses to determine which to keep

[1]

```
% uv run pytest --record-mode=all
```

### Continuous Integration

All commits will trigger Continuous Integration using GitLab's CI/CD platform, configured in `.gitlab-ci.yml`.

### Test exports

See the [Exporters](./exporters.md#test-exports) documentation for available test exports with static values.

## Managing development database

If using a local Postgres database installed through homebrew (assuming `@17` is the version installed):

- manage service: `brew services [command] postgresql@14`
- view logs: `/usr/local/var/log/postgresql@17.log`

## Syncing development database

To sync data from the production database to development:

```
% op inject --in-file tpl/.pgsync.yml.tpl --out-file .pgsync.yml
% pgsync
```

## Adding configuration options

In the [`Config`](../src/assets_tracking_service/config.py) class:

- define a new property
- add property to `ConfigDumpSafe` typed dict
- add property to `dumps_safe` method
- if needed, add logic to `validate` method

In the [Configuration](./config.md) documentation:

- add to options table in alphabetical order
- if configurable, update the [`.env.example`](../.env.tpl) template and local `.env` file
- if configurable, update the [Ansible Deployment Playbook](./deploy.md#bas-it-ansible)
- if configurable, update the `[tool.pytest_env]` section in [`pyproject.toml`](../pyproject.toml)

In the [test_config.py](../tests/assets_tracking_service_tests/test_config.py) module:

- update the expected response in the `test_dumps_safe` method
- if validated, update the `test_`
- update or create tests as needed

## Adding database migrations

To create a migration `foo`:

```
% scripts/create-migration.py foo
```

This will create an `up` and `down` migration file in the
[`db_migrations`](../src/assets_tracking_service/resources/db_migrations) resource directory.

**Notes**:

- migration are numbered to ensure they apply in the correct order
- migrations should be grouped into logical units:
  - for a new entity, define the table and it's indexes, triggers, etc. in a single migration
  - define separate entities (even if related and part of the same change/feature) in separate migrations
- existing migrations MUST NOT be amended
  - if a column type changes, use an `ALTER` command in a new migration
- a
- include a comment with a related GitLab issue if applicable
- do not create roles in migrations
  - the app does not superuser privileges when deployed so migrations will fail
  - instead, check for the role and emit an exception to create manually if missing
- if adding a new table with static data, add to the `exclusions` in `.pgsync.yml` & `tpl/.pgsync.yml.tpl`

See the [Implementation](./implementation.md#database-migrations) documentation for more information on migrations.

## Adding CLI commands

If a new command group is needed:

- create a new module in the [`cli`](../src/assets_tracking_service/cli) package
- create a corresponding test module
- import and add the new command CLI in the [Root CLI](../src/assets_tracking_service/cli/__init__.py)

In the relevant command group module, create a new method:

- make sure the command decorator name and help are set correctly
- follow the conventions established in other commands for error handling and presenting data to the user
- add corresponding tests

In the [CLI Reference](./cli-reference.md) documentation:

- if needed, create a new command group section
- list and summarise the new command in the relevant group section

## Adding providers

**[WIP]** This section is a work in progress.

- add config option for enabling/disabling provider
- update `enabled_providers` property to include new provider
- add provider specific [config options](#adding-configuration-options) as needed
- create a new module in the [`providers`](../src/assets_tracking_service/providers) package
- create a new class inheriting from the [`BaseProvider`](../src/assets_tracking_service/providers/base_provider.py)
- implement methods required by the base class
- integrate into the ProvidersManager class
  - update the `_make_providers` method
- add tests as needed

## Adding exporters

**[WIP]** This section is a work in progress.

- add config option for enabling/disabling exporter
- update `enabled_exporters` property to include new exporter
- add exporter specific [config options](#adding-configuration-options) as needed
- if another exporter is required, update the config validation method to ensure the dependant exporter is enabled
- create a new module in the [`exporters`](../src/assets_tracking_service/exporters) package
- create a new class inheriting from the [`BaseExporter`](../src/assets_tracking_service/exporters/base_exporter.py)
- implement methods required by the base class
- integrate into the [ExportersManager](../src/assets_tracking_service/exporters/exporters_manager.py) class:
  - update the `_make_exporters` method
- add tests as needed:
  - create a new module in [`exporters`](../tests/assets_tracking_service_tests/exporters) test package
  - [`test_make_each_exporter`](../tests/assets_tracking_service_tests/exporters/test_exporters_manager.py)
  - add mock for exporter in [`test_export](../tests/assets_tracking_service_tests/exporters/test_exporters_manager.py)
