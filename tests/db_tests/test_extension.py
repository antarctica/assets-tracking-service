import pytest
from psycopg.sql import SQL

from assets_tracking_service.db import DatabaseClient


class TestDbExtensions:
    """Test database extensions."""

    # noinspection SqlResolve
    @pytest.mark.parametrize("extension", ["postgis"])
    def test_extensions(self, fx_db_client_tmp_db_mig: DatabaseClient, extension: str):
        """Test required database extension are available."""
        result = fx_db_client_tmp_db_mig.get_query_result(
            SQL("""SELECT extname FROM pg_extension WHERE extname = %s;"""), (extension,)
        )
        assert len(result) == 1
