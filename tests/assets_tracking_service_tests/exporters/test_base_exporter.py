import logging

from assets_tracking_service.config import Config
from assets_tracking_service.db import DatabaseClient
from tests.examples.example_exporter import ExampleExporter


class TestBaseExporter:
    """
    Test abstract Exporter class.

    Because BaseExporter is an abstract class, we use a local concrete subclass (ExampleExporter) to test it.
    """

    def test_init(self, fx_config: Config, fx_db_client_tmp_db_pop: DatabaseClient, fx_logger: logging.Logger):
        """Initialises."""
        exporter = ExampleExporter(config=fx_config, db=fx_db_client_tmp_db_pop, logger=fx_logger)
        assert exporter is not None

    def test_export(self, fx_exporter_example: ExampleExporter):
        """Exports."""
        fx_exporter_example.export()
