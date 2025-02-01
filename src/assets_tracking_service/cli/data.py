import logging

import typer
from rich import print as rprint
from sentry_sdk import monitor

from assets_tracking_service.config import Config
from assets_tracking_service.db import DatabaseClient, make_conn
from assets_tracking_service.exporters.exporters_manager import ExportersManager
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
    rprint(f"{_ok} Command exited normally. Check log for any errors.")


@data_cli.command(name="export", help="Export summary data for assets and their last known positions.")
def export() -> None:
    """Dump assets with latest positions through each exporter."""
    config = Config()
    db = DatabaseClient(conn=make_conn(config.DB_DSN))
    exporters = ExportersManager(config=config, db=db, logger=logger)

    exporters.export()
    rprint(f"{_ok} Command exited normally. Check log for any errors.")


@data_cli.command(name="run", help="Fetch and export summary data for assets and their last known positions.")
def run() -> None:
    """
    Fetch and export assets with latest positions.

    As per the `fetch()` and `export()` methods. Triggers Sentry monitoring to ensure data is refreshed regularly.
    See docs/implementation.md#monitoring for details.
    """
    config = Config()
    db = DatabaseClient(conn=make_conn(config.DB_DSN))
    providers = ProvidersManager(config=config, db=db, logger=logger)
    exporters = ExportersManager(config=config, db=db, logger=logger)

    monitor_slug = "ats-run"
    with monitor(monitor_slug=monitor_slug, monitor_config=config.SENTRY_MONITOR_CONFIG[monitor_slug]):
        providers.fetch_active_assets()
        providers.fetch_latest_positions()
        exporters.export()

    rprint(f"{_ok} Command exited normally. Check log for any errors.")
