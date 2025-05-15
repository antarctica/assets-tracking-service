from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import PropertyMock

import pytest
from pytest_mock import MockerFixture

from assets_tracking_service.config import Config
from assets_tracking_service.lib.bas_data_catalogue.exporters.base_exporter import Exporter, S3Utils
from assets_tracking_service.lib.bas_data_catalogue.models.record import Record


class TestS3Utils:
    """Test S3 utility methods."""

    def test_init(self, mocker: MockerFixture, fx_s3_bucket_name: str):
        """Can create instance."""
        with TemporaryDirectory() as tmp_path:
            path = Path(tmp_path)
        s3_client = mocker.MagicMock()

        s3_utils = S3Utils(s3=s3_client, s3_bucket=fx_s3_bucket_name, relative_base=path)
        assert isinstance(s3_utils, S3Utils)

    def test_calc_s3_key(self, fx_lib_s3_utils: S3Utils):
        """Can get S3 key from path relative to site base."""
        expected = "x/y/z.txt"
        path = fx_lib_s3_utils._relative_base.joinpath(expected)

        actual = fx_lib_s3_utils.calc_key(path=path)
        assert actual == expected

    def test_upload_content(self, fx_s3_bucket_name: str, fx_lib_s3_utils: S3Utils):
        """Can write output to an object at a low level."""
        expected = "x"

        fx_lib_s3_utils.upload_content(key=expected, content_type="text/plain", body="x")

        result = fx_lib_s3_utils._s3.list_objects_v2(Bucket=fx_s3_bucket_name)
        assert len(result["Contents"]) == 1
        result = result["Contents"][0]
        assert result["Key"] == expected

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


class TestBaseExporter:
    """Test base exporter."""

    def test_init(self, mocker: MockerFixture, fx_lib_record_minimal_item: Record):
        """Can create an Exporter."""
        with TemporaryDirectory() as tmp_path:
            output_path = Path(tmp_path)
        s3_client = mocker.MagicMock()
        mock_config = mocker.Mock()
        type(mock_config).EXPORTER_DATA_CATALOGUE_OUTPUT_PATH = PropertyMock(return_value=output_path)

        base = Exporter(
            config=mock_config,
            s3=s3_client,
            record=fx_lib_record_minimal_item,
            export_base=output_path.joinpath("x"),
            export_name="x.txt",
        )

        assert isinstance(base, Exporter)

    def test_init_invalid_record(self, mocker: MockerFixture, fx_config: Config, fx_lib_record_minimal_iso: Record):
        """Cannot create an ItemBase with an invalid record."""
        with TemporaryDirectory() as tmp_path:
            output_path = Path(tmp_path)
        s3_client = mocker.MagicMock()

        with pytest.raises(ValueError, match="File identifier must be set to export record."):
            Exporter(
                config=fx_config,
                s3=s3_client,
                record=fx_lib_record_minimal_iso,
                export_base=output_path,
                export_name="x",
            )

    def test_init_invalid_base_path(self, mocker: MockerFixture, fx_config: Config, fx_lib_record_minimal_item: Record):
        """Cannot create an ItemBase with a base path that isn't relative to overall output_path."""
        with TemporaryDirectory() as tmp_path_site:
            output_path = Path(tmp_path_site)
        with TemporaryDirectory() as tmp_path_exporter:
            export_path = Path(tmp_path_exporter)
        s3_client = mocker.MagicMock()
        mock_config = mocker.Mock()
        type(mock_config).EXPORTER_DATA_CATALOGUE_OUTPUT_PATH = PropertyMock(return_value=output_path)

        with pytest.raises(ValueError, match="Export base must be relative to EXPORTER_DATA_CATALOGUE_OUTPUT_PATH."):
            Exporter(
                config=fx_config,
                s3=s3_client,
                record=fx_lib_record_minimal_item,
                export_base=export_path,
                export_name="x",
            )

    def test_name_invalid(self, mocker: MockerFixture, fx_lib_record_minimal_item: Record):
        """Cannot get exporter name from base exporter."""
        with TemporaryDirectory() as tmp_path:
            output_path = Path(tmp_path)
        s3_client = mocker.MagicMock()
        mock_config = mocker.Mock()
        type(mock_config).EXPORTER_DATA_CATALOGUE_OUTPUT_PATH = PropertyMock(return_value=output_path)
        exporter = Exporter(
            config=mock_config,
            s3=s3_client,
            record=fx_lib_record_minimal_item,
            export_base=output_path.joinpath("x"),
            export_name="x.txt",
        )

        with pytest.raises(NotImplementedError):
            _ = exporter.name

    def test_dump(self, fx_lib_exporter_base: Exporter):
        """Can write output to a file at a low level."""
        expected = fx_lib_exporter_base._export_path

        fx_lib_exporter_base._dump(path=expected)
        assert expected.exists()

    def test_dump_package_resources(self, fx_lib_exporter_base: Exporter):
        """Can copy package resources to directory if not already present."""
        src_ref = "assets_tracking_service.lib.bas_data_catalogue.resources.xsl.iso-html"
        dest_path = fx_lib_exporter_base._export_path / "xsl" / "iso-html"

        fx_lib_exporter_base._dump_package_resources(src_ref=src_ref, dest_path=dest_path)

        assert dest_path.exists()

    @pytest.mark.cov()
    def test_dump_package_resources_repeat(self, fx_lib_exporter_base: Exporter):
        """Can skip coping package resources to directory if already present."""
        src_ref = "assets_tracking_service.lib.bas_data_catalogue.resources.xsl.iso-html"
        dest_path = fx_lib_exporter_base._export_path / "xsl" / "iso-html"
        fx_lib_exporter_base._dump_package_resources(src_ref=src_ref, dest_path=dest_path)
        init_time = dest_path.stat().st_mtime

        fx_lib_exporter_base._dump_package_resources(src_ref=src_ref, dest_path=dest_path)
        rpt_time = dest_path.stat().st_mtime

        assert init_time == rpt_time

    def test_dumps_invalid(self, mocker: MockerFixture, fx_lib_record_minimal_item: Record):
        """Cannot generate a record in a derived format from base exporter."""
        with TemporaryDirectory() as tmp_path:
            output_path = Path(tmp_path)
        s3_client = mocker.MagicMock()
        mock_config = mocker.Mock()
        type(mock_config).EXPORTER_DATA_CATALOGUE_OUTPUT_PATH = PropertyMock(return_value=output_path)
        exporter = Exporter(
            config=mock_config,
            s3=s3_client,
            record=fx_lib_record_minimal_item,
            export_base=output_path.joinpath("x"),
            export_name="x.txt",
        )

        with pytest.raises(NotImplementedError):
            exporter.dumps()

    def test_export(self, fx_lib_exporter_base: Exporter):
        """Can write output to a file at a high level."""
        fx_lib_exporter_base.export()
        assert fx_lib_exporter_base._export_path.exists()

    def test_publish(self, fx_s3_bucket_name: str, fx_lib_exporter_base: Exporter):
        """Can write output to an object at a high level."""
        fx_lib_exporter_base.publish()

        result = fx_lib_exporter_base._s3_utils._s3.list_objects_v2(Bucket=fx_s3_bucket_name)
        assert len(result["Contents"]) == 1

    def test_publish_unknown_media_type(self, fx_s3_bucket_name: str, fx_lib_exporter_base: Exporter):
        """Can write output with default media type where unknown to an object."""
        fx_lib_exporter_base._export_path = fx_lib_exporter_base._export_path / "x.unknown"

        fx_lib_exporter_base.publish()

        result = fx_lib_exporter_base._s3_utils._s3.get_object(Bucket=fx_s3_bucket_name, Key="x/x.txt/x.unknown")
        assert result["ContentType"] == "application/octet-stream"
