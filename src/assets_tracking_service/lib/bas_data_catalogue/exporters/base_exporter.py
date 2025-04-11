from mimetypes import guess_type
from pathlib import Path

from mypy_boto3_s3 import S3Client

from assets_tracking_service.config import Config
from assets_tracking_service.lib.bas_data_catalogue.models.record import Record


class Exporter:
    """
    Base class for exporters.

    Defines a required interface all exporters must implement to allow operations to be performed across a set of
    exporters without knowledge of how each works.

    Exporters:
    - produce representations of a Record in a particular format, encoding or other form as string output
    - persist this output as files, stored on a local file system and remote object store (AWS S3)
    - require records to set Record.file_identifier
    """

    def __init__(
        self, config: Config, s3_client: S3Client, record: Record, export_base: Path, export_name: str
    ) -> None:
        """
        Initialise exporter.

        `export_base` is an output directory for each export type. This MUST be relative to
        `Config.EXPORTER_DATA_CATALOGUE_OUTPUT_PATH` so that a base S3 key can be generated from it.
        """
        if record.file_identifier is None:
            msg = "File identifier must be set to export record."
            raise ValueError(msg) from None

        try:
            _ = export_base.relative_to(config.EXPORTER_DATA_CATALOGUE_OUTPUT_PATH)
        except ValueError as e:
            msg = "Export base must be relative to EXPORTER_DATA_CATALOGUE_OUTPUT_PATH."
            raise ValueError(msg) from e

        self._config = config
        self._s3_client = s3_client
        self._record = record
        self._export_path = export_base.joinpath(export_name)

    def _dump(self, path: Path) -> None:
        """Write dumped output to file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w") as record_file:
            record_file.write(self.dumps())

    def _put_object(self, key: str, content_type: str, body: str, redirect: str | None = None) -> None:
        """
        Upload dumped output to S3 object.

        Optionally, a redirect can be set to redirect to another object as per [1].

        [1] https://docs.aws.amazon.com/AmazonS3/latest/userguide/how-to-page-redirect.html#redirect-requests-object-metadata
        """
        params = {
            "Bucket": self._config.EXPORTER_DATA_CATALOGUE_AWS_S3_BUCKET,
            "Key": key,
            "Body": body.encode("utf-8"),
            "ContentType": content_type,
        }
        if redirect is not None:
            params["WebsiteRedirectLocation"] = redirect
        self._s3_client.put_object(**params)

    def _calc_s3_key(self, path: Path) -> str:
        """
        Calculate `path` relative to `self._config.EXPORTER_DATA_CATALOGUE_OUTPUT_PATH`.

        E.g. `/data/site/html/123/index.html` gives `html/123/index.html` where OUTPUT_PATH is `/data/site/`.
        """
        return str(path.relative_to(self._config.EXPORTER_DATA_CATALOGUE_OUTPUT_PATH))

    def dumps(self) -> str:
        """Encode resource as a particular format."""
        raise NotImplementedError() from None

    def export(self) -> None:
        """Save dumped output to local export directory."""
        self._dump(self._export_path)

    def publish(self) -> None:
        """Save dumped output to remote S3 bucket."""
        media_type = guess_type(self._export_path.name)[0] or "application/octet-stream"
        key = self._calc_s3_key(self._export_path)
        self._put_object(key=key, content_type=media_type, body=self.dumps())
