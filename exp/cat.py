import logging

from boto3 import client as S3Client  # noqa: N812

from assets_tracking_service.config import Config
from assets_tracking_service.db import DatabaseClient, make_conn
from assets_tracking_service.exporters.catalogue import DataCatalogueExporter


def main() -> None:
    """Entrypoint."""
    logger = logging.getLogger("app")
    config = Config()
    db = DatabaseClient(conn=make_conn(config.DB_DSN))
    s3 = S3Client(
        "s3",
        aws_access_key_id=config.EXPORTER_DATA_CATALOGUE_AWS_ACCESS_ID,
        aws_secret_access_key=config.EXPORTER_DATA_CATALOGUE_AWS_ACCESS_SECRET,
        region_name="eu-west-1",
    )
    exporter = DataCatalogueExporter(config=config, db=db, s3=s3, logger=logger)
    exporter.export()


if __name__ == "__main__":
    main()
