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

    def __init__(self, config: Config, s3: S3Client, record: Record, export_base: Path) -> None:
        export_name = f"{record.file_identifier}.xml"
        super().__init__(config=config, s3=s3, record=record, export_base=export_base, export_name=export_name)

    @property
    def name(self) -> str:
        """Exporter name."""
        return "ISO XML"

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

    As browsers do not support loading XML stylesheets across origins, a local copy is created by the
    `SiteResourcesExporter()` exporter. This exporter adds this location to the record within each record.

    This exporter intentionally uses a `.html` file extension despite being an `application/xml` media type so that
    both the styled (.html) and un-styled (.xml) files can be named after the record identifier in the same location.
    I.e. `/some/path/123.html` and `/some/path/123.xml`.

    [1] https://metadata-standards.data.bas.ac.uk/standards/iso-19115-19139#iso-html
    """

    def __init__(
        self,
        config: Config,
        s3: S3Client,
        record: Record,
        export_base: Path,
    ) -> None:
        """Initialise exporter."""
        export_name = f"{record.file_identifier}.html"
        super().__init__(config=config, s3=s3, record=record, export_base=export_base, export_name=export_name)
        self._stylesheet_url = "static/xsl/iso-html/xml-to-html-ISO.xsl"

    @property
    def name(self) -> str:
        """Exporter name."""
        return "ISO XML HTML"

    def dumps(self) -> str:
        """
        Include ISO 19115 HTML XML stylesheet within XML encoded record.

        Uses the output of the `IsoXmlExporter` to generate encoded record.
        """
        # noinspection PyTypeChecker
        xml = IsoXmlExporter(
            config=self._config, s3=self._s3_client, record=self._record, export_base=self._export_path.parent
        ).dumps()
        doc = ElementTree(fromstring(xml.encode()))  # noqa: S320
        root = doc.getroot()
        root.addprevious(ProcessingInstruction("xml-stylesheet", f'type="text/xsl" href="{self._stylesheet_url}"'))
        return tostring(doc, pretty_print=True, xml_declaration=True, encoding="utf-8").decode()
