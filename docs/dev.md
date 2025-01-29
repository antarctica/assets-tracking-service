# BAS Assets Tracking Service - Development

## Local development environment

Requirements:

* Python 3.11 ([pyenv](https://github.com/pyenv/pyenv) recommended)
* [Poetry](https://python-poetry.org/docs/#installation) (1.8+)
* Git (`brew install git`)
* Postgres with PostGIS extension (`brew install postgis`)
* Pre-commit (`pipx install pre-commit`)

**Note:** You will need a BAS GitLab access token with at least the `read_api`scope to install this package as it
depends on privately published dependencies.

Clone project:

```
$ git clone https://gitlab.data.bas.ac.uk/MAGIC/assets-tracking-service.git
$ cd assets-tracking-service
```

Install project:

```
$ poetry config http-basic.ats-air __token__
$ poetry install
$ poetry run python -m pip install --no-deps arcgis
```

Create databases:

```
$ createdb assets-tracking-dev
$ createdb assets-tracking-test
```

Set configuration as per the [Configuration](./config.md) documentation:

```
$ cp .env.example .env
```

Install pre-commit hooks:

```
$ pre-commit install
```

## Running control CLI locally

```
$ poetry run python ats-ctl ...
```

See the [CLI Reference](./cli-reference.md) documentation for available commands.

## Contributing

All changes except minor tweaks (typos, comments, etc.) MUST:

- be associated with an issue (either directly or by reference)
- be included in the [Change Log](../CHANGELOG.md)

Conventions:

- all deployable code should be contained in the `assets-tracking-service` package
- use `Path.resolve()` if displaying or logging file/directory paths
- use logging to record how actions progress, using the app [`logger`](../src/assets_tracking_service/logging.py)
  - (e.g. `logger = logging.getLogger('app')`)

## Python version

The Python version is limited to 3.11 due to the `arcgis` dependency.

## Dependencies

### `arcgis` dependency

The [`arcgis`](https://developers.arcgis.com/python/) package (ArcGIS API for Python) is not included in the main
package dependencies because it is incompatible with Poetry and depends on a large number of dependencies that we don't
need.

This dependency therefore needs to be installed manually after the main project dependencies are installed.

### Vulnerability scanning

The [Safety](https://pypi.org/project/safety/) package is used to check dependencies against known vulnerabilities.

**WARNING!** As with all security tools, Safety is an aid for spotting common mistakes, not a guarantee of secure code.
In particular this is using the free vulnerability database, which is updated less frequently than paid options.

Checks are run automatically in [Continuous Integration](#continuous-integration). To check locally:

```
$ poetry run safety scan
```

## Linting

### Ruff

[Ruff](https://docs.astral.sh/ruff/) is used to lint and format Python files. Specific checks and config options are
set in [`pyproject.toml`](../pyproject.toml). Linting checks are run automatically in
[Continuous Integration](#continuous-integration).

To check linting locally:

```
$ poetry run ruff check src/ tests/
```

To run and check formatting locally:

```
$ poetry run ruff format src/ tests/
$ poetry run ruff format --check src/ tests/
```

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
$ pre-commit run --all-files
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
$ poetry run pytest
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

[`pytest-cov`](https://pypi.org/project/pytest-cov/) checks test coverage. We aim for 100% coverage but exemptions are fine with good justification:

- `# pragma: no cover` - for general exemptions
- `# pragma: no branch` - where a conditional branch can never be called

[Continuous Integration](#continuous-integration) will check coverage automatically.

To run tests with coverage locally:

```
$ poetry run pytest --cov --cov-report=html
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
- run tests in record mode: `poetry run pytest --record-mode=all`
- update test fixtures to use fake/safe credentials
- review captured requests/responses to determine which to keep

### Continuous Integration

All commits will trigger Continuous Integration using GitLab's CI/CD platform, configured in `.gitlab-ci.yml`.

## Managing development database

If using a local Postgres database installed through homebrew (assuming `@14` is the version installed):

- manage service: `brew services [command] postgresql@14`
- view logs: `/usr/local/var/log/postgresql@14.log`

## Adding configuration options

In the [`Config`](../src/assets_tracking_service/config.py) class:

- define a new property (use upper case name if configurable by the end user)
- add property to `ConfigDumpSafe` typed dict
- add property to `dumps_safe` method
- if needed, add logic to `validate` method

In the [Configuration](./config.md) documentation:

- add to either configurable or unconfigurable options table in alphabetical order
- update the [`.env.example`](../.env.example) template and local `.env` file
- update the `deploy` job in the [`.gitlab-ci.yml`](../.gitlab-ci.yml) file
- update the `[tool.pytest_env]` section in [`pyproject.toml`](../pyproject.toml)

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
- include a comment with a related GitLab issue if applicable
- do not create roles in migrations
  - the app does not superuser privileges when deployed so migrations will fail
  - instead, check for the role and emit an exception to create manually if missing

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
