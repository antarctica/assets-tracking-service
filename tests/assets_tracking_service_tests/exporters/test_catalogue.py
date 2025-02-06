import logging
from json import load as json_load
from typing import Self

from assets_tracking_service.config import Config
from assets_tracking_service.db import DatabaseClient
from assets_tracking_service.exporters.catalogue import DataCatalogueExporter


class TestExporterDataCatalogue:
    """Data Catalogue exporter tests."""

    def test_init(self: Self, fx_config: Config, fx_db_client_tmp_db_mig: DatabaseClient, fx_logger: logging.Logger):
        """Initialises."""
        DataCatalogueExporter(config=fx_config, db=fx_db_client_tmp_db_mig, logger=fx_logger)

    def test_metadata(self: Self, fx_exporter_catalogue: DataCatalogueExporter):
        """Generates metadata."""
        result = fx_exporter_catalogue.metadata

        assert isinstance(result, dict)
        assert "id" in result  # temp content

    def test_export(self: Self, fx_exporter_catalogue: DataCatalogueExporter):
        """Exports metadata record."""
        expected_path = fx_exporter_catalogue._config.EXPORTER_DATA_CATALOGUE_OUTPUT_PATH

        fx_exporter_catalogue.export()

        assert expected_path.exists()

        # verify file is valid JSON
        with expected_path.open("r") as f:
            json_load(f)
