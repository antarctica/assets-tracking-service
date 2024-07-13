import pytest
from psycopg import Connection
from pytest_mock import MockerFixture
from pytest_postgresql import factories
from typer.testing import CliRunner

from assets_tracking_service.cli import app_cli
from assets_tracking_service.config import Config
from assets_tracking_service.db import DatabaseClient

# unused-imports are needed for the `factory_name` import to work
from tests.pytest_postgresql import (  # noqa: F401
    postgresql_proc_factory,
    postgresql_noproc_factory,
    factory_name as postgresql_factory_name,
)

# override `postgresql` fixture with either a local (proc) or remote (noproc) fixture depending on if in CI.
postgresql = factories.postgresql(postgresql_factory_name)


@pytest.fixture
def fx_config() -> Config:
    return Config()


# noinspection PyShadowingNames
@pytest.fixture()
def fx_db_client_tmp_db(postgresql: Connection) -> DatabaseClient:
    """Database client with an empty, disposable, database."""
    return DatabaseClient(conn=postgresql)


@pytest.fixture()
def fx_db_client_tmp_db_mig(fx_db_client_tmp_db: DatabaseClient) -> DatabaseClient:
    """Database client with a migrated, disposable, database."""
    fx_db_client_tmp_db.migrate_upgrade()
    fx_db_client_tmp_db.commit()
    return fx_db_client_tmp_db


@pytest.fixture()
def fx_cli() -> CliRunner:
    """CLI testing fixture."""
    return CliRunner()


# noinspection PyShadowingNames
@pytest.fixture()
def fx_cli_tmp_db(mocker: MockerFixture, postgresql: Connection) -> CliRunner:
    """CLI testing fixture using a disposable database."""
    mocker.patch("assets_tracking_service.cli.db.make_conn", return_value=postgresql)
    return CliRunner()


@pytest.fixture()
def fx_cli_tmp_db_mig(fx_cli_tmp_db: CliRunner) -> CliRunner:
    """CLI using a disposable database after running app `db migrate` command."""
    fx_cli_tmp_db.invoke(app=app_cli, args=["db", "migrate"])
    return fx_cli_tmp_db
