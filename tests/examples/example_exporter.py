import logging
from typing import Self

from assets_tracking_service.config import Config
from assets_tracking_service.db import DatabaseClient
from assets_tracking_service.exporters.base_exporter import Exporter


class ExampleExporter(Exporter):
    """Minimal Exporter for testing."""

    # noinspection PyUnusedLocal
    def __init__(self: Self, config: Config, db: DatabaseClient, logger: logging.Logger) -> None:
        pass

    def export(self: Self):
        """Export data."""
        pass
