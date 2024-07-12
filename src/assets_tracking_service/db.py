from __future__ import annotations

import logging
from importlib.resources import files as resources_files, as_file as resources_as_file
from pathlib import Path
from typing import Any, Mapping, Sequence, Literal

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

    def __init__(self, conn: Connection) -> None:
        """Create client using injected database connection."""
        self._logger = logging.getLogger("app")

        self._conn = conn

    @property
    def conn(self) -> Connection:
        """
        Psycopg database connection.

        If needed for use-cases not covered by this class.
        """
        return self._conn

    def commit(self) -> None:
        """Commit any pending transactions."""
        self._conn.commit()

    def rollback(self) -> None:
        """Rollback any pending transactions."""
        self._conn.rollback()

    def execute(self, query: SQL | Composed, params: Sequence | Mapping[str, Any] | None = None) -> None:
        """Execute a given SQL statement."""
        try:
            with self._conn.cursor() as cur:
                cur.execute(query=query, params=params)
        except Exception as e:
            self.rollback()
            raise DatabaseError("Error executing statement") from e

    def execute_file(self, path: Path) -> None:
        """Execute SQL statements in a given file."""
        with path.open() as file:
            self._logger.info("Executing SQL from: %s", path.resolve())

            # noinspection PyTypeChecker
            self.execute(SQL(file.read()))

    def execute_files_in_path(self, path: Path) -> None:
        """Execute statements in all SQL files in a given directory."""
        for file_path in sorted(path.glob("*.sql")):
            self.execute_file(file_path)

    def get_query_result(
        self, query: SQL | Composed, params: Sequence | Mapping[str, Any] = None, as_dict: bool = False
    ) -> list[tuple | dict]:
        """Execute a query and return the result as a list of tuples or dicts."""
        with self._conn.cursor() as cur:
            try:
                cur.execute(query=query, params=params)
            except Exception as e:
                raise DatabaseError("Error executing query") from e

            if as_dict:
                columns = [desc[0] for desc in cur.description]
                return [dict(zip(columns, row)) for row in cur.fetchall()]

            return cur.fetchall()

    def insert_dict(self, schema: str, table_view: str, data: dict) -> None:
        """Insert data into table or view from a dict."""
        # PyCharm does not understand SQL placeholders and incorrectly marks this as an error.
        # noinspection PyTypeChecker
        query = SQL("INSERT INTO {}.{} ({}) VALUES ({});").format(
            Identifier(schema),
            Identifier(table_view),
            SQL(",").join(Identifier(key) for key in data.keys()),
            SQL(",").join(SQL("%s") for _ in data.keys()),
        )

        self.execute(query, list(data.values()))

    def update_dict(self, schema: str, table_view: str, data: dict, where: Composed) -> None:
        """Update data in a table or view from a dict."""
        # PyCharm does not understand SQL placeholders and incorrectly marks this as an error.
        # noinspection PyTypeChecker
        query = SQL("UPDATE {}.{} SET {} WHERE {};").format(
            Identifier(schema),
            Identifier(table_view),
            SQL(",").join(SQL("{} = %s").format(Identifier(key)) for key in data.keys()),
            where,
        )

        self.execute(query, list(data.values()))

    def _migrate(self, direction: Literal["up", "down"]) -> None:
        """Placeholder for DB migrations."""
        try:
            with resources_as_file(
                resources_files("assets_tracking_service.resources.db_migrations")
            ) as migrations_path:
                self.execute_files_in_path(migrations_path / direction)
                self.commit()
        except DatabaseError as e:
            self.rollback()
            raise DatabaseMigrationError(f"Error migrating DB {direction}") from e

    def migrate_upgrade(self) -> None:
        """Placeholder for DB upgrade migrations."""
        self._logger.info("Upgrading database to head revision...")
        self._migrate("up")

    def migrate_downgrade(self) -> None:
        """Placeholder for DB downgrade migrations."""
        self._logger.info("Downgrading database to base revision...")
        self._migrate("down")


def make_conn(dsn: str) -> Connection:
    """
    Create a psycopg connection from a connection string.

    This method is isolated to allow for easy mocking of the `DatabaseClient` class.
    """
    return connect(dsn)
