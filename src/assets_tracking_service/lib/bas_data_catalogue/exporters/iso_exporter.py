from pathlib import Path

from bas_metadata_library.standards.iso_19115_2 import MetadataRecord, MetadataRecordConfigV4
from bas_metadata_library.standards.iso_19115_common.utils import _decode_date_properties
from lxml.etree import ElementTree, ProcessingInstruction, fromstring, tostring
from mypy_boto3_s3 import S3Client

from assets_tracking_service.config import Config
from assets_tracking_service.lib.bas_data_catalogue.exporters.base_exporter import Exporter
from assets_tracking_service.lib.bas_data_catalogue.models.record import Record


class IsoXmlExporter(Exporter):
    """
    ISO 19115 XML exporter.

    Exports a Record as ISO 19115/19139 using the BAS Metadata Library [1].

    Intended for interoperability with clients that prefer ISO XML, or need access to the full underlying record.
    """

    def __init__(self, config: Config, s3_client: S3Client, record: Record, export_base: Path) -> None:
        export_name = f"{record.file_identifier}.xml"
        super().__init__(
            config=config, s3_client=s3_client, record=record, export_base=export_base, export_name=export_name
        )

    def dumps(self) -> str:
        """Encode record as XML using ISO 19139 schemas."""
        configuration = MetadataRecordConfigV4(**_decode_date_properties(self._record.dumps()))
        record = MetadataRecord(configuration=configuration)
        return record.generate_xml_document().decode()


class IsoXmlHtmlExporter(Exporter):
    """
    ISO 19115 XML (HTML) exporter.

    Exports a Record as ISO 19115/19139 using an XML stylesheet [1] to present as a low-level HTML representation.
    This stylesheet preserves the ISO 19115 structure and terminology without needing to interpret raw XML syntax.

    Intended for human inspection of ISO records, typically for evaluation or debugging.

    As browsers do not support loading XML stylesheets across origins, this exporter copies the stylesheet, and it's
    parts to a specified path/prefix. The `dumps()` method adds this location to the record to ensure consistency.

    This exporter intentionally uses a `.html` file extension despite being an `application/xml` media type so that
    both the styled (.html) and un-styled (.xml) files can be named after the record identifier in the same location.

    I.e. `/some/path/123.html` and `/some/path/123.xml`.

    [1] https://metadata-standards.data.bas.ac.uk/standards/iso-19115-19139#iso-html
    """

    def __init__(
        self,
        config: Config,
        s3_client: S3Client,
        record: Record,
        export_base: Path,
        stylesheets_base: Path,
    ) -> None:
        """
        Initialise exporter.

        `stylesheets_base` is the output directory for XML stylesheets, separate from records with this stylesheet
        applied (which is configured by `export_base`). As with `export_base`, this MUST be relative to
        `Config.EXPORTER_DATA_CATALOGUE_OUTPUT_PATH` so that a base S3 key can be generated from it.
        """
        export_name = f"{record.file_identifier}.html"
        super().__init__(
            config=config, s3_client=s3_client, record=record, export_base=export_base, export_name=export_name
        )
        self._stylesheets_src_ref = "assets_tracking_service.lib.bas_data_catalogue.resources.xsl.iso-html"
        self._stylesheets_path = stylesheets_base
        self._stylesheets_base_key = self._s3_utils.calc_key(stylesheets_base)
        self._stylesheet_url = f"{self._stylesheets_base_key}/xml-to-html-ISO.xsl"

    def _dump_xsl(self) -> None:
        """Copy XML stylesheets to directory if not already present."""
        self._dump_package_resources(src_ref=self._stylesheets_src_ref, dest_path=self._stylesheets_path)

    def _publish_xsl(self) -> None:
        """Upload stylesheets as S3 objects if they do not already exist."""
        self._s3_utils.upload_package_resources(src_ref=self._stylesheets_src_ref, base_key=self._stylesheets_base_key)

    def dumps(self) -> str:
        """
        Include ISO 19115 HTML XML stylesheet within XML encoded record.

        Uses the output of the `IsoXmlExporter` to generate encoded record.
        """
        # noinspection PyTypeChecker
        xml = IsoXmlExporter(
            config=self._config, s3_client=self._s3_client, record=self._record, export_base=self._export_path.parent
        ).dumps()
        doc = ElementTree(fromstring(xml.encode()))  # noqa: S320
        root = doc.getroot()
        root.addprevious(ProcessingInstruction("xml-stylesheet", f'type="text/xsl" href="{self._stylesheet_url}"'))
        return tostring(doc, pretty_print=True, xml_declaration=True, encoding="utf-8").decode()

    def export(self) -> None:
        """Write record and stylesheets to their respective directories."""
        super().export()
        self._dump_xsl()

    def publish(self) -> None:
        """
        Upload record and stylesheets to S3.

        `BaseExporter.publish()` not used for encoded record so we can override content type.
        """
        self._s3_utils.upload_content(
            key=self._s3_utils.calc_key(self._export_path), content_type="application/xml", body=self.dumps()
        )
        self._publish_xsl()
