import logging

import typer
from psycopg.sql import SQL
from rich import print

from assets_tracking_service.config import Config
from assets_tracking_service.db import DatabaseClient, make_conn, DatabaseMigrationError, DatabaseError

_ok = "[green]Ok.[/green]"
_no = "[red]No.[/red]"

logger = logging.getLogger("app")
db_cli = typer.Typer()


@db_cli.command(name="check", help="Check application database can be accessed.")
def check_db() -> None:
    """Check DB connection."""
    config = Config()
    db_client = DatabaseClient(conn=make_conn(config.DB_DSN))

    try:
        db_client.execute(SQL("SELECT 1;"))
        print(f"{_ok} Database ok.")
    except DatabaseError as e:
        logger.error(e, exc_info=True)
        print(f"{_no} Error accessing database.")
        typer.echo(e)
        raise typer.Abort() from e


@db_cli.command(name="migrate", help="Setup application database.")
def migrate_db_up() -> None:
    """Run DB migrations."""
    config = Config()
    db_client = DatabaseClient(conn=make_conn(config.DB_DSN))

    try:
        db_client.migrate_upgrade()
        print(f"{_ok} Database migrated.")
    except DatabaseMigrationError as e:
        logger.error(e, exc_info=True)
        print(f"{_no} Error migrating database.")
        typer.echo(e)
        raise typer.Abort() from e


@db_cli.command(name="rollback", help="Reset application database.")
def rollback_db_down() -> None:
    """Rollback DB migrations."""

    # prompt user to continue
    print("[yellow]WARNING![/yellow] This will remove all data from database!")
    if not typer.confirm("Continue?"):
        print(f"{_no} Aborted.")
        raise typer.Exit(code=0)

    config = Config()
    db_client = DatabaseClient(conn=make_conn(config.DB_DSN))

    try:
        db_client.migrate_downgrade()
        print(f"{_ok} DB rolled back.")
    except DatabaseMigrationError as e:
        logger.error(e, exc_info=True)
        print(f"{_no} Error rolling back database.")
        typer.echo(e)
        raise typer.Abort() from e
