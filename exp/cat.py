import logging

from boto3 import client as S3Client  # noqa: N812
from tests.resources.lib.data_catalogue.records.item_cat_collection_all import record as collection_all_supported
from tests.resources.lib.data_catalogue.records.item_cat_formatting import record as formatting_supported
from tests.resources.lib.data_catalogue.records.item_cat_product_all import record as product_all_supported

from assets_tracking_service.config import Config
from assets_tracking_service.db import DatabaseClient, make_conn
from assets_tracking_service.exporters.catalogue import DataCatalogueExporter
from assets_tracking_service.lib.bas_data_catalogue.exporters.site_exporter import SiteResourcesExporter
from assets_tracking_service.lib.bas_data_catalogue.models.item.catalogue import ItemCatalogue
from assets_tracking_service.lib.bas_data_catalogue.models.record import Record, RecordSummary


def build_test_records(config: Config, logger: logging.Logger) -> None:
    """Build test records."""
    records: list[Record] = [collection_all_supported, product_all_supported, formatting_supported]
    # noinspection PyTypeChecker
    summaries: list[RecordSummary] = {record.file_identifier: RecordSummary.loads(record) for record in records}

    def _get_item_summary(identifier: str) -> RecordSummary:
        """
        Get title for a record identifier.

        This is a very basic implementation of what will in time be provided by a full record repository interface.
        It doesn't make sense to implement that within this project so this simple stand-in is used.
        """
        # noinspection PyTypeChecker
        return summaries[identifier]

    for record in records:
        path = config.EXPORTER_DATA_CATALOGUE_OUTPUT_PATH / "items" / f"{record.file_identifier}.html"
        path.parent.mkdir(parents=True, exist_ok=True)

        item = ItemCatalogue(
            record=record,
            embedded_maps_endpoint=config.EXPORTER_DATA_CATALOGUE_EMBEDDED_MAPS_ENDPOINT,
            item_contact_endpoint=config.EXPORTER_DATA_CATALOGUE_ITEM_CONTACT_ENDPOINT,
            get_record_summary=_get_item_summary,
        )

        with path.open("w") as f:
            f.write(item.render())
            logger.info(f"Exported test record '{record.file_identifier}'")


def build_assets_records(config: Config, s3: S3Client, logger: logging.Logger) -> None:
    """Build assets records."""
    db = DatabaseClient(conn=make_conn(config.DB_DSN))
    exporter = DataCatalogueExporter(config=config, db=db, s3=s3, logger=logger)
    exporter.export()  # will also publish to S3


def build_static_resources(config: Config, s3: S3Client, logger: logging.Logger) -> None:
    """Build shared static resources."""
    exporter = SiteResourcesExporter(config=config, s3_client=s3)
    exporter.export()
    exporter.publish()
    logger.info("Exported static resources")


def main() -> None:
    """Entrypoint."""
    config = Config()
    logger = logging.getLogger("app")
    s3 = S3Client(
        "s3",
        aws_access_key_id=config.EXPORTER_DATA_CATALOGUE_AWS_ACCESS_ID,
        aws_secret_access_key=config.EXPORTER_DATA_CATALOGUE_AWS_ACCESS_SECRET,
        region_name="eu-west-1",
    )

    build_test_records(config=config, logger=logger)
    build_assets_records(config=config, s3=s3, logger=logger)
    build_static_resources(config=config, s3=s3, logger=logger)


if __name__ == "__main__":
    main()
