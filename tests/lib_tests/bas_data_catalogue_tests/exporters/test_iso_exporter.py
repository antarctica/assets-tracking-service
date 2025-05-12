from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import PropertyMock

from bas_metadata_library.standards.iso_19115_2 import MetadataRecord
from bas_metadata_library.standards.iso_19115_common.utils import _encode_date_properties
from boto3 import client as S3Client  # noqa: N812
from pytest_mock import MockerFixture

from assets_tracking_service.lib.bas_data_catalogue.exporters.iso_exporter import IsoXmlExporter, IsoXmlHtmlExporter
from assets_tracking_service.lib.bas_data_catalogue.models.record import Record


class TestIsoXmlExporter:
    """Test ISO 19115 XML exporter."""

    def test_init(
        self, mocker: MockerFixture, fx_s3_bucket_name: str, fx_s3_client: S3Client, fx_lib_record_minimal_item: Record
    ):
        """Can create an ISO XML Exporter."""
        with TemporaryDirectory() as tmp_path:
            output_path = Path(tmp_path)
        mock_config = mocker.Mock()
        type(mock_config).EXPORTER_DATA_CATALOGUE_OUTPUT_PATH = PropertyMock(return_value=output_path)
        type(mock_config).EXPORTER_DATA_CATALOGUE_AWS_S3_BUCKET = PropertyMock(return_value=fx_s3_bucket_name)
        expected = output_path.joinpath(f"{fx_lib_record_minimal_item.file_identifier}.xml")

        exporter = IsoXmlExporter(
            config=mock_config, s3=fx_s3_client, record=fx_lib_record_minimal_item, export_base=output_path
        )

        assert isinstance(exporter, IsoXmlExporter)
        assert exporter.name == "ISO XML"
        assert exporter._export_path == expected

    def test_dumps(
        self, mocker: MockerFixture, fx_s3_bucket_name: str, fx_s3_client: S3Client, fx_lib_record_minimal_item: Record
    ):
        """Can encode record as ISO 19139 XML string."""
        with TemporaryDirectory() as tmp_path:
            output_path = Path(tmp_path)
        mock_config = mocker.Mock()
        type(mock_config).EXPORTER_DATA_CATALOGUE_OUTPUT_PATH = PropertyMock(return_value=output_path)
        type(mock_config).EXPORTER_DATA_CATALOGUE_AWS_S3_BUCKET = PropertyMock(return_value=fx_s3_bucket_name)
        expected = fx_lib_record_minimal_item.dumps()

        exporter = IsoXmlExporter(
            config=mock_config, s3=fx_s3_client, record=fx_lib_record_minimal_item, export_base=output_path
        )

        result = exporter.dumps()
        assert "<gmi:MI_Metadata" in result
        config = _encode_date_properties(MetadataRecord(record=result).make_config().config)
        assert config == expected


class TestIsoXmlHtmlExporter:
    """Test ISO 19115 XML as HTML exporter."""

    def test_init(
        self, mocker: MockerFixture, fx_s3_bucket_name: str, fx_s3_client: S3Client, fx_lib_record_minimal_item: Record
    ):
        """Can create an ISO XML as HTML Exporter."""
        with TemporaryDirectory() as tmp_path:
            base_path = Path(tmp_path)
            exports_path = base_path.joinpath("exports")
            stylesheets_path = base_path.joinpath("static")
        mock_config = mocker.Mock()
        type(mock_config).EXPORTER_DATA_CATALOGUE_OUTPUT_PATH = PropertyMock(return_value=base_path)
        type(mock_config).EXPORTER_DATA_CATALOGUE_AWS_S3_BUCKET = PropertyMock(return_value=fx_s3_bucket_name)

        exporter = IsoXmlHtmlExporter(
            config=mock_config,
            s3=fx_s3_client,
            record=fx_lib_record_minimal_item,
            export_base=exports_path,
            stylesheets_base=stylesheets_path,
        )
        expected = exports_path.joinpath(f"{fx_lib_record_minimal_item.file_identifier}.html")

        assert isinstance(exporter, IsoXmlHtmlExporter)
        assert exporter.name == "ISO XML HTML"
        assert exporter._export_path == expected
        assert exporter._stylesheet_url == "static/xml-to-html-ISO.xsl"

    def test_dumps(self, fx_lib_exporter_iso_xml_html: IsoXmlHtmlExporter):
        """Can prepend stylesheet to string from IsoXmlExporter."""
        expected = '<?xml-stylesheet type="text/xsl" href="static/xml-to-html-ISO.xsl"?>\n<gmi:MI_Metadata'
        result = fx_lib_exporter_iso_xml_html.dumps()
        assert expected in result

    def test_dump_xsl(self, fx_lib_exporter_iso_xml_html: IsoXmlHtmlExporter):
        """Can copy stylesheets to output directory."""
        expected = fx_lib_exporter_iso_xml_html._stylesheets_path / "xml-to-html-ISO.xsl"
        fx_lib_exporter_iso_xml_html._dump_xsl()
        assert expected.exists()

    def test_publish_xsl(self, fx_s3_bucket_name: str, fx_lib_exporter_iso_xml_html: IsoXmlHtmlExporter):
        """Can upload stylesheets to S3 bucket."""
        expected = fx_lib_exporter_iso_xml_html._stylesheet_url
        fx_lib_exporter_iso_xml_html._publish_xsl()

        result = fx_lib_exporter_iso_xml_html._s3_utils._s3.get_object(Bucket=fx_s3_bucket_name, Key=expected)
        assert result["ResponseMetadata"]["HTTPStatusCode"] == 200

    def test_export(self, fx_lib_exporter_iso_xml_html: IsoXmlHtmlExporter):
        """Can copy output and stylesheets to output directory."""
        fx_lib_exporter_iso_xml_html.export()
        assert fx_lib_exporter_iso_xml_html._stylesheets_path.joinpath("xml-to-html-ISO.xsl").exists()
        assert fx_lib_exporter_iso_xml_html._export_path.exists()

    def test_publish(self, fx_s3_bucket_name: str, fx_lib_exporter_iso_xml_html: IsoXmlHtmlExporter):
        """Can copy output and stylesheets to output bucket."""
        fx_lib_exporter_iso_xml_html.publish()

        output = fx_lib_exporter_iso_xml_html._s3_utils._s3.get_object(
            Bucket=fx_s3_bucket_name,
            Key=fx_lib_exporter_iso_xml_html._s3_utils.calc_key(fx_lib_exporter_iso_xml_html._export_path),
        )
        assert output["ResponseMetadata"]["HTTPStatusCode"] == 200

        stylesheet = fx_lib_exporter_iso_xml_html._s3_client.get_object(
            Bucket=fx_s3_bucket_name, Key=fx_lib_exporter_iso_xml_html._stylesheet_url
        )
        assert stylesheet["ResponseMetadata"]["HTTPStatusCode"] == 200
