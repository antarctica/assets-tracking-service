import logging

from mypy_boto3_s3 import S3Client

from assets_tracking_service.config import Config
from assets_tracking_service.lib.bas_data_catalogue.exporters.base_exporter import Exporter
from assets_tracking_service.lib.bas_data_catalogue.exporters.html_exporter import HtmlAliasesExporter, HtmlExporter
from assets_tracking_service.lib.bas_data_catalogue.exporters.iso_exporter import IsoXmlExporter, IsoXmlHtmlExporter
from assets_tracking_service.lib.bas_data_catalogue.exporters.json_exporter import JsonExporter
from assets_tracking_service.lib.bas_data_catalogue.models.record import Record
from assets_tracking_service.lib.bas_data_catalogue.models.record.summary import RecordSummary


class RecordsExporter:
    """
    Data Catalogue records exporter.

    Combines format specific exporters for a set of records.

    Records and summaries handling is intentionally simple and not intended for large numbers of records.
    It will be replaced with a more capable record repository in the future.
    """

    def __init__(
        self,
        config: Config,
        s3: S3Client,
        logger: logging.Logger,
        records: list[Record],
        summaries: list[RecordSummary],
    ) -> None:
        """Initialise exporter."""
        self._config = config
        self._s3 = s3
        self._logger = logger

        self._records: dict[str, Record] = {}
        self._summaries: dict[str, RecordSummary] = {}

        self._logger.info(f"Initialising records exporter from {len(records)} records")
        self._index_records(records)
        self._index_summaries(summaries)

    def _index_records(self, records: list[Record]) -> None:
        """Index all records and create record summaries."""
        self._records = {record.file_identifier: record for record in records}
        self._logger.debug(f"{len(self._records)} records indexed")

    def _index_summaries(self, summaries: list[RecordSummary]) -> None:
        """Create record summaries for all records."""
        self._summaries = {summary.file_identifier: summary for summary in summaries}
        self._logger.debug(f"{len(self._summaries)} record summaries indexed")

    def _get_item_summary(self, identifier: str) -> RecordSummary:
        """
        Get title for a record identifier.

        Crude implementation a record repository interface.
        """
        return self._summaries[identifier]

    def _get_html_exporter(self, record: Record) -> HtmlExporter:
        """Record as item HTML."""
        output_path = self._config.EXPORTER_DATA_CATALOGUE_OUTPUT_PATH / "items"
        return HtmlExporter(
            config=self._config,
            s3=self._s3,
            record=record,
            export_base=output_path,
            get_record_summary=self._get_item_summary,
        )

    def _get_html_aliases_exporter(self, record: Record) -> HtmlAliasesExporter:
        """Record aliases as redirects to item HTML."""
        output_path = self._config.EXPORTER_DATA_CATALOGUE_OUTPUT_PATH
        return HtmlAliasesExporter(config=self._config, s3=self._s3, record=record, site_base=output_path)

    def _get_json_exporter(self, record: Record) -> JsonExporter:
        """Record as BAS Metadata Library JSON."""
        output_path = self._config.EXPORTER_DATA_CATALOGUE_OUTPUT_PATH / "records"
        return JsonExporter(config=self._config, s3=self._s3, record=record, export_base=output_path)

    def _get_iso_xml_exporter(self, record: Record) -> IsoXmlExporter:
        """Record as ISO XML."""
        output_path = self._config.EXPORTER_DATA_CATALOGUE_OUTPUT_PATH / "records"
        return IsoXmlExporter(config=self._config, s3=self._s3, record=record, export_base=output_path)

    def _get_iso_xml_html_exporter(self, record: Record) -> IsoXmlHtmlExporter:
        """Record as ISO XML with HTML stylesheet."""
        output_path = self._config.EXPORTER_DATA_CATALOGUE_OUTPUT_PATH / "records"
        return IsoXmlHtmlExporter(config=self._config, s3=self._s3, record=record, export_base=output_path)

    def _get_exporters(self, record: Record) -> list[Exporter]:
        """Get exporters for record."""
        return [
            self._get_html_exporter(record),
            self._get_html_aliases_exporter(record),
            self._get_json_exporter(record),
            self._get_iso_xml_exporter(record),
            self._get_iso_xml_html_exporter(record),
        ]

    @property
    def name(self) -> str:
        """Exporter name."""
        return "Records"

    def export_record(self, file_identifier: str) -> None:
        """Export a record to a directory."""
        self._logger.info(f"Exporting record '{file_identifier}'")
        record = self._records[file_identifier]
        for exporter in self._get_exporters(record):
            self._logger.debug(f"Exporting record '{file_identifier}' using {exporter.name} exporter")
            exporter.export()

    def publish_record(self, file_identifier: str) -> None:
        """Publish a records to S3."""
        self._logger.info(f"Publishing record '{file_identifier}'")
        record = self._records[file_identifier]
        for exporter in self._get_exporters(record):
            self._logger.debug(f"Publishing record '{file_identifier}' using {exporter.name} exporter")
            exporter.publish()

    def export(self) -> None:
        """Export all records to a directory."""
        for file_identifier in self._records:
            self.export_record(file_identifier)

    def publish(self) -> None:
        """Publish all records to S3."""
        for file_identifier in self._records:
            self.publish_record(file_identifier)
