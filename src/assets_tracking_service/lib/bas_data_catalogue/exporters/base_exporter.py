from mimetypes import guess_type
from pathlib import Path
from shutil import copytree

from importlib_resources import as_file as resources_as_file
from importlib_resources import files as resources_files
from mypy_boto3_s3 import S3Client

from assets_tracking_service.config import Config
from assets_tracking_service.lib.bas_data_catalogue.models.record import Record


class S3Utils:
    """Wrapper around Boto S3 client with high-level and/or convenience methods."""

    def __init__(self, s3: S3Client, s3_bucket: str, relative_base: Path) -> None:
        self._s3 = s3
        self._bucket = s3_bucket
        self._relative_base = relative_base

    def calc_key(self, path: Path) -> str:
        """
        Calculate `path` relative to `self._config.EXPORTER_DATA_CATALOGUE_OUTPUT_PATH`.

        E.g. `/data/site/html/123/index.html` gives `html/123/index.html` where OUTPUT_PATH is `/data/site/`.
        """
        return str(path.relative_to(self._relative_base))

    def upload_content(self, key: str, content_type: str, body: str | bytes, redirect: str | None = None) -> None:
        """
        Upload string or binary content as an S3 object.

        Optionally, a redirect can be set to redirect to another object as per [1].

        [1] https://docs.aws.amazon.com/AmazonS3/latest/userguide/how-to-page-redirect.html#redirect-requests-object-metadata
        """
        params = {"Bucket": self._bucket, "Key": key, "Body": body, "ContentType": content_type}
        if isinstance(body, str):
            params["Body"] = body.encode("utf-8")
        if redirect is not None:
            params["WebsiteRedirectLocation"] = redirect
        self._s3.put_object(**params)

    def upload_package_resources(self, src_ref: str, base_key: str) -> None:
        """
        Upload package resources as S3 objects if they do not already exist.

        `src_ref` MUST be a reference to a directory within a Python package compatible with `importlib_resources.files`.
        All files within this directory will be uploaded under a `base_key` if it does not already exist.
        """
        # abort if base_key already exists in bucket
        response = self._s3.list_objects_v2(Bucket=self._bucket, Prefix=base_key, MaxKeys=1)
        if "Contents" in response:
            return

        with resources_as_file(resources_files(src_ref)) as resources_path:
            for path in resources_path.glob("*"):
                self._s3.upload_file(Filename=path, Bucket=self._bucket, Key=base_key + "/" + path.name)


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

    def __init__(self, config: Config, s3: S3Client, record: Record, export_base: Path, export_name: str) -> None:
        """
        Initialise exporter.

        Where `export_base` is an output directory for each export type which MUST be relative to
        `Config.EXPORTER_DATA_CATALOGUE_OUTPUT_PATH`, so that a base S3 key can be generated from it.
        """
        self._config = config
        self._s3_client = s3
        self._s3_utils = S3Utils(
            s3=self._s3_client,
            s3_bucket=self._config.EXPORTER_DATA_CATALOGUE_AWS_S3_BUCKET,
            relative_base=self._config.EXPORTER_DATA_CATALOGUE_OUTPUT_PATH,
        )

        self._validate(record, export_base)
        self._record = record
        self._export_path = export_base.joinpath(export_name)

    def _validate(self, record: Record, export_base: Path) -> None:
        """Validate exporter configuration."""
        if record.file_identifier is None:
            msg = "File identifier must be set to export record."
            raise ValueError(msg) from None

        try:
            _ = export_base.relative_to(self._config.EXPORTER_DATA_CATALOGUE_OUTPUT_PATH)
        except ValueError as e:
            msg = "Export base must be relative to EXPORTER_DATA_CATALOGUE_OUTPUT_PATH."
            raise ValueError(msg) from e

    def _dump(self, path: Path) -> None:
        """Write dumped output to file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w") as record_file:
            record_file.write(self.dumps())

    @staticmethod
    def _dump_package_resources(src_ref: str, dest_path: Path) -> None:
        """
        Copy package resources to directory.

        `src_ref` MUST be a reference to a directory within a Python package compatible with `importlib_resources.files`.
        All files within this directory will be copied to `dest_path`, any matching existing files will be overwritten.
        """
        if dest_path.exists():
            return

        with resources_as_file(resources_files(src_ref)) as resources_path:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            copytree(resources_path, dest_path)

    @property
    def name(self) -> str:
        """Exporter name."""
        raise NotImplementedError() from None

    def dumps(self) -> str:
        """Encode resource as a particular format."""
        raise NotImplementedError() from None

    def export(self) -> None:
        """Save dumped output to local export directory."""
        self._dump(self._export_path)

    def publish(self) -> None:
        """Save dumped output to remote S3 bucket."""
        media_type = guess_type(self._export_path.name)[0] or "application/octet-stream"
        key = self._s3_utils.calc_key(self._export_path)
        self._s3_utils.upload_content(key=key, content_type=media_type, body=self.dumps())
