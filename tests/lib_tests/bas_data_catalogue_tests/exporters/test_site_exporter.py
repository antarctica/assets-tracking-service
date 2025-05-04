from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import PropertyMock

from pytest_mock import MockerFixture

from assets_tracking_service.lib.bas_data_catalogue.exporters.site_exporter import SiteResourcesExporter


class TestSiteResourcesExporter:
    """Test site exporter."""

    def test_init(self, mocker: MockerFixture):
        """Can create an Exporter."""
        with TemporaryDirectory() as tmp_path:
            output_path = Path(tmp_path)
        s3_client = mocker.MagicMock()
        mock_config = mocker.Mock()
        type(mock_config).EXPORTER_DATA_CATALOGUE_OUTPUT_PATH = PropertyMock(return_value=output_path)

        exporter = SiteResourcesExporter(config=mock_config, s3_client=s3_client)

        assert isinstance(exporter, SiteResourcesExporter)

    def test_dump_css(self, fx_lib_exporter_site_resources: SiteResourcesExporter):
        """Can copy CSS to output path."""
        expected = fx_lib_exporter_site_resources._export_base.joinpath("css/main.css")

        fx_lib_exporter_site_resources._dump_css()
        assert expected.exists()

    def test_dump_fonts(self, fx_lib_exporter_site_resources: SiteResourcesExporter):
        """Can copy fonts to output path."""
        expected = fx_lib_exporter_site_resources._export_base.joinpath("fonts/open-sans.ttf")

        fx_lib_exporter_site_resources._dump_fonts()
        assert expected.exists()

    def test_dump_favicon_ico(self, fx_lib_exporter_site_resources: SiteResourcesExporter):
        """Can copy favicon.ico to output path."""
        expected = fx_lib_exporter_site_resources._export_base.parent.joinpath("favicon.ico")

        fx_lib_exporter_site_resources._dump_favicon_ico()
        assert expected.exists()

    def test_dump_img(self, fx_lib_exporter_site_resources: SiteResourcesExporter):
        """Can copy images to output path."""
        expected = fx_lib_exporter_site_resources._export_base.joinpath("img/favicon.ico")

        fx_lib_exporter_site_resources._dump_img()
        assert expected.exists()

    def test_dump_txt(self, fx_lib_exporter_site_resources: SiteResourcesExporter):
        """Can copy text files to output path."""
        expected = fx_lib_exporter_site_resources._export_base.joinpath("txt/heartbeat.txt")

        fx_lib_exporter_site_resources._dump_txt()
        assert expected.exists()

    def test_publish_css(self, fx_lib_exporter_site_resources: SiteResourcesExporter):
        """Can upload CSS to S3."""
        expected = "static/css/main.css"

        fx_lib_exporter_site_resources._publish_css()
        result = fx_lib_exporter_site_resources._s3_utils._s3.get_object(
            Bucket=fx_lib_exporter_site_resources._s3_utils._bucket, Key=expected
        )
        assert result["ResponseMetadata"]["HTTPStatusCode"] == 200

    def test_publish_fonts(self, fx_lib_exporter_site_resources: SiteResourcesExporter):
        """Can upload fonts to S3."""
        expected = "static/fonts/open-sans.ttf"

        fx_lib_exporter_site_resources._publish_fonts()
        result = fx_lib_exporter_site_resources._s3_utils._s3.get_object(
            Bucket=fx_lib_exporter_site_resources._s3_utils._bucket, Key=expected
        )
        assert result["ResponseMetadata"]["HTTPStatusCode"] == 200

    def test_publish_favicon_ico(self, fx_lib_exporter_site_resources: SiteResourcesExporter):
        """Can upload favicon.ico to S3."""
        expected = "favicon.ico"

        fx_lib_exporter_site_resources._publish_favicon_ico()
        result = fx_lib_exporter_site_resources._s3_utils._s3.get_object(
            Bucket=fx_lib_exporter_site_resources._s3_utils._bucket, Key=expected
        )
        assert result["ResponseMetadata"]["HTTPStatusCode"] == 200

    def test_publish_img(self, fx_lib_exporter_site_resources: SiteResourcesExporter):
        """Can upload images to S3."""
        expected = "static/img/favicon.ico"

        fx_lib_exporter_site_resources._publish_img()
        result = fx_lib_exporter_site_resources._s3_utils._s3.get_object(
            Bucket=fx_lib_exporter_site_resources._s3_utils._bucket, Key=expected
        )
        assert result["ResponseMetadata"]["HTTPStatusCode"] == 200

    def test_publish_txt(self, fx_lib_exporter_site_resources: SiteResourcesExporter):
        """Can upload text files to S3."""
        expected = "static/txt/heartbeat.txt"

        fx_lib_exporter_site_resources._publish_txt()
        result = fx_lib_exporter_site_resources._s3_utils._s3.get_object(
            Bucket=fx_lib_exporter_site_resources._s3_utils._bucket, Key=expected
        )
        assert result["ResponseMetadata"]["HTTPStatusCode"] == 200

    def test_export(self, fx_lib_exporter_site_resources: SiteResourcesExporter):
        """Can copy resources to output path."""
        fx_lib_exporter_site_resources.export()
        assert fx_lib_exporter_site_resources._export_base.joinpath("css/main.css").exists()
        assert fx_lib_exporter_site_resources._export_base.joinpath("fonts/open-sans.ttf").exists()
        assert fx_lib_exporter_site_resources._export_base.joinpath("img/favicon.ico").exists()
        assert fx_lib_exporter_site_resources._export_base.joinpath("txt/heartbeat.txt").exists()

    def test_publish(self, fx_lib_exporter_site_resources: SiteResourcesExporter):
        """Can upload resources to S3."""
        fx_lib_exporter_site_resources.publish()
        assert (
            fx_lib_exporter_site_resources._s3_utils._s3.get_object(
                Bucket=fx_lib_exporter_site_resources._s3_utils._bucket, Key="static/css/main.css"
            )["ResponseMetadata"]["HTTPStatusCode"]
            == 200
        )
        assert (
            fx_lib_exporter_site_resources._s3_utils._s3.get_object(
                Bucket=fx_lib_exporter_site_resources._s3_utils._bucket, Key="static/fonts/open-sans.ttf"
            )["ResponseMetadata"]["HTTPStatusCode"]
            == 200
        )
        assert (
            fx_lib_exporter_site_resources._s3_utils._s3.get_object(
                Bucket=fx_lib_exporter_site_resources._s3_utils._bucket, Key="static/img/favicon.ico"
            )["ResponseMetadata"]["HTTPStatusCode"]
            == 200
        )
        assert (
            fx_lib_exporter_site_resources._s3_utils._s3.get_object(
                Bucket=fx_lib_exporter_site_resources._s3_utils._bucket, Key="static/txt/heartbeat.txt"
            )["ResponseMetadata"]["HTTPStatusCode"]
            == 200
        )
