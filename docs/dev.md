# BAS Assets Tracking Service - Deployment

## Local development environment

Requirements:

* Python 3.12 ([pyenv](https://github.com/pyenv/pyenv) recommended)
* [Poetry](https://python-poetry.org/docs/#installation)
* Git (`brew install git`)
* Postgres with PostGIS extension (`brew install postgis`)

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

## Running control CLI locally

```
$ poetry run python ats-ctl ...
```

See the [CLI Usage](#command-line-interface) section for available commands.

## Contributing

All changes must:

- be associated with an issue (either directly or by reference)
- be included in the [Change Log](./CHANGELOG.md)

Conventions:

- all deployable code should be contained in the `assets-tracking-service` package
- use `Path.resolve()` if displaying or logging file/directory paths
- use logging to record how actions progress, using the app [`logger`](../src/assets_tracking_service/loging.py)
  - (e.g. `logger = logging.getLogger('app')`)

## Dependencies

### Vulnerability scanning

The [Safety](https://pypi.org/project/safety/) package is used to check dependencies against known vulnerabilities.

**WARNING!** As with all security tools, Safety is an aid for spotting common mistakes, not a guarantee of secure code.
In particular this is using the free vulnerability database, which is updated less frequently than paid options.

Checks are run automatically in [Continuous Integration](#continuous-integration). To check locally:

```
$ poetry run safety scan
```

## Linting

[Ruff](https://docs.astral.sh/ruff/) is used to lint and format Python files. Specific checks and config options are
set in `pyproject.toml`. Linting checks are run automatically in [Continuous Integration](#continuous-integration).

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

## Testing

### Pytest

[pytest](https://docs.pytest.org) with a number of plugins is used to test the application. Config options are set in
[`pyproject.toml`](../pyproject.toml). Tests checks are run automatically in
[Continuous Integration](#continuous-integration).

To run tests locally:

```
$ poetry run pytest
```

Tests for the application are defined in the
[`tests/assets_tracking_service_tests`](../tests/assets_tracking_service_tests) module.

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

Test coverage is checked with [`pytest-cov`](https://pypi.org/project/pytest-cov/). We aim for 100% coverage.
Exemptions for coverage should be used sparingly and with good justification. Where tests are added to ensure coverage,
use the `cov` [mark](https://docs.pytest.org/en/7.1.x/how-to/mark.html), e.g:

```python
import pytest

@pytest.mark.cov
def test_foo():
    assert 'foo' == 'foo'
```

### Pytest-recording

[pytest-recording](https://github.com/kiwicom/pytest-recording) is used to mock HTTP calls to provider APIs (ensuring
known values are used in tests).

To (re-)record responses:

- if re-recording, remove some or all existing 'cassette' YAML files
- update test fixtures to use real credentials
- run tests in record mode: `poetry run pytest --record-mode=once`
- update test fixtures to use fake/safe credentials
- redact credentials captured in captured cassettes

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

Update config [tests](../tests/assets_tracking_service_tests/test_config.py) as needed.
