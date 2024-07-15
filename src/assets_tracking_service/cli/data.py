import logging

import typer
from rich import print

from assets_tracking_service.config import Config
from assets_tracking_service.db import DatabaseClient, make_conn
from assets_tracking_service.providers.providers_manager import ProvidersManager

_ok = "[green]Ok.[/green]"
_no = "[red]No.[/red]"

logger = logging.getLogger("app")
data_cli = typer.Typer()


@data_cli.command(name="fetch", help="Fetch active assets and their last known positions.")
def fetch() -> None:
    """
    Fetch active assets and last known positions.

    The providers manager is designed to try and handle problems/exceptions raised by providers gracefully (by logging
    them and moving on), such that one problematic resource or provider doesn't block everything else.

    As such there are no expected exceptions we can handle here.
    """
    config = Config()
    db = DatabaseClient(conn=make_conn(config.DB_DSN))
    providers = ProvidersManager(config=config, db=db, logger=logger)

    providers.fetch_active_assets()
    providers.fetch_latest_positions()
    print(f"{_ok} Command exited normally. Check log for any errors.")
