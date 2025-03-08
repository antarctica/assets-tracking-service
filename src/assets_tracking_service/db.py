from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Literal, Self

from importlib_resources import as_file as resources_as_file
from importlib_resources import files as resources_files
from psycopg import Connection, connect
from psycopg.sql import SQL, Composed, Identifier


class DatabaseError(Exception):
    """Raised for database errors unless a more specific subclass applies."""

    pass


class DatabaseMigrationError(DatabaseError):
    """Raised when database can't be migrated up or down."""

    pass


class DatabaseClient:
    """Basic database client."""

    def __init__(self: Self, conn: Connection) -> None:
        """
        Create client using injected database connection.

        All date times are fetched as UTC.
        """
        self._logger = logging.getLogger("app")
        self._conn = conn

        self._conn.execute("SET timezone TO 'UTC';")

    @property
    def conn(self: Self) -> Connection:
        """
        Psycopg database connection.

        If needed for use-cases not covered by this class.
        """
        return self._conn

    def close(self) -> None:
        """Close the database connection."""
        self._logger.info("Closing DB connection.")
        self._conn.close()

    def execute(self: Self, query: SQL | Composed, params: Sequence | Mapping[str, Any] | None = None) -> None:
        """Execute a given SQL statement."""
        try:
            with self._conn.cursor() as cur:
                cur.execute(query=query, params=params)
        except Exception as e:
            self._logger.exception("Error executing statement")
            self._conn.rollback()
            self.close()
            msg = "Error executing statement"
            raise DatabaseError(msg) from e

    def execute_file(self: Self, path: Path) -> None:
        """Execute SQL statements in a given file."""
        with path.open() as file:
            self._logger.info("Executing SQL from: %s", path.resolve())

            # noinspection PyTypeChecker
            self.execute(SQL(file.read()))

    def execute_files_in_path(self: Self, path: Path) -> None:
        """Execute statements in all SQL files in a given directory."""
        for file_path in sorted(path.glob("*.sql")):
            self.execute_file(file_path)

    def get_query_result(
        self: Self, query: SQL | Composed, params: Sequence | Mapping[str, Any] | None = None, as_dict: bool = False
    ) -> list[tuple | dict]:
        """Execute a query and return the result as a list of tuples or dicts."""
        with self._conn.cursor() as cur:
            try:
                cur.execute(query=query, params=params)
            except Exception as e:
                msg = "Error executing query"
                raise DatabaseError(msg) from e
            if as_dict:
                columns = [desc[0] for desc in cur.description]
                return [dict(zip(columns, row)) for row in cur.fetchall()]  # noqa: B905
            return cur.fetchall()

    def insert_dict(self: Self, schema: str, table_view: str, data: dict) -> None:
        """
        Insert data into table or view from a dict.

        This method is mainly to avoid PyCharm's incorrect error highlighting when using SQL composition.
        """
        # PyCharm does not understand SQL placeholders and incorrectly marks this as an error.
        # noinspection PyTypeChecker
        query = SQL("INSERT INTO {schema}.{table_view} ({fields}) VALUES ({values});").format(
            schema=Identifier(schema),
            table_view=Identifier(table_view),
            fields=SQL(",").join(Identifier(key) for key in data),
            values=SQL(",").join(SQL("%s") for _ in data),
        )

        self.execute(query, list(data.values()))

    def update_dict(self: Self, schema: str, table_view: str, data: dict, where: Composed) -> None:
        """
        Update data in a table or view from a dict.

        This method is mainly to avoid PyCharm's incorrect error highlighting when using SQL composition.
        """
        # PyCharm does not understand SQL placeholders and incorrectly marks this as an error.
        # noinspection PyTypeChecker
        query = SQL("UPDATE {schema}.{table_view} SET {data} WHERE {where};").format(
            schema=Identifier(schema),
            table_view=Identifier(table_view),
            data=SQL(",").join(SQL("{} = %s").format(Identifier(key)) for key in data),
            where=where,
        )

        self.execute(query, list(data.values()))

    def _migrate(self: Self, direction: Literal["up", "down"]) -> None:
        """
        Migrate DB.

        Migrations are stored as SQL files included within the package.
        """
        try:
            with resources_as_file(
                resources_files("assets_tracking_service.resources.db_migrations")
            ) as migrations_path:
                self.execute_files_in_path(migrations_path / direction)
        except DatabaseError as e:
            msg = f"Error migrating DB {direction}"
            raise DatabaseMigrationError(msg) from e

    def migrate_upgrade(self: Self) -> None:
        """Upgrade database to head migration."""
        self._logger.info("Upgrading database to head revision...")
        self._migrate("up")

    def migrate_downgrade(self: Self) -> None:
        """Downgrade database to base migration."""
        self._logger.info("Downgrading database to base revision...")
        self._migrate("down")

    @property
    def _head_available_migration(self: Self) -> int:
        """
        Index of the latest migration that could have been applied.

        Returned as an integer to allow for comparison. E.g. If the latest migration is `012-foo.sql`, 12.
        """
        with resources_as_file(resources_files("assets_tracking_service.resources.db_migrations")) as migrations_path:
            head_file = sorted(migrations_path.glob("up/*.sql"))[-1]
            return int(head_file.stem.split("-")[0])

    @property
    def _head_applied_migration(self: Self) -> int | None:
        """
        Index of the latest migration that has been applied to the database.

        As reported by the migrations table. Returned as an integer to allow for comparison.

        Returns `None` if any error occurs getting the current migration (because the migrations table is not present
        for example, or the database was migrated before migration tracking was introduced in migration 14).
        """
        try:
            result = self.get_query_result(
                query=SQL("""SELECT migration_id FROM public.meta_migration WHERE pk = 1;""")
            )
            return result[0][0]
        except DatabaseError:
            self._logger.warning("Error getting current migration")
            return None

    def get_migrate_status(self: Self) -> bool | None:
        """
        Check if the database is at the head migration.

        Returns `True` if the database is at the head migration.
        Returns `False` if the database is not at the head migration.
        Returns `None` if the migration last applied to the database can't be determined.
        """
        applied_migration = self._head_applied_migration
        if applied_migration is None:
            return None

        return applied_migration == self._head_available_migration


def make_conn(dsn: str) -> Connection:
    """
    Create a psycopg connection from a connection string.

    This method is isolated to allow for easy mocking of the `DatabaseClient` class.
    """
    return connect(dsn, autocommit=True)
