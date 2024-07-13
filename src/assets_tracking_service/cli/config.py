import logging

import typer
from rich import print

from assets_tracking_service.config import Config, ConfigurationError

_ok = "[green]Ok.[/green]"
_no = "[red]No.[/red]"

logger = logging.getLogger("app")
config_cli = typer.Typer()


@config_cli.command(help="Check current app configuration is valid.")
def check() -> None:
    """Validate current app configuration."""
    config = Config()

    try:
        logger.info("Checking app config.")
        config.validate()
    except ConfigurationError as e:
        logger.error(e, exc_info=True)
        print(f"{_no} Configuration invalid.")
        typer.echo(e)
        raise typer.Abort() from e

    logger.info("App config ok.")
    print(f"{_ok} Configuration ok.")


@config_cli.command(help="Display current app configuration.")
def show() -> None:
    """Display current app configuration."""
    config = Config()

    logger.info("Dumping app config with sensitive values redacted.")
    print(config.dumps_safe())
