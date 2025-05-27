import logging
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import PropertyMock

from bs4 import BeautifulSoup
from pytest_mock import MockerFixture

from assets_tracking_service.lib.bas_data_catalogue.exporters.site_exporter import (
    SiteExporter,
    SiteIndexExporter,
    SitePagesExporter,
    SiteResourcesExporter,
)
from assets_tracking_service.lib.bas_data_catalogue.models.record import Record
from assets_tracking_service.lib.bas_data_catalogue.models.record.summary import RecordSummary


class TestSiteIndexExporter:
    """Test site index exporter."""

    def test_init(self, mocker: MockerFixture, fx_logger: logging.Logger):
        """Can create an Exporter."""
        with TemporaryDirectory() as tmp_path:
            output_path = Path(tmp_path)
        s3_client = mocker.MagicMock()
        mock_config = mocker.Mock()
        type(mock_config).EXPORTER_DATA_CATALOGUE_OUTPUT_PATH = PropertyMock(return_value=output_path)

        exporter = SiteIndexExporter(config=mock_config, s3=s3_client, logger=fx_logger)

        assert isinstance(exporter, SiteIndexExporter)
        assert exporter.name == "Site Index"
        assert len(exporter._summaries) == 0

    def test_loads(self, fx_lib_exporter_site_index: SiteIndexExporter, fx_lib_record_minimal_item_catalogue: Record):
        """Can load summaries."""
        summaries = [RecordSummary.loads(fx_lib_record_minimal_item_catalogue)]
        fx_lib_exporter_site_index.loads(summaries)
        assert len(fx_lib_exporter_site_index._summaries) == len(summaries)

    def test_dumps(self, fx_lib_exporter_site_index_pop: SiteIndexExporter):
        """Can dump site index."""
        result = fx_lib_exporter_site_index_pop._dumps()
        assert "<h1>Proto Items Index</h1>" in result
        assert '<ul><li><a href="/items/x/index.html">[DATASET] x - x (None)</a></li></ul>' in result

    def test_export(self, fx_lib_exporter_site_index_pop: SiteIndexExporter):
        """Can export site index to a local file."""
        site_path = fx_lib_exporter_site_index_pop._config.EXPORTER_DATA_CATALOGUE_OUTPUT_PATH
        expected = site_path.joinpath("-", "index", "index.html")

        fx_lib_exporter_site_index_pop.export()

        result = list(fx_lib_exporter_site_index_pop._config.EXPORTER_DATA_CATALOGUE_OUTPUT_PATH.glob("**/*.*"))
        assert expected in result

    def test_publish(self, fx_lib_exporter_site_index_pop: SiteIndexExporter, fx_s3_bucket_name: str):
        """Can publish site index to S3."""
        site_path = fx_lib_exporter_site_index_pop._config.EXPORTER_DATA_CATALOGUE_OUTPUT_PATH

        fx_lib_exporter_site_index_pop.publish()

        output = fx_lib_exporter_site_index_pop._s3_utils._s3.get_object(
            Bucket=fx_s3_bucket_name,
            Key=fx_lib_exporter_site_index_pop._s3_utils.calc_key(site_path.joinpath("-", "index", "index.html")),
        )
        assert output["ResponseMetadata"]["HTTPStatusCode"] == 200


class TestSitePageExporter:
    """Test site pages exporter."""

    def test_init(self, mocker: MockerFixture, fx_logger: logging.Logger):
        """Can create an Exporter."""
        with TemporaryDirectory() as tmp_path:
            output_path = Path(tmp_path)
        s3_client = mocker.MagicMock()
        mock_config = mocker.Mock()
        type(mock_config).EXPORTER_DATA_CATALOGUE_OUTPUT_PATH = PropertyMock(return_value=output_path)

        exporter = SitePagesExporter(config=mock_config, s3=s3_client, logger=fx_logger)

        assert isinstance(exporter, SitePagesExporter)
        assert exporter.name == "Site Pages"

    def test_dumps(self, fx_lib_exporter_site_pages: SitePagesExporter):
        """Can dump a site page with expected title and site title."""
        expected = "Privacy Policy | BAS Data Catalogue"
        result = fx_lib_exporter_site_pages._dumps("legal/privacy.html.j2")
        html = BeautifulSoup(result, parser="html.parser", features="lxml")

        assert html.head.title.string == expected
        assert "This website has links to other websites for which we are not responsible." in result

    def test_export_page(self, fx_lib_exporter_site_pages: SitePagesExporter):
        """Can export a site page to a local file."""
        site_path = fx_lib_exporter_site_pages._config.EXPORTER_DATA_CATALOGUE_OUTPUT_PATH
        expected = site_path.joinpath("legal/privacy/index.html")

        fx_lib_exporter_site_pages.export_page("legal/privacy.html.j2")

        assert expected.exists()

    def test_publish_page(self, fx_lib_exporter_site_pages: SitePagesExporter, fx_s3_bucket_name: str):
        """Can publish a site page to S3."""
        expected = "legal/privacy/index.html"

        fx_lib_exporter_site_pages.publish_page("legal/privacy.html.j2")

        result = fx_lib_exporter_site_pages._s3_utils._s3.get_object(Bucket=fx_s3_bucket_name, Key=expected)
        assert result["ResponseMetadata"]["HTTPStatusCode"] == 200

    def test_export(self, fx_lib_exporter_site_pages: SitePagesExporter):
        """Can export site pages to local files."""
        site_path = fx_lib_exporter_site_pages._config.EXPORTER_DATA_CATALOGUE_OUTPUT_PATH
        expected = [
            site_path.joinpath("404.html"),
            site_path.joinpath("legal/cookies/index.html"),
            site_path.joinpath("legal/copyright/index.html"),
            site_path.joinpath("legal/privacy/index.html"),
        ]

        fx_lib_exporter_site_pages.export()

        result = list(fx_lib_exporter_site_pages._config.EXPORTER_DATA_CATALOGUE_OUTPUT_PATH.glob("**/*.*"))
        for path in expected:
            assert path in result

    def test_publish(self, fx_lib_exporter_site_pages: SitePagesExporter, fx_s3_bucket_name: str):
        """Can publish site pages to S3."""
        expected = [
            "404.html",
            "legal/cookies/index.html",
            "legal/copyright/index.html",
            "legal/privacy/index.html",
        ]

        fx_lib_exporter_site_pages.publish()

        result = fx_lib_exporter_site_pages._s3_utils._s3.list_objects(Bucket=fx_s3_bucket_name)
        keys = [o["Key"] for o in result["Contents"]]
        for key in expected:
            assert key in keys


class TestSiteResourcesExporter:
    """Test site exporter."""

    def test_init(self, mocker: MockerFixture, fx_logger: logging.Logger):
        """Can create an Exporter."""
        with TemporaryDirectory() as tmp_path:
            output_path = Path(tmp_path)
        s3_client = mocker.MagicMock()
        mock_config = mocker.Mock()
        type(mock_config).EXPORTER_DATA_CATALOGUE_OUTPUT_PATH = PropertyMock(return_value=output_path)

        exporter = SiteResourcesExporter(config=mock_config, logger=fx_logger, s3=s3_client)

        assert isinstance(exporter, SiteResourcesExporter)
        assert exporter.name == "Site Resources"

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
        expected = [
            fx_lib_exporter_site_resources._export_base.joinpath("txt/heartbeat.txt"),
            fx_lib_exporter_site_resources._export_base.joinpath("txt/manifest.webmanifest"),
        ]

        fx_lib_exporter_site_resources._dump_txt()
        for path in expected:
            assert path.exists()

    def test_dump_xsl(self, fx_lib_exporter_site_resources: SiteResourcesExporter):
        """Can copy XSL files to output path."""
        expected = fx_lib_exporter_site_resources._export_base.joinpath("xsl/iso-html/xml-to-html-ISO.xsl")

        fx_lib_exporter_site_resources._dump_xsl()
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
        expected = ["static/txt/heartbeat.txt", "static/txt/manifest.webmanifest"]

        fx_lib_exporter_site_resources._publish_txt()
        for key in expected:
            result = fx_lib_exporter_site_resources._s3_utils._s3.get_object(
                Bucket=fx_lib_exporter_site_resources._s3_utils._bucket, Key=key
            )
            assert result["ResponseMetadata"]["HTTPStatusCode"] == 200

    def test_publish_xsl(self, fx_lib_exporter_site_resources: SiteResourcesExporter):
        """Can upload XSL files to S3."""
        expected = "static/xsl/iso-html/xml-to-html-ISO.xsl"

        fx_lib_exporter_site_resources._publish_xsl()
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
        assert fx_lib_exporter_site_resources._export_base.joinpath("xsl/iso-html/xml-to-html-ISO.xsl").exists()

    def test_publish(self, fx_s3_bucket_name: str, fx_lib_exporter_site_resources: SiteResourcesExporter):
        """Can upload resources to S3."""
        expected = [
            "static/css/main.css",
            "static/fonts/open-sans.ttf",
            "static/img/favicon.ico",
            "static/txt/heartbeat.txt",
            "static/xsl/iso-html/xml-to-html-ISO.xsl",
        ]

        fx_lib_exporter_site_resources.publish()

        result = fx_lib_exporter_site_resources._s3_utils._s3.list_objects(Bucket=fx_s3_bucket_name)
        keys = [o["Key"] for o in result["Contents"]]
        for key in expected:
            assert key in keys


class TestSiteExporter:
    """Test site index exporter."""

    def test_init(self, mocker: MockerFixture, fx_logger: logging.Logger):
        """Can create an Exporter."""
        with TemporaryDirectory() as tmp_path:
            output_path = Path(tmp_path)
        s3_client = mocker.MagicMock()
        mock_config = mocker.Mock()
        type(mock_config).EXPORTER_DATA_CATALOGUE_OUTPUT_PATH = PropertyMock(return_value=output_path)

        exporter = SiteExporter(config=mock_config, s3=s3_client, logger=fx_logger)

        assert isinstance(exporter, SiteExporter)
        assert exporter.name == "Site"
        assert len(exporter._index_exporter._summaries) == 0
        assert len(exporter._records_exporter._records) == 0

    def test_loads(self, fx_lib_exporter_site: SiteExporter, fx_lib_record_minimal_item_catalogue: Record):
        """Can load summaries and records."""
        records = [fx_lib_record_minimal_item_catalogue]
        summaries = [RecordSummary.loads(record) for record in records]
        fx_lib_exporter_site.loads(summaries, records)

        assert len(fx_lib_exporter_site._index_exporter._summaries) == len(summaries)
        assert len(fx_lib_exporter_site._records_exporter._records) == len(records)

    def test_export(self, fx_lib_exporter_site: SiteExporter, fx_lib_record_minimal_item_catalogue: Record):
        """Can export all site components to local files."""
        record = fx_lib_record_minimal_item_catalogue
        site_path = fx_lib_exporter_site._config.EXPORTER_DATA_CATALOGUE_OUTPUT_PATH
        fx_lib_exporter_site.loads([RecordSummary.loads(record)], [record])
        expected = [
            site_path.joinpath("favicon.ico"),
            site_path.joinpath("404.html"),
            site_path.joinpath("static", "css", "main.css"),
            site_path.joinpath("static", "xsl", "iso-html", "xml-to-html-ISO.xsl"),
            site_path.joinpath("items", record.file_identifier, "index.html"),
            site_path.joinpath("legal", "privacy", "index.html"),
            site_path.joinpath("-", "index", "index.html"),
        ]  # representative sample

        fx_lib_exporter_site.export()

        result = list(fx_lib_exporter_site._config.EXPORTER_DATA_CATALOGUE_OUTPUT_PATH.glob("**/*.*"))
        for path in expected:
            assert path in result

    def test_publish(
        self, fx_s3_bucket_name: str, fx_lib_exporter_site: SiteExporter, fx_lib_record_minimal_item_catalogue: Record
    ):
        """Can publish site index to S3."""
        s3 = fx_lib_exporter_site._index_exporter._s3_utils._s3
        record = fx_lib_record_minimal_item_catalogue
        fx_lib_exporter_site.loads([RecordSummary.loads(record)], [record])
        expected = [
            "favicon.ico",
            "404.html",
            "static/css/main.css",
            "static/xsl/iso-html/xml-to-html-ISO.xsl",
            f"items/{record.file_identifier}/index.html",
            "legal/privacy/index.html",
            "-/index/index.html",
        ]  # representative sample

        fx_lib_exporter_site.publish()

        result = s3.list_objects(Bucket=fx_s3_bucket_name)
        keys = [o["Key"] for o in result["Contents"]]
        for key in expected:
            assert key in keys
