from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import PropertyMock

from boto3 import client as S3Client  # noqa: N812
from pytest_mock import MockerFixture

from assets_tracking_service.lib.bas_data_catalogue.exporters.html_exporter import HtmlAliasesExporter, HtmlExporter
from assets_tracking_service.lib.bas_data_catalogue.models.record import Record
from tests.conftest import _lib_get_record_summary


class TestHtmlExporter:
    """Test Data Catalogue HTML exporter."""

    def test_init(
        self, mocker: MockerFixture, fx_s3_bucket_name: str, fx_s3_client: S3Client, fx_lib_record_minimal_item: Record
    ):
        """Can create an HTML Exporter."""
        with TemporaryDirectory() as tmp_path:
            output_path = Path(tmp_path)
        mock_config = mocker.Mock()
        type(mock_config).EXPORTER_DATA_CATALOGUE_OUTPUT_PATH = PropertyMock(return_value=output_path)
        type(mock_config).EXPORTER_DATA_CATALOGUE_AWS_S3_BUCKET = PropertyMock(return_value=fx_s3_bucket_name)
        expected = output_path.joinpath(f"{fx_lib_record_minimal_item.file_identifier}/index.html")

        exporter = HtmlExporter(
            config=mock_config,
            s3_client=fx_s3_client,
            record=fx_lib_record_minimal_item,
            export_base=output_path,
            get_record_summary=_lib_get_record_summary,
        )

        assert isinstance(exporter, HtmlExporter)
        assert exporter._export_path == expected

    def test_dumps(
        self,
        mocker: MockerFixture,
        fx_s3_bucket_name: str,
        fx_s3_client: S3Client,
        fx_lib_record_minimal_item_catalogue: Record,
    ):
        """Can encode record as Data Catalogue item page."""
        with TemporaryDirectory() as tmp_path:
            output_path = Path(tmp_path)
        mock_config = mocker.Mock()
        type(mock_config).EXPORTER_DATA_CATALOGUE_OUTPUT_PATH = PropertyMock(return_value=output_path)
        type(mock_config).EXPORTER_DATA_CATALOGUE_AWS_S3_BUCKET = PropertyMock(return_value=fx_s3_bucket_name)
        type(mock_config).EXPORTER_DATA_CATALOGUE_EMBEDDED_MAPS_ENDPOINT = PropertyMock(return_value="x")
        type(mock_config).EXPORTER_DATA_CATALOGUE_ITEM_CONTACT_ENDPOINT = PropertyMock(return_value="x")
        exporter = HtmlExporter(
            config=mock_config,
            s3_client=fx_s3_client,
            record=fx_lib_record_minimal_item_catalogue,
            export_base=output_path,
            get_record_summary=_lib_get_record_summary,
        )

        result = exporter.dumps()
        assert "<!DOCTYPE html>" in result


class TestHtmlAliasesExporter:
    """Test HTML alias redirect exporter."""

    def test_init(
        self, mocker: MockerFixture, fx_s3_bucket_name: str, fx_s3_client: S3Client, fx_lib_record_minimal_item: Record
    ):
        """Can create an HTML alias Exporter."""
        with TemporaryDirectory() as tmp_path:
            output_path = Path(tmp_path)
        mock_config = mocker.Mock()
        type(mock_config).EXPORTER_DATA_CATALOGUE_OUTPUT_PATH = PropertyMock(return_value=output_path)
        type(mock_config).EXPORTER_DATA_CATALOGUE_AWS_S3_BUCKET = PropertyMock(return_value=fx_s3_bucket_name)

        exporter = HtmlAliasesExporter(
            config=mock_config, s3_client=fx_s3_client, record=fx_lib_record_minimal_item, site_base=output_path
        )

        assert isinstance(exporter, HtmlAliasesExporter)

    def test_get_aliases(self, fx_lib_exporter_html_alias: HtmlAliasesExporter):
        """Can process any alias identifiers in record."""
        result = fx_lib_exporter_html_alias._get_aliases()
        assert result == ["datasets/x"]

    def test_dumps(self, fx_lib_exporter_html_alias: HtmlAliasesExporter):
        """Can generate fallback redirection page."""
        expected = fx_lib_exporter_html_alias._record.file_identifier

        result = fx_lib_exporter_html_alias.dumps()
        assert "<!DOCTYPE html>" in result
        assert f'refresh" content="0;url=/items/{expected}' in result

    def test_export(self, fx_lib_exporter_html_alias: HtmlAliasesExporter):
        """Can write fallback redirection page to a file."""
        expected = fx_lib_exporter_html_alias._site_base / "datasets" / "x" / "index.html"

        fx_lib_exporter_html_alias.export()
        assert expected.exists()

    def test_publish(self, fx_s3_bucket_name: str, fx_lib_exporter_html_alias: HtmlAliasesExporter):
        """Can upload fallback redirection page as a bucket object with redirect metadata."""
        expected = "/items/x/index.html"
        fx_lib_exporter_html_alias.publish()

        result = fx_lib_exporter_html_alias._s3_client.get_object(Bucket=fx_s3_bucket_name, Key="datasets/x/index.html")
        assert result["WebsiteRedirectLocation"] == expected
