import logging
from json import load as json_load
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import PropertyMock

import pytest
from pytest_mock import MockerFixture

from assets_tracking_service.config import Config
from assets_tracking_service.db import DatabaseClient
from assets_tracking_service.exporters.catalogue import CollectionRecord, DataCatalogueExporter, LayerRecord


class TestCollectionRecord:
    """Test CollectionRecord class."""

    def test_init(
        self,
        fx_config: Config,
        fx_db_client_tmp_db_pop_exported: DatabaseClient,
        fx_logger: logging.Logger,
        fx_record_layer_slug: str,
    ):
        """Can initialise."""
        result = CollectionRecord(config=fx_config, db=fx_db_client_tmp_db_pop_exported, logger=fx_logger)
        assert isinstance(result, CollectionRecord)

    def test_valid(self, fx_exporter_collection_record: CollectionRecord):
        """Generates valid metadata record."""
        fx_exporter_collection_record.validate()

    @pytest.mark.cov()
    def test_output_path(self, fx_exporter_collection_record: CollectionRecord):
        """Can get output path."""
        result = fx_exporter_collection_record.output_path
        assert result.name == "collection.json"


class TestLayerRecord:
    """Test LayerRecord class."""

    def test_init(
        self,
        fx_config: Config,
        fx_db_client_tmp_db_pop_exported: DatabaseClient,
        fx_logger: logging.Logger,
        fx_record_layer_slug: str,
    ):
        """Can initialise."""
        result = LayerRecord(
            config=fx_config, db=fx_db_client_tmp_db_pop_exported, logger=fx_logger, layer_slug=fx_record_layer_slug
        )

        assert isinstance(result, LayerRecord)

    def test_valid(self, fx_exporter_layer_record: LayerRecord):
        """Generates valid metadata record."""
        fx_exporter_layer_record.validate()

    @pytest.mark.cov()
    def test_output_path(self, fx_exporter_layer_record: LayerRecord, fx_record_layer_slug: str):
        """Can get output path."""
        result = fx_exporter_layer_record.output_path
        assert result.name == f"{fx_record_layer_slug}.json"


class TestExporterDataCatalogue:
    """Data Catalogue exporter tests."""

    def test_init(self, fx_config: Config, fx_db_client_tmp_db_mig: DatabaseClient, fx_logger: logging.Logger):
        """Initialises."""
        DataCatalogueExporter(config=fx_config, db=fx_db_client_tmp_db_mig, logger=fx_logger)

    def test_get_records(self, fx_exporter_catalogue: DataCatalogueExporter):
        """Generates records."""
        result = fx_exporter_catalogue._get_records()

        assert isinstance(result, list)
        assert len(result) > 1
        assert all(isinstance(record, LayerRecord | CollectionRecord) for record in result)

    def test_export(
        self,
        mocker: MockerFixture,
        fx_db_client_tmp_db_pop: DatabaseClient,
        fx_logger: logging.Logger,
        fx_exporter_collection_record: CollectionRecord,
        fx_exporter_layer_record: LayerRecord,
    ):
        """Exports parsable metadata records."""
        with TemporaryDirectory() as tmp_path:
            output_path = Path(tmp_path)
            mock_config = mocker.Mock()
            type(mock_config).EXPORTER_DATA_CATALOGUE_OUTPUT_PATH = PropertyMock(return_value=output_path)
        mocker.patch.object(type(fx_exporter_collection_record), "output_path", PropertyMock(return_value=output_path))
        mocker.patch.object(type(fx_exporter_layer_record), "output_path", PropertyMock(return_value=output_path))

        exporter = DataCatalogueExporter(config=mock_config, db=fx_db_client_tmp_db_pop, logger=fx_logger)
        mocker.patch.object(
            type(exporter), "_get_records", return_value=[fx_exporter_collection_record, fx_exporter_layer_record]
        )
        expected_path = exporter._config.EXPORTER_DATA_CATALOGUE_OUTPUT_PATH

        exporter.export()

        assert expected_path.exists()

        # verify file is valid JSON
        with expected_path.open("r") as f:
            json_load(f)
