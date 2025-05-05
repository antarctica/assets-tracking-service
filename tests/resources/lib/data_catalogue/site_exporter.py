import logging

from mypy_boto3_s3 import S3Client

from assets_tracking_service.config import Config
from assets_tracking_service.lib.bas_data_catalogue.exporters.records_exporter import RecordsExporter
from assets_tracking_service.lib.bas_data_catalogue.exporters.site_exporter import (
    SiteIndexExporter,
    SiteResourcesExporter,
)
from assets_tracking_service.lib.bas_data_catalogue.models.record import Record, RecordSummary


class SiteExporter:
    """
    Data Catalogue static site exporter.

    Combines exporters for records and static resources to create a standalone static website.
    """

    def __init__(
        self, config: Config, s3: S3Client, logger: logging.Logger, records: list[Record] | None = None
    ) -> None:
        """Initialise exporter."""
        self._config = config
        self._logger = logger
        self._s3 = s3

        self._records = records
        self._summaries = [RecordSummary.loads(record) for record in self._records]

        self._resources_exporter = SiteResourcesExporter(config=self._config, s3=self._s3)
        self._records_exporter = RecordsExporter(
            config=self._config, s3=self._s3, logger=self._logger, records=self._records, summaries=self._summaries
        )
        self._index_exporter = SiteIndexExporter(
            config=self._config, s3=self._s3, logger=self._logger, summaries=self._summaries
        )

    def export(self) -> None:
        """Export site contents to a directory."""
        self._resources_exporter.export()
        self._records_exporter.export_all()
        self._index_exporter.export()

    def publish(self) -> None:
        """Publish site contents to S3."""
        self._resources_exporter.publish()
        self._records_exporter.publish_all()
        self._index_exporter.publish()
