from shutil import copy

from importlib_resources import as_file as resources_as_file
from importlib_resources import files as resources_files
from mypy_boto3_s3 import S3Client

from assets_tracking_service.config import Config
from assets_tracking_service.lib.bas_data_catalogue.exporters.base_exporter import Exporter as BaseExporter
from assets_tracking_service.lib.bas_data_catalogue.exporters.base_exporter import S3Utils


class SiteResourcesExporter:
    """
    Static site resource exporters.

    A non-record specific exporter for static resources used across the static site (CSS, fonts, etc.).

    Due to global nature of this exporter it does subclass the BaseExporter to avoid hacking around its requirements.
    """

    def __init__(self, config: Config, s3: S3Client) -> None:
        self._s3_utils = S3Utils(
            s3=s3,
            s3_bucket=config.EXPORTER_DATA_CATALOGUE_AWS_S3_BUCKET,
            relative_base=config.EXPORTER_DATA_CATALOGUE_OUTPUT_PATH,
        )
        self._css_src_ref = "assets_tracking_service.lib.bas_data_catalogue.resources.css"
        self._fonts_src_ref = "assets_tracking_service.lib.bas_data_catalogue.resources.fonts"
        self._img_src_ref = "assets_tracking_service.lib.bas_data_catalogue.resources.img"
        self._txt_src_ref = "assets_tracking_service.lib.bas_data_catalogue.resources.txt"
        self._export_base = config.EXPORTER_DATA_CATALOGUE_OUTPUT_PATH.joinpath("static")

    def _dump_css(self) -> None:
        """
        Copy CSS to directory if not already present.

        The source CSS file needs generating from `main.css.j2` using the `scripts/recreate-css.py` script.
        Note: the source `main.css` contains an environment specific output path and MUST NOT be checked into git.
        """
        with resources_as_file(resources_files(self._css_src_ref)) as src_base:
            name = "main.css"
            src_path = src_base / name
            dst_path = self._export_base.joinpath("css", name)
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            copy(src_path, dst_path)

    def _dump_fonts(self) -> None:
        """Copy fonts to directory if not already present."""
        BaseExporter._dump_package_resources(src_ref=self._fonts_src_ref, dest_path=self._export_base.joinpath("fonts"))

    def _dump_favicon_ico(self) -> None:
        """
        Copy favicon.ico to conventional path if not already present.

        Fallback for `favicon.ico` where clients don't respect `<link rel="shortcut icon">` in HTML.
        """
        with resources_as_file(resources_files(self._img_src_ref)) as src_base:
            name = "favicon.ico"
            src_path = src_base / name
            dst_path = self._export_base.parent.joinpath(name)
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            copy(src_path, dst_path)

    def _dump_img(self) -> None:
        """Copy image files to directory if not already present."""
        BaseExporter._dump_package_resources(src_ref=self._img_src_ref, dest_path=self._export_base.joinpath("img"))

    def _dump_txt(self) -> None:
        """Copy text files to directory if not already present."""
        BaseExporter._dump_package_resources(src_ref=self._txt_src_ref, dest_path=self._export_base.joinpath("txt"))

    def _publish_css(self) -> None:
        """Upload CSS as an S3 object."""
        name = "main.css"
        with resources_as_file(resources_files(self._css_src_ref)) as src_base:
            src_path = src_base / name
            with src_path.open("r") as css_file:
                content = css_file.read()

        key = self._s3_utils.calc_key(self._export_base.joinpath("css", name))
        self._s3_utils.upload_content(key=key, content_type="text/css", body=content)

    def _publish_favicon_ico(self) -> None:
        """Upload favicon.ico as an S3 object."""
        name = "favicon.ico"
        with resources_as_file(resources_files(self._img_src_ref)) as src_base:
            src_path = src_base / name
            with src_path.open("rb") as favicon_file:
                content = favicon_file.read()

        key = self._s3_utils.calc_key(self._export_base.parent.joinpath(name))
        self._s3_utils.upload_content(key=key, content_type="image/x-icon", body=content)

    def _publish_fonts(self) -> None:
        """Upload fonts as S3 objects if they do not already exist."""
        self._s3_utils.upload_package_resources(
            src_ref=self._fonts_src_ref, base_key=self._s3_utils.calc_key(self._export_base.joinpath("fonts"))
        )

    def _publish_img(self) -> None:
        """Upload images as S3 objects if they do not already exist."""
        self._s3_utils.upload_package_resources(
            src_ref=self._img_src_ref, base_key=self._s3_utils.calc_key(self._export_base.joinpath("img"))
        )

    def _publish_txt(self) -> None:
        """Upload fonts as S3 objects if they do not already exist."""
        self._s3_utils.upload_package_resources(
            src_ref=self._txt_src_ref, base_key=self._s3_utils.calc_key(self._export_base.joinpath("txt"))
        )

    @property
    def name(self) -> str:
        """Exporter name."""
        return "Site Resources"

    def export(self) -> None:
        """Copy site resources to their respective directories."""
        self._dump_css()
        self._dump_fonts()
        self._dump_favicon_ico()
        self._dump_img()
        self._dump_txt()

    def publish(self) -> None:
        """Copy site resources to S3 bucket."""
        self._publish_css()
        self._publish_fonts()
        self._publish_favicon_ico()
        self._publish_img()
        self._publish_txt()
