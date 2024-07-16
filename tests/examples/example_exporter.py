import logging

from assets_tracking_service.config import Config
from assets_tracking_service.db import DatabaseClient
from assets_tracking_service.exporters.base_exporter import Exporter


class ExampleExporter(Exporter):
    # noinspection PyUnusedLocal
    def __init__(self, config: Config, db: DatabaseClient, logger: logging.Logger):
        pass

    def export(self):
        pass
