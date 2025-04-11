from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import PropertyMock

import pytest
from pytest_mock import MockerFixture

from assets_tracking_service.config import Config
from assets_tracking_service.lib.bas_data_catalogue.exporters.base_exporter import Exporter
from assets_tracking_service.lib.bas_data_catalogue.models.record import Record


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
            s3_client=s3_client,
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
                s3_client=s3_client,
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
                s3_client=s3_client,
                record=fx_lib_record_minimal_item,
                export_base=export_path,
                export_name="x",
            )

    def test_dump(self, fx_lib_exporter_base: Exporter):
        """Can write output to a file at a low level."""
        expected = fx_lib_exporter_base._export_path

        fx_lib_exporter_base._dump(path=expected)
        assert expected.exists()

    def test_put_object(self, fx_s3_bucket_name: str, fx_lib_exporter_base: Exporter):
        """Can write output to an object at a low level."""
        expected = "x"

        fx_lib_exporter_base._put_object(key=expected, content_type="text/plain", body="x")

        result = fx_lib_exporter_base._s3_client.list_objects_v2(Bucket=fx_s3_bucket_name)
        assert len(result["Contents"]) == 1
        result = result["Contents"][0]
        assert result["Key"] == expected

    def test_put_object_redirect(self, fx_s3_bucket_name: str, fx_lib_exporter_base: Exporter):
        """Can write output to an object with a object redirect."""
        key = "x"
        expected = "y"

        fx_lib_exporter_base._put_object(key=key, content_type="text/plain", body="x", redirect="y")

        result = fx_lib_exporter_base._s3_client.get_object(Bucket=fx_s3_bucket_name, Key=key)
        assert result["WebsiteRedirectLocation"] == expected

    def test_calc_s3_key(self, fx_lib_exporter_base: Exporter):
        """Can get S3 key from path relative to site base."""
        expected = "x/y/z.txt"
        path = fx_lib_exporter_base._config.EXPORTER_DATA_CATALOGUE_OUTPUT_PATH.joinpath(expected)

        actual = fx_lib_exporter_base._calc_s3_key(path=path)
        assert actual == expected

    def test_dumps_invalid(self, mocker: MockerFixture, fx_lib_record_minimal_item: Record):
        """Cannot export record from base exporter."""
        with TemporaryDirectory() as tmp_path:
            output_path = Path(tmp_path)
        s3_client = mocker.MagicMock()
        mock_config = mocker.Mock()
        type(mock_config).EXPORTER_DATA_CATALOGUE_OUTPUT_PATH = PropertyMock(return_value=output_path)
        exporter = Exporter(
            config=mock_config,
            s3_client=s3_client,
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

        result = fx_lib_exporter_base._s3_client.list_objects_v2(Bucket=fx_s3_bucket_name)
        assert len(result["Contents"]) == 1

    def test_publish_unknown_media_type(self, fx_s3_bucket_name: str, fx_lib_exporter_base: Exporter):
        """Can write output with default media type where unknown to an object."""
        fx_lib_exporter_base._export_path = fx_lib_exporter_base._export_path / "x.unknown"

        fx_lib_exporter_base.publish()

        result = fx_lib_exporter_base._s3_client.get_object(Bucket=fx_s3_bucket_name, Key="x/x.txt/x.unknown")
        assert result["ContentType"] == "application/octet-stream"
