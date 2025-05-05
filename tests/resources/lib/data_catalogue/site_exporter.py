import logging

from mypy_boto3_s3 import S3Client

from assets_tracking_service.config import Config
from assets_tracking_service.lib.bas_data_catalogue.exporters.records_exporter import RecordsExporter
from assets_tracking_service.lib.bas_data_catalogue.exporters.resources_exporter import SiteResourcesExporter
from assets_tracking_service.lib.bas_data_catalogue.models.record import Record
from tests.resources.lib.data_catalogue.records.item_cat_collection_all import record as collection_all_supported
from tests.resources.lib.data_catalogue.records.item_cat_data import record as data_all_supported
from tests.resources.lib.data_catalogue.records.item_cat_formatting import record as formatting_supported
from tests.resources.lib.data_catalogue.records.item_cat_licence import (
    cc_record,
    ogl_record,
    ops_record,
    rights_reversed_record,
)
from tests.resources.lib.data_catalogue.records.item_cat_product_all import record as product_all_supported
from tests.resources.lib.data_catalogue.records.item_cat_product_min import record as product_min_supported
from tests.resources.lib.data_catalogue.records.item_cat_pub_map import record as product_published_map


class SiteExporter:
    """Proto site exporter."""

    def __init__(
        self, config: Config, s3: S3Client, logger: logging.Logger, extra_records: list[Record] | None = None
    ) -> None:
        """Initialise exporter."""
        self._config = config
        self._logger = logger
        self._s3 = s3

        records = self._test_records
        if extra_records is not None:
            records.extend(extra_records)

        self._records = RecordsExporter(config=self._config, s3=self._s3, logger=self._logger, records=records)
        self._resources = SiteResourcesExporter(config=self._config, s3=self._s3)

    @property
    def _test_records(self) -> list[Record]:
        """Internal test records."""
        return [
            collection_all_supported,
            product_min_supported,
            product_all_supported,
            formatting_supported,
            data_all_supported,
            ogl_record,
            cc_record,
            ops_record,
            rights_reversed_record,
            product_published_map,
        ]

    def _build_index(self) -> str:
        """Build proto/backstage index."""
        # noinspection PyProtectedMember
        item_links = "\n".join(
            [
                f'<li><a href="/items/{summary.file_identifier}/index.html">[{summary.hierarchy_level.name}] {summary.file_identifier} - {summary.title} ({summary.edition})</a></li>'
                for summary in self._records._summaries.values()
            ]
        )
        return f"<html><body><h1>Items Index</h1><ul>{item_links}</ul></body></html>"

    def _export_index(self) -> None:
        """Export proto index to directory."""
        index_path = self._config.EXPORTER_DATA_CATALOGUE_OUTPUT_PATH / "-" / "index" / "index.html"
        self._logger.info(f"Exporting proto site index to {index_path}")
        index_path.parent.mkdir(parents=True, exist_ok=True)
        with index_path.open("w") as f:
            f.write(self._build_index())

    # noinspection PyProtectedMember
    def _publish_index(self) -> None:
        """Publish proto index to S3."""
        index_path = self._config.EXPORTER_DATA_CATALOGUE_OUTPUT_PATH / "-" / "index" / "index.html"
        index_key = self._resources._s3_utils.calc_key(index_path)
        index_url = f"https://{self._config.EXPORTER_DATA_CATALOGUE_AWS_S3_BUCKET}/{index_key}"
        self._logger.info(f"Publishing proto site index to: {index_url}")
        self._resources._s3_utils.upload_content(key=index_key, content_type="text/html", body=self._build_index())

    def export(self) -> None:
        """Export site contents to a directory."""
        self._resources.export()
        self._records.export_all()
        self._export_index()

    def publish(self) -> None:
        """Publish site contents to S3."""
        self._resources.publish()
        self._records.publish_all()
        self._publish_index()
