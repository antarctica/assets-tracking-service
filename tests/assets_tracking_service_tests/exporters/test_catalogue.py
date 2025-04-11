import logging
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import PropertyMock

from mypy_boto3_s3 import S3Client
from pytest_mock import MockerFixture

from assets_tracking_service.config import Config
from assets_tracking_service.db import DatabaseClient
from assets_tracking_service.exporters.catalogue import CollectionRecord, DataCatalogueExporter, LayerRecord
from assets_tracking_service.lib.bas_data_catalogue.models.record import RecordSummary


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


class TestExporterDataCatalogue:
    """Data Catalogue exporter tests."""

    def test_init(
        self,
        fx_config: Config,
        fx_db_client_tmp_db_mig: DatabaseClient,
        fx_s3_client: S3Client,
        fx_logger: logging.Logger,
    ):
        """Initialises."""
        DataCatalogueExporter(config=fx_config, db=fx_db_client_tmp_db_mig, s3=fx_s3_client, logger=fx_logger)

    def test_get_records(self, fx_exporter_catalogue: DataCatalogueExporter):
        """Generates records."""
        result = fx_exporter_catalogue._get_records()

        assert isinstance(result, list)
        assert len(result) > 1
        assert all(isinstance(record, LayerRecord | CollectionRecord) for record in result)

    def test_get_summaries(self, fx_exporter_catalogue: DataCatalogueExporter):
        """Generates record summaries."""
        result = fx_exporter_catalogue._get_summarises()

        assert isinstance(result, dict)
        assert len(result) > 1
        assert all(isinstance(summary, RecordSummary) for summary in result.values())

    def test_export(
        self,
        mocker: MockerFixture,
        fx_s3_bucket_name: str,
        fx_exporter_catalogue: DataCatalogueExporter,
        fx_exporter_collection_record: CollectionRecord,
        fx_exporter_layer_record: LayerRecord,
    ):
        """Exports valid metadata records in a range of formats."""
        with TemporaryDirectory() as tmp_path:
            output_path = Path(tmp_path)
        mock_config = mocker.Mock()
        type(mock_config).EXPORTER_DATA_CATALOGUE_OUTPUT_PATH = PropertyMock(return_value=output_path)
        type(mock_config).EXPORTER_DATA_CATALOGUE_AWS_ACCESS_ID = PropertyMock(return_value="x")
        type(mock_config).EXPORTER_DATA_CATALOGUE_AWS_ACCESS_SECRET = PropertyMock(return_value="x")
        type(mock_config).EXPORTER_DATA_CATALOGUE_AWS_S3_BUCKET = PropertyMock(return_value=fx_s3_bucket_name)
        type(mock_config).EXPORTER_DATA_CATALOGUE_EMBEDDED_MAPS_ENDPOINT = PropertyMock(return_value="x")
        type(mock_config).EXPORTER_DATA_CATALOGUE_ITEM_CONTACT_ENDPOINT = PropertyMock(return_value="x")

        mocker.patch.object(fx_exporter_catalogue, "_config", new=mock_config)
        mocker.patch.object(
            type(fx_exporter_catalogue),
            "_get_records",
            return_value=[fx_exporter_collection_record, fx_exporter_layer_record],
        )

        fx_exporter_catalogue.export()

        expected = [
            f"records/{fx_exporter_collection_record.file_identifier}.html",
            f"records/{fx_exporter_layer_record.file_identifier}.xml",
            f"records/{fx_exporter_collection_record.file_identifier}.xml",
            f"records/{fx_exporter_layer_record.file_identifier}.json",
            f"records/{fx_exporter_layer_record.file_identifier}.html",
            f"records/{fx_exporter_collection_record.file_identifier}.json",
            f"items/{fx_exporter_layer_record.file_identifier}/index.html",
            f"items/{fx_exporter_collection_record.file_identifier}/index.html",
            "collections/assets-tracking-service/index.html",
            "static/xsl/iso-html/printFormatted.xsl",
            "static/xsl/iso-html/elements-ISO.xml",
            "static/xsl/iso-html/xml-to-html-ISO.xsl",
            "static/xsl/iso-html/xml-to-text-ISO.xsl",
            "static/xsl/iso-html/headers-ISO.xml",
            "static/xsl/iso-html/printTextLines.xsl",
            "static/xsl/iso-html/displayElement.xsl",
        ]
        assert output_path.exists()
        _debug = [path.relative_to(output_path) for path in output_path.glob("**/*.*")]
        for path in expected:
            assert output_path.joinpath(path).exists()
