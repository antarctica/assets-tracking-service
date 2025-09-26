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

1. install tools (`brew install git uv pre-commit 1password-cli postgis pgsync`)
1. configure access to private dependencies [1]
1. clone and setup project [2]
1. [generate](/docs/config.md#generate-an-environment-config-file) an `.env` file
1. configure local databases [3]

[1]

You will need a BAS GitLab access token to install privately published app dependencies set in `~/.netrc`:

```text
machine gitlab.data.bas.ac.uk login __token__ password {{token}}
```

[2]

```text
% git clone https://gitlab.data.bas.ac.uk/MAGIC/assets-tracking-service.git
% cd assets-tracking-service/
% pre-commit install
% uv sync --all-groups
```

[3]

```text
% psql -d postgres -c "CREATE USER assets_tracking_owner WITH PASSWORD 'xxx';"
% psql -d postgres -c "CREATE USER assets_tracking_service_ro WITH PASSWORD 'xxx';"
```

Where `xxx` are placeholder values.

Then run the `reset-db` [Development Task](/docs/dev.md#development-tasks) to create databases and required extensions.

> [!TIP]
> You can also [Populate](#syncing-development-database) the development database from production.

## Running control CLI locally

```text
% uv run ats-ctl --help
```

Or if within the project virtual environment:

```text
% ats-ctl --help
```

See the [CLI Reference](/docs/cli-reference.md) documentation for available commands.

## Development tasks

[Taskipy](https://github.com/taskipy/taskipy?tab=readme-ov-file#general) is used to define development tasks, such as
running tests and resetting local databases. These tasks are akin to NPM scripts or similar concepts.

Run `task --list` (or `uv run task --list`) for available commands.

Run `task [task]` (`uv run task [task]`) to run a specific task.

See [Adding development tasks](#adding-development-tasks) for how to add new tasks.

> [!TIP]
> If offline, use `uv run --offline task ...` to avoid lookup errors trying to the unconstrained build system
> requirements in `pyproject.toml`, which is a [Known Issue](https://github.com/astral-sh/uv/issues/5190) within UV.

## Contributing

All changes except minor tweaks (typos, comments, etc.) MUST:

- be associated with an issue (either directly or by reference)
- be included in the [Change Log](/CHANGELOG.md)

### Conventions

- all deployable code should be contained in the `assets-tracking-service` package
- use `Path.resolve()` if displaying or logging file/directory paths
- use logging to record how actions progress, using the app logger (`logger = logging.getLogger('app')`)
- extensions to third party dependencies should be:
  - created in `assets_tracking_service.lib`
  - documented in [Libraries](/docs/libraries.md)
  - tested in `tests.lib_tests/`

### Adding configuration options

In the `assets_tracking_service.Config` class:

- define a new property
- add property to `ConfigDumpSafe` typed dict
- add property to `dumps_safe()` method
- if needed, add logic to `validate()` method

In the [Configuration](/docs/config.md) documentation:

- add to [Options Table](/docs/config.md#config-options) in alphabetical order
- if needed, add a subsection to explain the option in more detail

If configurable:

- update the `.env.tpl` template and any existing `.env` files
- update the `[tool.pytest_env]` section in `pyproject.toml`

In the `tests.assets_tracking_service_tests.config` module:

- update the expected response in the `test_dumps_safe` method
- if validated, update the `test_validate` (valid) method and add new `test_validate_` (invalid) tests
- update or create other tests as needed

### Adding database migrations

To create a migration run the `migration [slug]` [Development Task](#development-tasks) where `[slug]` is a short, `-`
separated, identifier (e.g. `foo-bar`).

This will create an *up* and *down* migration in the
[`db_migrations`](/src/assets_tracking_service/resources/db_migrations) resource directory. Migration are numbered
(ascending for up migrations, descending for down) to ensure they are applied in the correct order.

- include a related GitLab issue wherever applicable to these mirations
- views should be named with a `v_` prefix.
- if adding a new table with static data, add to the `exclusions` in `.pgsync.yml` & `tpl/.pgsync.yml.tpl`
- update the [Data Model](/docs/data-model.md) documentation as necessary
- migrations should be grouped into logical units:
  - e.g. for a new entity, define the table and it's indexes, triggers, etc. in a single migration
  - multiple entities (even if related and part of the same change/feature) SHOULD use separate migrations

<!-- pyml disable md028 -->
> [!CAUTION]
> Existing migrations MUST NOT be amended. Use an `ALTER` command in new migrations if a column type changes,

> [!NOTE]
> The application database role does not have privileges to create other roles.
<!-- pyml enable md028 -->

See the [Implementation](/docs/implementation.md#database-migrations) documentation for more information on migrations.

### Adding CLI command groups

If a new CLI command group is needed:

- create a new module within the `assets_tracking_service.cli` package
- create a corresponding test module in `tests.asset_tracking_service_tests.cli`
- import and add the new command CLI in the `assets_tracking_service.cli` module

In the relevant command group module, create a new method:

- make sure the command decorator *name* and *help* are set correctly
- follow the conventions established in other commands for error handling and presenting data to the user
- add corresponding tests

In the [CLI Reference](/docs/cli-reference.md) documentation:

- if needed, create a new command group section
- list and summarise the new command in the relevant group section

### Adding providers

1. add `ENABLE_PROVIDER_FOO` [Config Option](#adding-configuration-options) for enabling/disabling provider
1. update `ENABLED_PROVIDERS` computed config property to include new provider
1. add provider specific [Config Options](#adding-configuration-options) as needed
1. create a new module in the `assets_tracking_service.providers` package
1. create a new class inheriting from the [`assets_tracking_service.providers.base_provider.BaseProvider` class
1. implement methods required by the base class
1. include in the `assets_tracking_service.providers.providers_manager.ProvidersManager` class and update the
  `_make_providers()` method
1. add tests as needed

### Adding exporters

> [!CAUTION]
> This section is Work in Progress (WIP) and may be incomplete/inaccurate.

1. add a `ENABLE_EXPORTER_FOO` [Config Option](#adding-configuration-options) for enabling/disabling the exporter
1. update the `ENABLED_EXPORTERS` computed config option to include new exporter
1. add exporter specific [Config Options](#adding-configuration-options) as needed
1. if the exporter relies on another, update the `Config.validate()` method to ensure the dependent exporter is enabled
1. create a new module in the `assets_tracking_service.exporters` package
1. create a new class inheriting from the `assets_tracking_service.exporters.base_exporter.BaseExporter` class
1. implement methods required by the base class
1. integrate into the `assets_tracking_service.exporters.exporters_manager.ExportersManager` class and update the
  `_make_exporters()` method
1. add tests as needed, including:
   - creating a new module in the `tests.assets_tracking_service_tests.exporters` package
   - the `tests.assets_tracking_service_tests.exporters.test_exporters_manager.test_make_each_exporter` method
   - adding a mock in `/tests/assets_tracking_service_tests/exporters/test_exporters_manager.test_export`

### Adding layers

> [!CAUTION]
> This section is Work in Progress (WIP) and may be incomplete/inaccurate.

1. agree a slug to use to identify the new layer (e.g. `foo`)
1. create a new [Database Migration](#adding-database-migrations) that:
   - creates a source view, selecting data for the new layer (named `v_{slug}`)
   - creates a GeoJSON view, selecting from source view into a feature collection (named `v_{slug}_geojson`)
   - inserts rows into `layer` and `record` with relevant details
1. create resource files for the record associated with the new layer:
   - `resources/records/{slug}/abstract.md`
   - `resources/records/{slug}/lineage.md`
1. run the [`data export`](/docs/cli-reference.md#data-commands) command to provision and publish the new layer and
  it's record
1. configure symbology, fields and popups for the ArcGIS feature layer as needed
1. capture this portrayal information in `resources/arcgis_layers/{slug}/portrayal.json`:
    1. use https://ago-assistant.esri.com/ and view the relevant item
    2. copy the contents of the Data file into the relevant `portrayal.json` file
1. document new layer in the [Data Access](/README.md#data-access) documentation

### Adding development tasks

See the [Taskipy](https://github.com/taskipy/taskipy?tab=readme-ov-file#adding-tasks) documentation.

## Python version

The Python version is limited to 3.11 due to the `arcgis` dependency.

## Dependencies

### Vulnerability scanning

The [Safety](https://pypi.org/project/safety/) package checks dependencies for known vulnerabilities.

> [!WARNING]
> As with all security tools, Safety is an aid for spotting common mistakes, not a guarantee of secure code.
> In particular this is using the free vulnerability database, which is updated less frequently than paid options.

Checks are run automatically in [Continuous Integration](#continuous-integration).

> [!TIP]
> To check locally run the `safety` [Development Task](#development-tasks).

### Updating dependencies

- create an issue and switch to branch
- run `uv tree --outdated --depth=1` to list outdated packages
- follow https://docs.astral.sh/uv/concepts/projects/sync/#upgrading-locked-package-versions
- note upgrades in the issue
- review any major/breaking upgrades
- run [Tests](#testing) manually
- commit changes

## Linting

### Ruff

[Ruff](https://docs.astral.sh/ruff/) is used to lint and format Python files. Specific checks and config options are
set in [`pyproject.toml`](/pyproject.toml). Linting checks are run automatically in
[Continuous Integration](#continuous-integration) and the [Pre-Commit Hook](#pre-commit-hook).

> [!TIP]
> To check linting manually run the `lint` [Development Task](#development-tasks), for formatting run the `format` task.

### SQLFluff

[SQLFluff](https://www.sqlfluff.com) is used to lint and format SQL files. Specific checks and config options are set
in [`pyproject.toml`](/pyproject.toml). Linting checks are run automatically in
[Continuous Integration](#continuous-integration) and the [Pre-Commit Hook](#pre-commit-hook).

> [!TIP]
> To check SQL linting manually run the `sql` [Development Task](#development-tasks).

#### SQLFluff disabled rules

- [`ST06`](https://docs.sqlfluff.com/en/stable/reference/rules.html#rule-ST06)
  - where select elements should be ordered by complexity rather than preference/opinion
- [`ST10`](https://docs.sqlfluff.com/en/stable/reference/rules.html#rule-ST10)
  - where a condition such as `WHERE elem.label ->> 'scheme' = 'ats:last_fetched'` is incorrectly seen as a constant

### Static security analysis

[Ruff](#ruff) is configured to run [Bandit](https://github.com/PyCQA/bandit), a static analysis tool for Python.

> [!WARNING]
> As with all security tools, Bandit is an aid for spotting common mistakes, not a guarantee of secure code.
> In particular this tool can't check for issues that are only be detectable when running code.

### Markdown

[PyMarkdown](https://pymarkdown.readthedocs.io/en/latest/) is used to lint Markdown files. Specific checks and config
options are set in [`pyproject.toml`](/pyproject.toml). Linting checks are run automatically in
[Continuous Integration](#continuous-integration) and the [Pre-Commit Hook](#pre-commit-hook).

> [!TIP]
> To check linting manually run the `markdown` [Development Task](#development-tasks).

Wide tables will fail rule `MD013` (max line length). Wrap such tables with pragma disable/enable exceptions:

```markdown
<!-- pyml disable md013 -->
| Header | Header |
|--------|--------|
| Value  | Value  |
<!-- pyml enable md013 -->
```

Stacked admonitions will fail rule `MD028` (blank lines in blockquote) as it's ambiguous whether a new blockquote has
started where another element isn't inbetween. Wrap such instances with pragma disable/enable exceptions:

```markdown
<!-- pyml disable md028 -->
> [!NOTE]
> ...

> [!NOTE]
> ...
<!-- pyml enable md028 -->
```

### Editorconfig

For consistency, it's strongly recommended to configure your IDE or other editor to use the
[EditorConfig](https://editorconfig.org/) settings defined in [`.editorconfig`](/.editorconfig).

### Pre-commit hook

A [Pre-Commit](https://pre-commit.com) hook is configured in [`.pre-commit-config.yaml`](/.pre-commit-config.yaml).

To update Pre-Commit and configured hooks:

```shell
% pre-commit autoupdate
```

> [!TIP]
> To run pre-commit checks against all files manually run the `pre-commit` [Development Task](#development-tasks).

## Testing

### Pytest

[pytest](https://docs.pytest.org) with a number of plugins is used for testing the application. Config options are set
in `pyproject.toml`. Tests are defined in the `tests` package.

Tests are run automatically in [Continuous Integration](#continuous-integration).

<!-- pyml disable md028 -->
> [!TIP]
> To run tests manually run the `test` [Development Task](#development-tasks).

> [!TIP]
> To run a specific test:
>
> ```shell
> % uv run pytest tests/path/to/test_module.py::<class>.<method>
> ```
<!-- pyml enable md028 -->

### Pytest fast fail

If a test run fails with a `NotImplementedError` exception run the `test-reset` [Development Task](#development-tasks).

This occurs where:

- a test fails and the failed test is then renamed or parameterised options changed
- the reference to the previously failed test has been cached to enable the `--failed-first` runtime option
- the cached reference no longer exists triggering an error which isn't handled by the `pytest-random-order` plugin

Running this task clears Pytest's cache and re-runs all tests, skipping the `--failed-first` option.

### Pytest fixtures

Fixtures SHOULD be defined in `tests.conftest` prefixed with `fx_` to indicate they are a fixture when used in tests.
E.g.:

```python
import pytest

@pytest.fixture()
def fx_foo() -> str:
    """Example test fixture."""
    return 'foo'
```

### Pytest-cov test coverage

[`pytest-cov`](https://pypi.org/project/pytest-cov/) checks test coverage. We aim for 100% coverage but exemptions are
fine with good justification:

- `# pragma: no cover` - for general exemptions
- `# pragma: no branch` - where a conditional branch can never be called

[Continuous Integration](#continuous-integration) will check coverage automatically.

<!-- pyml disable md028 -->
> [!TIP]
> To check coverage manually run the `test-cov` [Development Task](#development-tasks).

> [!TIP]
> To run tests for a specific module locally:
>
> ```shell
> % uv run pytest --cov=asets_tracking_service.some.module --cov-report=html tests/asets_tracking_service_tests/some/module
> ```
<!-- pyml enable md028 -->

Where tests are added to ensure coverage, use the `cov` [mark](https://docs.pytest.org/en/7.1.x/how-to/mark.html), e.g:

```python
import pytest

@pytest.mark.cov()
def test_foo():
    assert 'foo' == 'foo'
```

### Pytest-env

[pytest-env](https://pypi.org/project/pytest-env/) sets environment variables used by the [Config](/docs/config.md)
class to fake values when testing. Values are configured in the `[tool.pytest_env]` section of `pyproject.toml`.

### Pytest-recording

[pytest-recording](https://github.com/kiwicom/pytest-recording) is used to mock HTTP calls to provider APIs (ensuring
known values are used in tests).

> [!CAUTION]
> Review recorded responses to check for any sensitive information.

To update a specific test:

```text
% uv run pytest --record-mode=once tests/path/to/test_module.py::<class>::<method>
```

To incrementally build up a set of related tests (including parameterised tests) use the `new_episodes` recording mode:

```text
% uv run pytest --record-mode=new_episodes tests/path/to/test_module.py::<class>::<method>
```

### Continuous Integration

All commits will trigger Continuous Integration using GitLab's CI/CD platform, configured in `.gitlab-ci.yml`.

## Development database

If using a local Postgres database installed through homebrew (assuming `@17` is the version installed):

- manage service: `brew services [command] postgresql@14`
- view logs: `/usr/local/var/log/postgresql@17.log`

To check current DB sessions with `psql -d postgres`:

```sql
select *
from pg_catalog.pg_stat_activity
where datname = 'assets_tracking_dev';
\q
```

> [!TIP]
> To drop and recreate local databases run the `reset-db` [Development Task](#development-tasks).
> Then recreate as per [Local Development Environment](#local-development-environment) steps.

### Syncing development database

To sync production data to the Development database:

- run the `pgsync-init` [Development Task](#development-tasks) if needed to create a `.pgsync.yml` config
- run the `pgsync` [Development Task](#development-tasks)
