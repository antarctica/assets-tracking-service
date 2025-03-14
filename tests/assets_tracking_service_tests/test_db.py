from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import PropertyMock

import pytest
from psycopg import Connection
from psycopg.sql import SQL, Identifier
from psycopg.types.json import Jsonb
from pytest_mock import MockerFixture

from assets_tracking_service.config import Config
from assets_tracking_service.db import DatabaseClient, DatabaseError, DatabaseMigrationError, make_conn


class TestDBClient:
    """Test database client."""

    def test_get_conn_info(self, fx_db_client_tmp_db: DatabaseClient):
        """Gets connection info."""
        result = fx_db_client_tmp_db.conn.info.user
        assert result == "postgres"

    @pytest.mark.cov()
    def test_close(self, postgresql: Connection):
        """Closes connection."""
        client = DatabaseClient(conn=postgresql)
        client.close()

    def test_execute_statement(self, fx_db_client_tmp_db: DatabaseClient):
        """Statement can be executed."""
        fx_db_client_tmp_db.execute(SQL("SELECT 1;"))

    def test_execute_statement_error(self, fx_db_client_tmp_db: DatabaseClient):
        """Invalid statement triggers error."""
        with pytest.raises(DatabaseError):
            fx_db_client_tmp_db.execute(SQL("SELECT * FROM {};").format(Identifier("unknown")))

    def test_execute_file(self, caplog: pytest.LogCaptureFixture, fx_db_client_tmp_db: DatabaseClient):
        """Statements loaded from a file can be executed."""
        with TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.sql"
            file_path.write_text("SELECT 1;")

            fx_db_client_tmp_db.execute_file(file_path)

            assert f"Executing SQL from: {file_path.resolve()}" in caplog.text

    def test_execute_files_in_path(self, fx_db_client_tmp_db: DatabaseClient):
        """
        Statements loaded from files in a directory can be executed.

        These file names are chosen intentionally to check they are sorted correctly.
        """
        with TemporaryDirectory() as temp_dir:
            file_1_path = Path(temp_dir) / "0 run first.sql"
            file_1_path.write_text(
                """CREATE TABLE public.test (
                id INTEGER  GENERATED ALWAYS AS IDENTITY CONSTRAINT test_pk PRIMARY KEY
                );"""
            )
            file_2_path = Path(temp_dir) / "1 go second.sql"
            file_2_path.write_text("""DROP TABLE public.test;""")

            fx_db_client_tmp_db.execute_files_in_path(Path(temp_dir))

    def test_get_query_result_tuple(self, fx_db_client_tmp_db: DatabaseClient):
        """Gets query results as tuple."""
        result = fx_db_client_tmp_db.get_query_result(SQL("SELECT 1;"))
        assert result == [(1,)]

    def test_get_query_result_dict(self, fx_db_client_tmp_db: DatabaseClient):
        """Gets query results as dict using placeholders."""
        answer = 1
        result = fx_db_client_tmp_db.get_query_result(query=SQL("SELECT %s as result;"), params=(answer,), as_dict=True)
        assert result == [{"result": answer}]

    def test_get_query_result_json(self, fx_db_client_tmp_db: DatabaseClient):
        """Gets query results with JSON based where clause."""
        expected_label = {"name": "test"}

        fx_db_client_tmp_db.execute(
            SQL("""
                CREATE TABLE IF NOT EXISTS public.test
                (
                    id      INTEGER  GENERATED ALWAYS AS IDENTITY CONSTRAINT test_pk PRIMARY KEY,
                    labels  JSONB
                );
                """)
        )
        fx_db_client_tmp_db.insert_dict("public", "test", {"labels": Jsonb([expected_label])})

        results = fx_db_client_tmp_db.get_query_result(
            query=SQL("""
                WITH labels AS (
                    SELECT jsonb_array_elements(labels) AS label
                    FROM {}.{}
                )
                SELECT label->>'name' AS name
                FROM labels
                WHERE label @> %s;
            """).format(Identifier("public"), Identifier("test")),
            params=(Jsonb(expected_label),),
            as_dict=True,
        )
        assert results == [expected_label]

        fx_db_client_tmp_db.execute(SQL("DROP TABLE {}.{};").format(Identifier("public"), Identifier("test")))

    def test_get_query_result_error(self, fx_db_client_tmp_db: DatabaseClient):
        """Getting invalid query triggers error."""
        with pytest.raises(DatabaseError):
            fx_db_client_tmp_db.get_query_result(SQL("SELECT * FROM {};").format(Identifier("unknown")))

    def test_select_timezone_utc(self, fx_db_client_tmp_db: DatabaseClient):
        """Date times are returned in UTC."""
        fx_db_client_tmp_db.execute(
            SQL("""
                CREATE TABLE IF NOT EXISTS public.test
                (
                    id      INTEGER  GENERATED ALWAYS AS IDENTITY CONSTRAINT test_pk PRIMARY KEY,
                    time    TIMESTAMPTZ
                );
                INSERT INTO public.test (time) VALUES ('2021-01-01 14:30:00+00:00');
                """)
        )

        result = fx_db_client_tmp_db.get_query_result(SQL("SELECT time FROM public.test;"))

        assert isinstance(result[0][0], datetime)
        assert result[0][0].tzinfo == UTC

    # noinspection SqlResolve
    def test_insert_dict(self, fx_db_client_tmp_db: DatabaseClient):
        """Inserts a dictionary."""
        fx_db_client_tmp_db.execute(
            SQL("""
        CREATE TABLE IF NOT EXISTS public.test
        (
            id    INTEGER  GENERATED ALWAYS AS IDENTITY CONSTRAINT test_pk PRIMARY KEY,
            name  TEXT
        );
        """)
        )

        fx_db_client_tmp_db.insert_dict("public", "test", {"name": "test"})

        result = fx_db_client_tmp_db.get_query_result(
            SQL("SELECT * FROM {}.{};").format(Identifier("public"), Identifier("test"))
        )
        assert result == [(1, "test")]

        fx_db_client_tmp_db.execute(SQL("DROP TABLE {}.{};").format(Identifier("public"), Identifier("test")))

    def test_insert_dict_jsonb(self, fx_db_client_tmp_db: DatabaseClient):
        """Inserts a dictionary with JSONB data."""
        fx_db_client_tmp_db.execute(
            SQL("""
        CREATE TABLE IF NOT EXISTS public.test
        (
            id    INTEGER  GENERATED ALWAYS AS IDENTITY CONSTRAINT test_pk PRIMARY KEY,
            data  JSONB
        );
        """)
        )

        data = {"foo": "bar"}

        fx_db_client_tmp_db.insert_dict("public", "test", {"data": Jsonb(data)})

        result = fx_db_client_tmp_db.get_query_result(
            SQL("SELECT * FROM {}.{};").format(Identifier("public"), Identifier("test"))
        )
        assert result == [(1, data)]

    def test_insert_dict_error(self, fx_db_client_tmp_db: DatabaseClient):
        """Invalid insert triggers error."""
        with pytest.raises(DatabaseError):
            fx_db_client_tmp_db.insert_dict("public", "unknown", {"name": "test"})

    def test_upgrade_dict(self, fx_db_client_tmp_db: DatabaseClient):
        """Updates existing data from a dictionary."""
        fx_db_client_tmp_db.execute(
            SQL("""
        CREATE TABLE IF NOT EXISTS public.test
        (
            id    INTEGER  GENERATED ALWAYS AS IDENTITY CONSTRAINT test_pk PRIMARY KEY,
            name  TEXT
        );
        """)
        )
        fx_db_client_tmp_db.insert_dict("public", "test", {"name": "test"})

        # noinspection PyTypeChecker
        fx_db_client_tmp_db.update_dict("public", "test", {"name": "updated"}, SQL("id = 1"))

        result = fx_db_client_tmp_db.get_query_result(
            SQL("SELECT * FROM {}.{};").format(Identifier("public"), Identifier("test"))
        )
        assert result == [(1, "updated")]

    def test_migrate_upgrade(self, caplog: pytest.LogCaptureFixture, fx_db_client_tmp_db: DatabaseClient):
        """Database can be migrated up."""
        fx_db_client_tmp_db.migrate_upgrade()

        assert "Upgrading database to head revision..." in caplog.text

        # verify an expected object exists
        result = fx_db_client_tmp_db.get_query_result(SQL("SELECT PostGIS_Version();"))
        assert "USE_GEOS" in result[0][0]

    @pytest.mark.cov()
    def test_migrate_upgrade_error(self, mocker: MockerFixture, fx_db_client_tmp_db: DatabaseClient):
        """Problem when migrating database up triggers error."""
        mocker.patch.object(fx_db_client_tmp_db, "execute_files_in_path", side_effect=DatabaseError)

        with pytest.raises(DatabaseMigrationError):
            fx_db_client_tmp_db.migrate_upgrade()

    def test_migrate_downgrade(self, caplog: pytest.LogCaptureFixture, fx_db_client_tmp_db_mig: DatabaseClient):
        """Database can be migrated down."""
        fx_db_client_tmp_db_mig.migrate_downgrade()

        assert "Downgrading database to base revision..." in caplog.text

        # verify an expected object does not exist
        with pytest.raises(DatabaseError):
            fx_db_client_tmp_db_mig.get_query_result(SQL("SELECT generate_ulid();"))

    def test_migrate_migrate(self, caplog: pytest.LogCaptureFixture, fx_db_client_tmp_db_mig: DatabaseClient):
        """Database can be migrated up if already at head migration."""
        fx_db_client_tmp_db_mig.migrate_upgrade()

        assert "Upgrading database to head revision..." in caplog.text

    def test_head_available_migration(self, fx_db_client_tmp_db: DatabaseClient):
        """Latest available migrations in the app package can be reported."""
        result = fx_db_client_tmp_db._head_available_migration

        assert isinstance(result, int)
        assert result > 1

    def test_head_applied_migration(self, fx_db_client_tmp_db_mig: DatabaseClient):
        """Migrated database returns migration last applied."""
        result = fx_db_client_tmp_db_mig._head_applied_migration

        assert isinstance(result, int)
        assert result > 1

    def test_head_applied_migration_error(self, fx_db_client_tmp_db: DatabaseClient):
        """Problem determining database migration returns None."""
        result = fx_db_client_tmp_db._head_applied_migration

        assert result is None

    def test_migrate_status(self, fx_db_client_tmp_db_mig: DatabaseClient):
        """Fully migrated database returns True."""
        result = fx_db_client_tmp_db_mig.get_migrate_status()
        assert result is True

    def test_migrate_status_behind(self, mocker: MockerFixture, fx_db_client_tmp_db_mig: DatabaseClient):
        """Database with outstanding migrations returns False."""
        mocker.patch.object(
            type(fx_db_client_tmp_db_mig), "_head_available_migration", new_callable=PropertyMock, return_value=999
        )

        result = fx_db_client_tmp_db_mig.get_migrate_status()

        assert result is False

    def test_migrate_status_unknown(self, fx_db_client_tmp_db: DatabaseClient):
        """Problem determining if all migrations are applied returns None."""
        result = fx_db_client_tmp_db.get_migrate_status()
        assert result is None


class TestMakeConn:
    """Test method to make a database connection."""

    def test_make_conn(self, fx_config: Config):
        """Connection can be made."""
        conn = make_conn(fx_config.DB_DSN)
        with conn.cursor() as cur:
            cur.execute("SELECT 1;")
            assert cur.fetchone() == (1,)
        conn.close()
