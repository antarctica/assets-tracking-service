import logging
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import PropertyMock

from mypy_boto3_s3 import S3Client
from pytest_mock import MockerFixture

from assets_tracking_service.lib.bas_data_catalogue.exporters.base_exporter import S3Utils
from assets_tracking_service.lib.bas_data_catalogue.exporters.records_exporter import RecordsExporter
from assets_tracking_service.lib.bas_data_catalogue.models.record import Record, RecordSummary
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.common import Identifier


class TestRecordsExporter:
    """Test meta records exporter."""

    def test_init(
        self,
        mocker: MockerFixture,
        fx_logger: logging.Logger,
        fx_s3_bucket_name: str,
        fx_s3_client: S3Client,
        fx_lib_record_minimal_item_catalogue: Record,
    ):
        """Can create a Records meta Exporter."""
        with TemporaryDirectory() as tmp_path:
            output_path = Path(tmp_path)
        mock_config = mocker.Mock()
        type(mock_config).EXPORTER_DATA_CATALOGUE_OUTPUT_PATH = PropertyMock(return_value=output_path)
        type(mock_config).EXPORTER_DATA_CATALOGUE_AWS_S3_BUCKET = PropertyMock(return_value=fx_s3_bucket_name)

        exporter = RecordsExporter(
            config=mock_config, s3=fx_s3_client, logger=fx_logger, records=[fx_lib_record_minimal_item_catalogue]
        )

        assert isinstance(exporter, RecordsExporter)
        assert exporter.name == "Records"

    def test_load_records(self, fx_lib_exporter_records: RecordsExporter, fx_lib_record_minimal_item_catalogue: Record):
        """Can load records."""
        assert fx_lib_exporter_records._records == {
            fx_lib_record_minimal_item_catalogue.file_identifier: fx_lib_record_minimal_item_catalogue
        }

    def test_load_summaries(
        self, fx_lib_exporter_records: RecordsExporter, fx_lib_record_minimal_item_catalogue: Record
    ):
        """Can load records."""
        summary = RecordSummary.loads(fx_lib_record_minimal_item_catalogue)
        assert fx_lib_exporter_records._summaries == {fx_lib_record_minimal_item_catalogue.file_identifier: summary}

    def test_get_item_summary(
        self, fx_lib_exporter_records: RecordsExporter, fx_lib_record_minimal_item_catalogue: Record
    ):
        """Can get item summary."""
        summary = RecordSummary.loads(fx_lib_record_minimal_item_catalogue)
        assert (
            fx_lib_exporter_records._get_item_summary(fx_lib_record_minimal_item_catalogue.file_identifier) == summary
        )

    def test_get_exporters(
        self, fx_lib_exporter_records: RecordsExporter, fx_lib_record_minimal_item_catalogue: Record
    ):
        """Can get exporter instances."""
        result = fx_lib_exporter_records._get_exporters(fx_lib_record_minimal_item_catalogue)
        names = sorted([exporter.name for exporter in result])
        assert names == sorted(["Item HTML", "Item Aliases", "BAS JSON", "ISO XML", "ISO XML HTML"])

    def test_export_record(
        self, fx_lib_exporter_records: RecordsExporter, fx_lib_record_minimal_item_catalogue: Record
    ):
        """Can export a record."""
        site_path = fx_lib_exporter_records._config.EXPORTER_DATA_CATALOGUE_OUTPUT_PATH
        record_id = fx_lib_record_minimal_item_catalogue.file_identifier
        expected = [
            site_path.joinpath("records", f"{record_id}.json"),
            site_path.joinpath("records", f"{record_id}.xml"),
            site_path.joinpath("records", f"{record_id}.html"),
            site_path.joinpath("datasets", "y", "index.html"),
            site_path.joinpath("items", record_id, "index.html"),
        ]
        fx_lib_exporter_records._records[record_id].identification.identifiers.append(
            Identifier(
                identifier="datasets/y", href="https://data.bas.ac.uk/datasets/y", namespace="alias.data.bas.ac.uk"
            )
        )

        fx_lib_exporter_records.export_record(fx_lib_record_minimal_item_catalogue.file_identifier)

        result = list(fx_lib_exporter_records._config.EXPORTER_DATA_CATALOGUE_OUTPUT_PATH.glob("**/*.*"))
        for path in expected:
            assert path in result

    def test_publish_record(
        self, fx_lib_exporter_records: RecordsExporter, fx_lib_record_minimal_item_catalogue: Record
    ):
        """Can export a record."""
        record_id = fx_lib_record_minimal_item_catalogue.file_identifier
        bucket = fx_lib_exporter_records._config.EXPORTER_DATA_CATALOGUE_AWS_S3_BUCKET
        s3_utils = S3Utils(
            s3=fx_lib_exporter_records._s3,
            s3_bucket=bucket,
            relative_base=fx_lib_exporter_records._config.EXPORTER_DATA_CATALOGUE_OUTPUT_PATH,
        )
        expected = [
            "items/x/index.html",
            "datasets/y/index.html",
            "records/x.html",
            "records/x.json",
            "records/x.xml",
        ]
        fx_lib_exporter_records._records[record_id].identification.identifiers.append(
            Identifier(
                identifier="datasets/y", href="https://data.bas.ac.uk/datasets/y", namespace="alias.data.bas.ac.uk"
            )
        )

        fx_lib_exporter_records.publish_record(fx_lib_record_minimal_item_catalogue.file_identifier)

        result = s3_utils._s3.list_objects(Bucket=bucket)
        keys = [o["Key"] for o in result["Contents"]]
        for key in expected:
            assert key in keys

    def test_export_all(self, fx_lib_exporter_records: RecordsExporter):
        """Can export all records."""
        fx_lib_exporter_records.export_all()

        result = list(fx_lib_exporter_records._config.EXPORTER_DATA_CATALOGUE_OUTPUT_PATH.glob("**/*.*"))
        assert len(result) > 0

    def test_publish_all(self, fx_lib_exporter_records: RecordsExporter):
        """Can export all records."""
        bucket = fx_lib_exporter_records._config.EXPORTER_DATA_CATALOGUE_AWS_S3_BUCKET
        s3_utils = S3Utils(
            s3=fx_lib_exporter_records._s3,
            s3_bucket=bucket,
            relative_base=fx_lib_exporter_records._config.EXPORTER_DATA_CATALOGUE_OUTPUT_PATH,
        )

        fx_lib_exporter_records.publish_all()

        result = s3_utils._s3.list_objects(Bucket=bucket)
        keys = [o["Key"] for o in result["Contents"]]
        assert len(keys) > 0
