import logging
from json import loads as json_loads
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import PropertyMock

from boto3 import client as S3Client  # noqa: N812
from pytest_mock import MockerFixture

from assets_tracking_service.lib.bas_data_catalogue.exporters.json_exporter import JsonExporter
from assets_tracking_service.lib.bas_data_catalogue.models.record import Record


class TestIsoXmlExporter:
    """Test Metadata Library JSON config exporter."""

    def test_init(
        self,
        mocker: MockerFixture,
        fx_logger: logging.Logger,
        fx_s3_bucket_name: str,
        fx_s3_client: S3Client,
        fx_lib_record_minimal_item: Record,
    ):
        """Can create an ISO XML Exporter."""
        with TemporaryDirectory() as tmp_path:
            output_path = Path(tmp_path)
        mock_config = mocker.Mock()
        type(mock_config).EXPORTER_DATA_CATALOGUE_OUTPUT_PATH = PropertyMock(return_value=output_path)
        type(mock_config).EXPORTER_DATA_CATALOGUE_AWS_S3_BUCKET = PropertyMock(return_value=fx_s3_bucket_name)

        exporter = JsonExporter(
            config=mock_config,
            logger=fx_logger,
            s3=fx_s3_client,
            record=fx_lib_record_minimal_item,
            export_base=output_path,
        )

        assert isinstance(exporter, JsonExporter)
        assert exporter.name == "BAS JSON"

    def test_dumps(
        self,
        mocker: MockerFixture,
        fx_logger: logging.Logger,
        fx_s3_bucket_name: str,
        fx_s3_client: S3Client,
        fx_lib_record_minimal_item: Record,
    ):
        """Can encode record as Metadata Library JSON config dict."""
        with TemporaryDirectory() as tmp_path:
            output_path = Path(tmp_path)
        mock_config = mocker.Mock()
        type(mock_config).EXPORTER_DATA_CATALOGUE_OUTPUT_PATH = PropertyMock(return_value=output_path)
        type(mock_config).EXPORTER_DATA_CATALOGUE_AWS_S3_BUCKET = PropertyMock(return_value=fx_s3_bucket_name)
        expected = fx_lib_record_minimal_item.dumps()

        exporter = JsonExporter(
            config=mock_config,
            logger=fx_logger,
            s3=fx_s3_client,
            record=fx_lib_record_minimal_item,
            export_base=output_path,
        )

        result = exporter.dumps()
        assert json_loads(result) == expected
