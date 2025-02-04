import logging

import typer
from psycopg.sql import SQL
from rich import print as rprint

from assets_tracking_service.config import Config
from assets_tracking_service.db import DatabaseClient, DatabaseError, DatabaseMigrationError, make_conn

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
        rprint(f"{_ok} Database ok.")
    except DatabaseError as e:
        logger.error(e, exc_info=True)
        rprint(f"{_no} Error accessing database.")
        typer.echo(e)
        raise typer.Exit(code=1) from e
    finally:
        db_client.close()


@db_cli.command(name="migrate", help="Setup application database.")
def migrate_db_up() -> None:
    """Run DB migrations."""
    config = Config()
    db_client = DatabaseClient(conn=make_conn(config.DB_DSN))

    try:
        db_client.migrate_upgrade()
        rprint(f"{_ok} Database migrated.")
    except DatabaseMigrationError as e:
        logger.error(e, exc_info=True)
        rprint(f"{_no} Error migrating database.")
        typer.echo(e)
        raise typer.Exit(code=1) from e
    finally:
        pass
        db_client.close()


@db_cli.command(name="rollback", help="Reset application database.")
def rollback_db_down() -> None:
    """Rollback DB migrations."""
    # prompt user to continue
    rprint("[yellow]WARNING![/yellow] This will remove all data from database!")
    if not typer.confirm("Continue?"):
        rprint(f"{_no} Aborted.")
        raise typer.Exit(code=0)

    config = Config()
    db_client = DatabaseClient(conn=make_conn(config.DB_DSN))

    try:
        db_client.migrate_downgrade()
        rprint(f"{_ok} DB rolled back.")
    except DatabaseMigrationError as e:
        logger.error(e, exc_info=True)
        rprint(f"{_no} Error rolling back database.")
        typer.echo(e)
        raise typer.Exit(code=1) from e
    finally:
        db_client.close()
