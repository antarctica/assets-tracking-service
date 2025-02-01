from typing import Union

import typer

from assets_tracking_service.cli.config import config_cli
from assets_tracking_service.cli.data import data_cli
from assets_tracking_service.cli.db import db_cli
from assets_tracking_service.config import Config

config = Config()

app_cli = typer.Typer(name="ats-ctl", help="Assets Tracking Service control CLI.")

app_cli.add_typer(config_cli, name="config", help="Manage application configuration.")
app_cli.add_typer(data_cli, name="data", help="Manage application data.")
app_cli.add_typer(db_cli, name="db", help="Manage application database.")

_version_option = typer.Option(None, "-v", "--version", is_eager=True, help="Show application version and exit.")


@app_cli.callback(invoke_without_command=True)
def cli(version: Union[bool | None] = _version_option) -> None:  # noqa: UP007
    """CLI entry point."""
    if version:
        print(config.VERSION)
        raise typer.Exit()
