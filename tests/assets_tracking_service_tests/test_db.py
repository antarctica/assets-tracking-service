from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from psycopg.sql import SQL, Identifier
from psycopg.types.json import Jsonb
from pytest_mock import MockerFixture

from assets_tracking_service.config import Config
from assets_tracking_service.db import DatabaseClient, DatabaseError, DatabaseMigrationError, make_conn


class TestDBClient:
    """Test database client."""

    def test_get_conn_info(self, fx_db_client_tmp: DatabaseClient):
        """Gets connection info."""
        result = fx_db_client_tmp.conn.info.user
        assert result == "postgres"

    @pytest.mark.cov
    def test_commit(self, fx_db_client_tmp: DatabaseClient):
        """
        Commits transaction.
        TODO: Expand beyond stub.
        """
        fx_db_client_tmp.commit()

    @pytest.mark.cov
    def test_rollback(self, fx_db_client_tmp: DatabaseClient):
        """
        Rolls back transaction.
        TODO: Expand beyond stub.
        """
        fx_db_client_tmp.rollback()

    def test_execute_statement(self, fx_db_client_tmp: DatabaseClient):
        """Statement can be executed."""
        fx_db_client_tmp.execute(SQL("SELECT 1;"))

    def test_execute_statement_error(self, fx_db_client_tmp: DatabaseClient):
        """Invalid statement triggers error."""
        with pytest.raises(DatabaseError):
            fx_db_client_tmp.execute(SQL("SELECT * FROM {};").format(Identifier("unknown")))

    def test_execute_file(self, caplog: pytest.LogCaptureFixture, fx_db_client_tmp: DatabaseClient):
        """Statements loaded from a file can be executed."""
        with TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.sql"
            file_path.write_text("SELECT 1;")

            fx_db_client_tmp.execute_file(file_path)

            assert f"Executing SQL from: {file_path.resolve()}" in caplog.text

    def test_execute_files_in_path(self, fx_db_client_tmp: DatabaseClient):
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

            fx_db_client_tmp.execute_files_in_path(Path(temp_dir))

    def test_get_query_result_tuple(self, fx_db_client_tmp: DatabaseClient):
        """Gets query results as tuple."""
        result = fx_db_client_tmp.get_query_result(SQL("SELECT 1;"))
        assert result == [(1,)]

    def test_get_query_result_dict(self, fx_db_client_tmp: DatabaseClient):
        """Gets query results as dict using placeholders."""
        answer = 1
        result = fx_db_client_tmp.get_query_result(query=SQL("SELECT %s as result;"), params=(answer,), as_dict=True)
        assert result == [{"result": answer}]

    def test_get_query_result_json(self, fx_db_client_tmp: DatabaseClient):
        """Gets query results with JSON based where clause."""
        expected_label = {"name": "test"}

        fx_db_client_tmp.execute(
            SQL("""
                CREATE TABLE IF NOT EXISTS public.test
                (
                    id      INTEGER  GENERATED ALWAYS AS IDENTITY CONSTRAINT test_pk PRIMARY KEY,
                    labels  JSONB
                );
                """)
        )
        fx_db_client_tmp.insert_dict("public", "test", {"labels": Jsonb([expected_label])})

        results = fx_db_client_tmp.get_query_result(
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

        fx_db_client_tmp.execute(SQL("DROP TABLE {}.{};").format(Identifier("public"), Identifier("test")))

    def test_get_query_result_error(self, fx_db_client_tmp: DatabaseClient):
        """Getting invalid query triggers error."""
        with pytest.raises(DatabaseError):
            fx_db_client_tmp.get_query_result(SQL("SELECT * FROM {};").format(Identifier("unknown")))

    # noinspection SqlResolve
    def test_insert_dict(self, fx_db_client_tmp: DatabaseClient):
        """Inserts a dictionary."""
        fx_db_client_tmp.execute(
            SQL("""
        CREATE TABLE IF NOT EXISTS public.test
        (
            id    INTEGER  GENERATED ALWAYS AS IDENTITY CONSTRAINT test_pk PRIMARY KEY,
            name  TEXT
        );
        """)
        )

        fx_db_client_tmp.insert_dict("public", "test", {"name": "test"})

        result = fx_db_client_tmp.get_query_result(
            SQL("SELECT * FROM {}.{};").format(Identifier("public"), Identifier("test"))
        )
        assert result == [(1, "test")]

        fx_db_client_tmp.execute(SQL("DROP TABLE {}.{};").format(Identifier("public"), Identifier("test")))

    def test_insert_dict_jsonb(self, fx_db_client_tmp: DatabaseClient):
        fx_db_client_tmp.execute(
            SQL("""
        CREATE TABLE IF NOT EXISTS public.test
        (
            id    INTEGER  GENERATED ALWAYS AS IDENTITY CONSTRAINT test_pk PRIMARY KEY,
            data  JSONB
        );
        """)
        )

        data = {"foo": "bar"}

        fx_db_client_tmp.insert_dict("public", "test", {"data": Jsonb(data)})

        result = fx_db_client_tmp.get_query_result(
            SQL("SELECT * FROM {}.{};").format(Identifier("public"), Identifier("test"))
        )
        assert result == [(1, data)]

    def test_insert_dict_error(self, fx_db_client_tmp: DatabaseClient):
        """Invalid insert triggers error."""
        with pytest.raises(DatabaseError):
            fx_db_client_tmp.insert_dict("public", "unknown", {"name": "test"})

    def test_update_dict(self, fx_db_client_tmp: DatabaseClient):
        """Updates data from a dictionary."""
        fx_db_client_tmp.execute(
            SQL("""
                CREATE TABLE IF NOT EXISTS public.test
                (
                    id    INTEGER  GENERATED ALWAYS AS IDENTITY CONSTRAINT test_pk PRIMARY KEY,
                    name  TEXT
                );

                INSERT INTO public.test (name) VALUES ('initial');
                INSERT INTO public.test (name) VALUES ('no-change');
                """)
        )

        fx_db_client_tmp.update_dict(
            schema="public", table_view="test", data={"name": "updated"}, where=SQL("id = {}").format(1)
        )

        result = fx_db_client_tmp.get_query_result(
            SQL("SELECT * FROM {}.{};").format(Identifier("public"), Identifier("test"))
        )
        assert (1, "updated") in result
        assert (2, "no-change") in result

        fx_db_client_tmp.execute(SQL("DROP TABLE {}.{};").format(Identifier("public"), Identifier("test")))

    def test_migrate_upgrade(self, caplog: pytest.LogCaptureFixture, fx_db_client_tmp: DatabaseClient):
        """Database can be migrated up."""
        fx_db_client_tmp.migrate_upgrade()

        assert "Upgrading database to head revision..." in caplog.text

        # verify an expected object exists
        result = fx_db_client_tmp.get_query_result(SQL("SELECT PostGIS_Version();"))
        assert "USE_GEOS" in result[0][0]

    @pytest.mark.cov
    def test_migrate_upgrade_error(self, mocker: MockerFixture, fx_db_client_tmp: DatabaseClient):
        """Problem when migrating database up triggers error."""
        mocker.patch.object(fx_db_client_tmp, "execute_files_in_path", side_effect=DatabaseError)

        with pytest.raises(DatabaseMigrationError):
            fx_db_client_tmp.migrate_upgrade()

    def test_migrate_downgrade(self, caplog: pytest.LogCaptureFixture, fx_db_client_tmp_migrated: DatabaseClient):
        """Database can be migrated down."""
        fx_db_client_tmp_migrated.migrate_downgrade()

        assert "Downgrading database to base revision..." in caplog.text

        # verify an expected object does not exist
        with pytest.raises(DatabaseError):
            fx_db_client_tmp_migrated.get_query_result(SQL("SELECT PostGIS_Version();"))


class TestMakeConn:
    """Test method to make a database connection."""

    def test_make_conn(self, fx_config: Config):
        """Connection can be made."""
        conn = make_conn(fx_config.DB_DSN)
        with conn.cursor() as cur:
            cur.execute("SELECT 1;")
            assert cur.fetchone() == (1,)
        conn.close()
