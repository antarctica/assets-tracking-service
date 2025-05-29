import logging
from datetime import UTC, date, datetime

from mypy_boto3_s3 import S3Client

from assets_tracking_service.config import Config
from assets_tracking_service.db import DatabaseClient
from assets_tracking_service.exporters.base_exporter import Exporter
from assets_tracking_service.lib.bas_data_catalogue.exporters.html_exporter import HtmlAliasesExporter, HtmlExporter
from assets_tracking_service.lib.bas_data_catalogue.exporters.iso_exporter import IsoXmlExporter, IsoXmlHtmlExporter
from assets_tracking_service.lib.bas_data_catalogue.exporters.json_exporter import JsonExporter
from assets_tracking_service.lib.bas_data_catalogue.models.record import Record
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.common import (
    Contacts,
    Date,
    Dates,
    Identifiers,
)
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.common import Identifier as CatIdentifier
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.data_quality import (
    DataQuality,
    Lineage,
)
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.identification import (
    Aggregations,
    Constraints,
    Extents,
    Identification,
    Maintenance,
)
from assets_tracking_service.lib.bas_data_catalogue.models.record.enums import (
    ContactRoleCode,
    HierarchyLevelCode,
    MaintenanceFrequencyCode,
    ProgressCode,
)
from assets_tracking_service.lib.bas_data_catalogue.models.record.presets.aggregations import (
    make_bas_cat_collection_member,
    make_in_bas_cat_collection,
)
from assets_tracking_service.lib.bas_data_catalogue.models.record.presets.base import RecordMagicDiscoveryV1
from assets_tracking_service.lib.bas_data_catalogue.models.record.presets.constraints import OGL_V3, OPEN_ACCESS
from assets_tracking_service.lib.bas_data_catalogue.models.record.presets.contacts import (
    make_magic_role as magic_contact,
)
from assets_tracking_service.lib.bas_data_catalogue.models.record.presets.distribution import make_esri_feature_layer
from assets_tracking_service.lib.bas_data_catalogue.models.record.presets.projections import EPSG_4326
from assets_tracking_service.lib.bas_data_catalogue.models.record.summary import RecordSummary
from assets_tracking_service.models.layer import LayersClient
from assets_tracking_service.models.record import RecordsClient


class CollectionRecord(RecordMagicDiscoveryV1):
    """
    Data Catalogue record for collection grouping layer records.

    Based on the MAGIC Discovery profile v1 record base which sets defaults for elements such as contacts and citation.
    """

    def __init__(self, config: Config, db: DatabaseClient, logger: logging.Logger) -> None:
        self._config = config
        self._logger = logger
        self._db = db
        self._records = RecordsClient(db)
        self._layers = LayersClient(db_client=db, logger=logger)

        self._slug = "ats_collection"
        self._alias = "assets-tracking-service"
        self._record = self._records.get_by_slug(self._slug)

        identification = Identification(
            title=self._record.title,
            dates=Dates(
                creation=Date(date=date(2025, 1, 25)),
                publication=Date(date=datetime(2025, 1, 27, 10, 3, 20, tzinfo=UTC)),
                released=Date(date=datetime(2025, 1, 27, 10, 3, 20, tzinfo=UTC)),
                revision=Date(date=self._layers.get_latest_data_refresh()),
            ),
            edition=self._record.edition,
            identifiers=Identifiers(
                [
                    CatIdentifier(
                        identifier=self._record.gitlab_issue,
                        href=self._record.gitlab_issue,
                        namespace="gitlab.data.bas.ac.uk",
                    ),
                    CatIdentifier(
                        identifier=self._alias,
                        href=f"https://data.bas.ac.uk/collections/{self._alias}",
                        namespace="alias.data.bas.ac.uk",
                    ),
                ]
            ),
            abstract=self._record.abstract,
            purpose=self._record.summary,
            contacts=Contacts([magic_contact(roles=[ContactRoleCode.AUTHOR, ContactRoleCode.PUBLISHER])]),
            constraints=Constraints([OPEN_ACCESS, OGL_V3]),
            extents=Extents([self._layers.get_bounding_extent()]),
            aggregations=Aggregations(
                [
                    make_bas_cat_collection_member(item_id=str(record_id))
                    for record_id in self._records.list_ids()
                    if record_id != self._record.id
                ]
            ),
            maintenance=Maintenance(
                progress=ProgressCode.ON_GOING,
                maintenance_frequency=MaintenanceFrequencyCode(self._record.update_frequency),
            ),
        )

        super().__init__(
            file_identifier=str(self._record.id),
            hierarchy_level=HierarchyLevelCode.COLLECTION,
            identification=identification,
        )
        self.set_citation()


class LayerRecord(RecordMagicDiscoveryV1):
    """
    Data Catalogue record for a layer.

    Based on the MAGIC Discovery profile v1 record base which sets defaults for elements such as contacts and citation.
    """

    def __init__(self, config: Config, db: DatabaseClient, logger: logging.Logger, layer_slug: str) -> None:
        self._config = config
        self._logger = logger
        self._db = db
        self._records = RecordsClient(db)
        self._layers = LayersClient(db_client=db, logger=logger)

        self._slug = layer_slug
        self._collection = self._records.get_by_slug("ats_collection")
        self._record = self._records.get_by_slug(self._slug)
        self._layer = self._layers.get_by_slug(self._slug)

        identification = Identification(
            title=self._record.title,
            dates=self._dates,
            edition=self._record.edition,
            identifiers=Identifiers(
                [
                    CatIdentifier(
                        identifier=self._record.gitlab_issue,
                        href=self._record.gitlab_issue,
                        namespace="gitlab.data.bas.ac.uk",
                    ),
                ]
            ),
            abstract=self._record.abstract,
            purpose=self._record.summary,
            contacts=Contacts([magic_contact(roles=[ContactRoleCode.AUTHOR, ContactRoleCode.PUBLISHER])]),
            constraints=Constraints([OPEN_ACCESS, OGL_V3]),
            extents=Extents([self._layers.get_extent_by_slug(self._slug)]),
            aggregations=Aggregations([make_in_bas_cat_collection(str(self._collection.id))]),
            maintenance=Maintenance(
                progress=ProgressCode.ON_GOING,
                maintenance_frequency=MaintenanceFrequencyCode(self._record.update_frequency),
            ),
        )

        distribution = make_esri_feature_layer(
            portal_endpoint=self._config.EXPORTER_ARCGIS_BASE_ENDPOINT_PORTAL,
            server_endpoint=self._config.EXPORTER_ARCGIS_BASE_ENDPOINT_SERVER,
            service_name=self._layer.slug,
            item_id=self._layer.agol_id_feature,
            item_ogc_id=self._layer.agol_id_feature_ogc,
        )

        super().__init__(
            file_identifier=str(self._record.id),
            hierarchy_level=HierarchyLevelCode.DATASET,
            reference_system_info=EPSG_4326,
            identification=identification,
            data_quality=DataQuality(lineage=Lineage(statement=self._record.lineage)),
            distribution=distribution,
        )
        self.set_citation()

    @property
    def _dates(self) -> Dates:
        """Record dates."""
        dates = Dates(
            creation=Date(date=self._layer.created_at),
            publication=Date(date=self._record.publication),
            released=Date(date=self._record.released),
        )
        if self._layer.data_last_refreshed:
            dates.revision = Date(date=self._layer.data_last_refreshed)
        return dates


class DataCatalogueExporter(Exporter):
    """Exports metadata records for the BAS Data Catalogue."""

    def __init__(self, config: Config, db: DatabaseClient, s3: S3Client, logger: logging.Logger) -> None:
        self._config = config
        self._logger = logger
        self._db = db
        self._s3 = s3
        self._layers = LayersClient(db_client=db, logger=logger)

    def _get_records(self) -> list[CollectionRecord | LayerRecord]:
        """Metadata records to export."""
        collection = CollectionRecord(self._config, self._db, self._logger)
        layers = [LayerRecord(self._config, self._db, self._logger, slug) for slug in self._layers.list_slugs()]
        return [collection, *layers]

    def _get_summarises(self) -> dict[str, RecordSummary]:
        """
        Summaries of metadata records for cross-referencing.

        Needed for building Data Catalogue items which may contain references to other items. Record summaries are used
        to avoid needing to use an index of full records, which would get unwieldy with a large number of records.
        """
        return {record.file_identifier: RecordSummary.loads(record) for record in self._get_records()}

    def _export_cat_json(self, record: Record) -> None:
        """Export record as BAS Metadata Library JSON."""
        self._logger.debug("Exporting record '%s' as BAS ISO JSON...", record.file_identifier)
        output_path = self._config.EXPORTER_DATA_CATALOGUE_OUTPUT_PATH / "records"
        exporter = JsonExporter(
            config=self._config, logger=self._logger, s3=self._s3, record=record, export_base=output_path
        )
        exporter.export()
        exporter.publish()
        self._logger.debug("Exported record '%s' as BAS ISO JSON", record.file_identifier)

    def _export_cat_html(self, record: Record, summaries: dict[str, RecordSummary]) -> None:
        """Export record as BAS Data Catalogue item HTML."""

        def _get_item_summary(identifier: str) -> RecordSummary:
            """
            Get title for a record identifier.

            This is a very basic implementation of what will in time be provided by a full record repository interface.
            It doesn't make sense to implement that within this project so this simple stand-in is used.
            """
            return summaries[identifier]

        self._logger.debug("Exporting record '%s' as BAS catalogue item...", record.file_identifier)
        output_path = self._config.EXPORTER_DATA_CATALOGUE_OUTPUT_PATH / "items"
        exporter = HtmlExporter(
            config=self._config,
            logger=self._logger,
            s3=self._s3,
            record=record,
            export_base=output_path,
            get_record_summary=_get_item_summary,
        )
        exporter.export()
        exporter.publish()
        self._logger.debug("Exported record '%s' as BAS catalogue item", record.file_identifier)

    def _export_aliases_html(self, record: Record) -> None:
        """Export aliases in record as redirects to catalogue items."""
        self._logger.debug("Exporting optional catalogue item aliases for record '%s' ...", record.file_identifier)
        output_path = self._config.EXPORTER_DATA_CATALOGUE_OUTPUT_PATH
        exporter = HtmlAliasesExporter(
            config=self._config, logger=self._logger, s3=self._s3, record=record, site_base=output_path
        )
        exporter.export()
        exporter.publish()
        self._logger.debug("Exported optional catalogue item aliases for record '%s'", record.file_identifier)

    def _export_iso_xml(self, record: Record) -> None:
        """Export record as ISO XML."""
        self._logger.debug("Exporting record '%s' as ISO XML...", record.file_identifier)
        output_path = self._config.EXPORTER_DATA_CATALOGUE_OUTPUT_PATH / "records"
        exporter = IsoXmlExporter(
            config=self._config, logger=self._logger, s3=self._s3, record=record, export_base=output_path
        )
        exporter.export()
        exporter.publish()
        self._logger.debug("Exported record '%s' as ISO XML", record.file_identifier)

    def _export_iso_xml_html(self, record: Record) -> None:
        """Export record as ISO XML with HTML stylesheet."""
        self._logger.debug("Exporting record '%s' as ISO XML with HTML stylesheet...", record.file_identifier)
        output_path = self._config.EXPORTER_DATA_CATALOGUE_OUTPUT_PATH / "records"
        exporter = IsoXmlHtmlExporter(
            config=self._config, logger=self._logger, s3=self._s3, record=record, export_base=output_path
        )
        exporter.export()
        exporter.publish()
        self._logger.debug("Exported record '%s' as ISO XML with HTML stylesheet", record.file_identifier)

    def export(self) -> None:
        """
        Export metadata records as a mini Data Catalogue static site.

        Records are exported in a variety of formats for Items and Records (HTML, JSON, XML). These outputs are saved
        as files to a local directory for reference and uploaded to the S3 bucket used for the ADD Metadata Toolbox
        / Data Catalogue, to avoid needing to publish records separately through the Toolbox project (which is too slow).
        """
        summaries = self._get_summarises()
        output_path = self._config.EXPORTER_DATA_CATALOGUE_OUTPUT_PATH
        bucket = self._config.EXPORTER_DATA_CATALOGUE_AWS_S3_BUCKET
        self._logger.info("Exporting records locally to '%s'", output_path.resolve())
        self._logger.info("Publishing records to S3 bucket '%s'", bucket)

        self._logger.debug("Ensuring local output path '%s' exists", output_path.resolve())
        output_path.mkdir(parents=True, exist_ok=True)

        for record in self._get_records():
            self._logger.info("Exporting record '%s'", record.file_identifier)

            self._logger.debug("Ensuring record '%s' is valid", record.file_identifier)
            record.validate()

            self._export_cat_json(record=record)
            self._export_cat_html(record=record, summaries=summaries)
            self._export_aliases_html(record=record)
            self._export_iso_xml(record=record)
            self._export_iso_xml_html(record=record)
