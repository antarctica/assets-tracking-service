from collections.abc import Callable
from pathlib import Path

from mypy_boto3_s3 import S3Client

from assets_tracking_service.config import Config
from assets_tracking_service.lib.bas_data_catalogue.exporters.base_exporter import Exporter
from assets_tracking_service.lib.bas_data_catalogue.models.item.catalogue import ItemCatalogue
from assets_tracking_service.lib.bas_data_catalogue.models.record import Record, RecordSummary


class HtmlExporter(Exporter):
    """
    Data Catalogue HTML item exporter.

    Exports a Record as ItemCatalogue HTML.

    Intended as the primary human-readable representation of a record.
    """

    def __init__(
        self,
        config: Config,
        s3_client: S3Client,
        record: Record,
        export_base: Path,
        get_record_summary: Callable[[str], RecordSummary],
    ) -> None:
        """
        Initialise.

        `get_record_summary` requires a callable to get a RecordSummary for a given identifier (used for related items).
        """
        export_base = export_base / record.file_identifier
        export_name = "index.html"
        super().__init__(
            config=config, s3_client=s3_client, record=record, export_base=export_base, export_name=export_name
        )
        self._get_summary = get_record_summary

    def dumps(self) -> str:
        """Encode record as data catalogue item in HTML."""
        return ItemCatalogue(
            record=self._record,
            embedded_maps_endpoint=self._config.EXPORTER_DATA_CATALOGUE_EMBEDDED_MAPS_ENDPOINT,
            item_contact_endpoint=self._config.EXPORTER_DATA_CATALOGUE_ITEM_CONTACT_ENDPOINT,
            sentry_dsn=self._config.SENTRY_DSN,
            get_record_summary=self._get_summary,
        ).render()


class HtmlAliasesExporter(Exporter):
    """
    HTML aliases exporter.

    Creates redirects back to Data Catalogue item pages for any aliases set within a Record.

    Uses S3 object redirects with a minimal HTML page as a fallback.
    """

    def __init__(self, config: Config, s3_client: S3Client, record: Record, site_base: Path) -> None:
        """
        Initialise.

        The `export_base` and `export_name` parameters required by the base Exporter aren't used by this class. The
        values used can be ignored.

        The `site_base` parameter MUST be the root of the overall site/catalogue output directory, so aliases under
        various prefixes can be generated.
        """
        export_name = f"{record.file_identifier}.html"
        export_base = site_base
        self._site_base = site_base
        super().__init__(
            config=config, s3_client=s3_client, record=record, export_base=export_base, export_name=export_name
        )

    def _get_aliases(self) -> list[str]:
        """Get optional aliases for record as relative file paths / S3 keys."""
        identifiers = self._record.identification.identifiers.filter(namespace="alias.data.bas.ac.uk")
        return [identifier.href.replace("https://data.bas.ac.uk/", "") for identifier in identifiers]

    def dumps(self) -> str:
        """Generate redirect page for record."""
        target = f"/items/{self._record.file_identifier}/"
        return f"""
<!DOCTYPE html>
<html lang="en-GB">
    <head><title>BAS Data Catalogue</title><meta http-equiv="refresh" content="0;url={target}" /></head>
    <body>Click <a href="{target}">here</a> if you are not redirected after a few seconds.</body>
</html>
        """

    def export(self) -> None:
        """Write redirect pages for each alias to export directory."""
        for alias in self._get_aliases():
            alias_path = self._site_base / alias / "index.html"
            self._dump(alias_path)

    def publish(self) -> None:
        """Write redirect pages with redirect headers to S3."""
        location = f"/items/{self._record.file_identifier}/index.html"
        for alias in self._get_aliases():
            self._put_object(key=f"{alias}/index.html", content_type="text/html", body=self.dumps(), redirect=location)
