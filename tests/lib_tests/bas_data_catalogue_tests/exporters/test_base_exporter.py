import logging
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import PropertyMock

import pytest
from boto3 import client as S3Client  # noqa: N812
from pytest_mock import MockerFixture

from assets_tracking_service.config import Config
from assets_tracking_service.lib.bas_data_catalogue.exporters.base_exporter import Exporter, ResourceExporter, S3Utils
from assets_tracking_service.lib.bas_data_catalogue.models.record import Record


class FakeResourceExporter(ResourceExporter):
    """For testing base resource exporter."""

    def __init__(self, config: Config, logger: logging.Logger, s3: S3Client, record: Record, export_base: Path) -> None:
        super().__init__(
            config=config, logger=logger, s3=s3, record=record, export_base=export_base, export_name="x.txt"
        )

    @property
    def name(self) -> str:
        """..."""
        return "FakeResourceExporter"

    def dumps(self) -> str:
        """..."""
        return "x"


class TestS3Utils:
    """Test S3 utility methods."""

    def test_init(self, fx_logger: logging.Logger, fx_s3_client: S3Client, fx_s3_bucket_name: str):
        """Can create instance."""
        with TemporaryDirectory() as tmp_path:
            path = Path(tmp_path)

        s3_utils = S3Utils(s3=fx_s3_client, logger=fx_logger, s3_bucket=fx_s3_bucket_name, relative_base=path)
        assert isinstance(s3_utils, S3Utils)

    def test_calc_s3_key(self, fx_lib_s3_utils: S3Utils):
        """Can get S3 key from path relative to site base."""
        expected = "x/y/z.txt"
        path = fx_lib_s3_utils._relative_base.joinpath(expected)

        actual = fx_lib_s3_utils.calc_key(path=path)
        assert actual == expected

    def test_upload_content(self, caplog: pytest.LogCaptureFixture, fx_s3_bucket_name: str, fx_lib_s3_utils: S3Utils):
        """Can write output to an object at a low level."""
        expected = "x"

        fx_lib_s3_utils.upload_content(key=expected, content_type="text/plain", body="x")

        result = fx_lib_s3_utils._s3.list_objects_v2(Bucket=fx_s3_bucket_name)
        assert len(result["Contents"]) == 1
        result = result["Contents"][0]
        assert result["Key"] == expected
        assert f"s3://{fx_s3_bucket_name}/{expected}" in caplog.text

    def test_upload_content_redirect(self, fx_s3_bucket_name: str, fx_lib_s3_utils: S3Utils):
        """Can write output to an object with a object redirect."""
        key = "x"
        expected = "y"

        fx_lib_s3_utils.upload_content(key=key, content_type="text/plain", body="x", redirect="y")

        result = fx_lib_s3_utils._s3.get_object(Bucket=fx_s3_bucket_name, Key=key)
        assert result["WebsiteRedirectLocation"] == expected

    def test_upload_package_resources(self, fx_s3_bucket_name: str, fx_lib_s3_utils: S3Utils):
        """Can upload package resources to S3 bucket."""
        expected = "static/xsl/iso-html/xml-to-html-ISO.xsl"
        fx_lib_s3_utils.upload_package_resources(
            src_ref="assets_tracking_service.lib.bas_data_catalogue.resources.xsl.iso-html",
            base_key="static/xsl/iso-html",
        )

        result = fx_lib_s3_utils._s3.get_object(Bucket=fx_s3_bucket_name, Key=expected)
        assert result["ResponseMetadata"]["HTTPStatusCode"] == 200

    def test_upload_package_resources_exists(self, fx_s3_bucket_name: str, fx_lib_s3_utils: S3Utils):
        """Can keep existing objects if already copied to S3 bucket from package resources."""
        src_ref = "assets_tracking_service.lib.bas_data_catalogue.resources.xsl.iso-html"
        base_key = "static/xsl/iso-html"
        key = "static/xsl/iso-html/xml-to-html-ISO.xsl"

        fx_lib_s3_utils.upload_package_resources(src_ref=src_ref, base_key=base_key)
        initial = fx_lib_s3_utils._s3.get_object(Bucket=fx_s3_bucket_name, Key=key)

        fx_lib_s3_utils.upload_package_resources(src_ref=src_ref, base_key=base_key)
        repeat = fx_lib_s3_utils._s3.get_object(Bucket=fx_s3_bucket_name, Key=key)
        assert initial["LastModified"] == repeat["LastModified"]

    def test_empty_bucket(self, caplog: pytest.LogCaptureFixture, fx_s3_bucket_name: str, fx_lib_s3_utils: S3Utils):
        """Can empty all objects in bucket."""
        fx_lib_s3_utils.upload_content(key="x", content_type="text/plain", body="x")
        result = fx_lib_s3_utils._s3.list_objects_v2(Bucket=fx_s3_bucket_name)
        assert len(result["Contents"]) == 1

        fx_lib_s3_utils.empty_bucket()
        result = fx_lib_s3_utils._s3.list_objects_v2(Bucket=fx_s3_bucket_name)
        assert "contents" not in result


class TestBaseExporter:
    """Test base exporter."""

    def test_init(self, mocker: MockerFixture, fx_logger: logging.Logger):
        """Can create an Exporter."""
        s3_client = mocker.MagicMock()
        mock_config = mocker.Mock()

        base = Exporter(config=mock_config, logger=fx_logger, s3=s3_client)

        assert isinstance(base, Exporter)

    def test_dump_package_resources(self, fx_lib_exporter_base: Exporter):
        """Can copy package resources to directory if not already present."""
        with TemporaryDirectory() as tmp_path:
            output_path = Path(tmp_path)
        src_ref = "assets_tracking_service.lib.bas_data_catalogue.resources.xsl.iso-html"
        dest_path = output_path / "xsl" / "iso-html"

        fx_lib_exporter_base._dump_package_resources(src_ref=src_ref, dest_path=dest_path)

        assert dest_path.exists()

    @pytest.mark.cov()
    def test_dump_package_resources_repeat(self, fx_lib_exporter_base: Exporter):
        """Can skip coping package resources to directory if already present."""
        with TemporaryDirectory() as tmp_path:
            output_path = Path(tmp_path)
        src_ref = "assets_tracking_service.lib.bas_data_catalogue.resources.xsl.iso-html"
        dest_path = output_path / "xsl" / "iso-html"

        fx_lib_exporter_base._dump_package_resources(src_ref=src_ref, dest_path=dest_path)
        init_time = dest_path.stat().st_mtime

        fx_lib_exporter_base._dump_package_resources(src_ref=src_ref, dest_path=dest_path)
        rpt_time = dest_path.stat().st_mtime

        assert init_time == rpt_time


class TestBaseResourceExporter:
    """Test base resource exporter."""

    def test_init(
        self,
        mocker: MockerFixture,
        fx_logger: logging.Logger,
        fx_lib_exporter_base: Exporter,
        fx_s3_bucket_name: str,
        fx_s3_client: S3Client,
        fx_lib_record_minimal_item: Record,
    ):
        """Can create an Exporter."""
        with TemporaryDirectory() as tmp_path:
            output_path = Path(tmp_path)
        mock_config = mocker.Mock()
        type(mock_config).EXPORTER_DATA_CATALOGUE_AWS_S3_BUCKET = PropertyMock(return_value=fx_s3_bucket_name)
        type(mock_config).EXPORTER_DATA_CATALOGUE_OUTPUT_PATH = PropertyMock(return_value=output_path)
        fx_lib_exporter_base._config = mock_config

        exporter = ResourceExporter(
            config=mock_config,
            logger=fx_logger,
            s3=fx_s3_client,
            record=fx_lib_record_minimal_item,
            export_base=output_path.joinpath("x"),
            export_name="x.txt",
        )
        assert isinstance(exporter, ResourceExporter)

    def test_invalid_record(self, fx_lib_exporter_resource_base: ResourceExporter, fx_lib_record_minimal_iso: Record):
        """Cannot create an ItemBase with an invalid record."""
        with pytest.raises(ValueError, match="File identifier must be set to export record."):
            ResourceExporter(
                config=fx_lib_exporter_resource_base._config,
                logger=fx_lib_exporter_resource_base._logger,
                s3=fx_lib_exporter_resource_base._s3_client,
                record=fx_lib_record_minimal_iso,
                export_base=fx_lib_exporter_resource_base._export_path.parent,
                export_name="x",
            )

    def test_init_invalid_base_path(self, fx_lib_exporter_resource_base: ResourceExporter):
        """Cannot create an ItemBase with a base path that isn't relative to overall output_path."""
        with TemporaryDirectory() as tmp_path_exporter:
            alt_path = Path(tmp_path_exporter)
        with pytest.raises(ValueError, match="Export base must be relative to EXPORTER_DATA_CATALOGUE_OUTPUT_PATH."):
            ResourceExporter(
                config=fx_lib_exporter_resource_base._config,
                logger=fx_lib_exporter_resource_base._logger,
                s3=fx_lib_exporter_resource_base._s3_client,
                record=fx_lib_exporter_resource_base._record,
                export_base=alt_path,
                export_name="x",
            )

    def test_name_invalid(self, fx_lib_exporter_resource_base: ResourceExporter):
        """Cannot get exporter name from base exporter."""
        with pytest.raises(NotImplementedError):
            _ = fx_lib_exporter_resource_base.name

    def test_dumps_invalid(self, fx_lib_exporter_resource_base: ResourceExporter):
        """Cannot generate a record in a derived format from base exporter."""
        with pytest.raises(NotImplementedError):
            _ = fx_lib_exporter_resource_base.dumps()

    def test_export(self, fx_lib_exporter_resource_base: ResourceExporter):
        """Can write output to a file at a high level."""
        exporter = FakeResourceExporter(
            config=fx_lib_exporter_resource_base._config,
            logger=fx_lib_exporter_resource_base._logger,
            s3=fx_lib_exporter_resource_base._s3_client,
            record=fx_lib_exporter_resource_base._record,
            export_base=fx_lib_exporter_resource_base._export_path.parent,
        )
        exporter.export()
        assert exporter._export_path.exists()

    def test_publish(self, fx_s3_bucket_name: str, fx_lib_exporter_resource_base: ResourceExporter):
        """Can write output to an object at a high level."""
        exporter = FakeResourceExporter(
            config=fx_lib_exporter_resource_base._config,
            logger=fx_lib_exporter_resource_base._logger,
            s3=fx_lib_exporter_resource_base._s3_client,
            record=fx_lib_exporter_resource_base._record,
            export_base=fx_lib_exporter_resource_base._export_path.parent,
        )
        exporter.publish()

        result = exporter._s3_utils._s3.list_objects_v2(Bucket=fx_s3_bucket_name)
        assert len(result["Contents"]) == 1

    def test_publish_unknown_media_type(self, fx_s3_bucket_name: str, fx_lib_exporter_resource_base: ResourceExporter):
        """Can write output with default media type where unknown to an object."""
        exporter = FakeResourceExporter(
            config=fx_lib_exporter_resource_base._config,
            logger=fx_lib_exporter_resource_base._logger,
            s3=fx_lib_exporter_resource_base._s3_client,
            record=fx_lib_exporter_resource_base._record,
            export_base=fx_lib_exporter_resource_base._export_path.parent,
        )
        exporter._export_path = exporter._export_path / "x.unknown"
        exporter.publish()

        result = exporter._s3_utils._s3.get_object(Bucket=fx_s3_bucket_name, Key="x/x.txt/x.unknown")
        assert result["ContentType"] == "application/octet-stream"
