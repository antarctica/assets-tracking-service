import pytest
from psycopg import Connection
from pytest_postgresql import factories

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
def fx_db_client_tmp(postgresql: Connection) -> DatabaseClient:
    """Database client with an empty, disposable, database."""
    return DatabaseClient(conn=postgresql)


@pytest.fixture()
def fx_db_client_tmp_migrated(fx_db_client_tmp: DatabaseClient) -> DatabaseClient:
    """Database client with a migrated, disposable, database."""
    fx_db_client_tmp.migrate_upgrade()
    fx_db_client_tmp.commit()
    return fx_db_client_tmp
