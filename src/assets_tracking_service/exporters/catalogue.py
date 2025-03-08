import logging
from datetime import UTC, date, datetime
from json import dump as json_dump
from pathlib import Path

from assets_tracking_service.config import Config
from assets_tracking_service.db import DatabaseClient
from assets_tracking_service.exporters.base_exporter import Exporter
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.common import Date, Dates
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.common import Identifier as CatIdentifier
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.data_quality import (
    DataQuality,
    Lineage,
)
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.identification import (
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
            identifiers=[
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
            ],
            abstract=self._record.abstract,
            purpose=self._record.summary,
            contacts=[magic_contact(roles=[ContactRoleCode.AUTHOR, ContactRoleCode.PUBLISHER])],
            constraints=[OPEN_ACCESS, OGL_V3],
            extents=[self._layers.get_bounding_extent()],
            aggregations=[
                make_bas_cat_collection_member(item_id=str(record_id)) for record_id in self._records.list_ids()
            ],
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

    @property
    def output_path(self) -> Path:
        """Record output path."""
        return self._config.EXPORTER_DATA_CATALOGUE_OUTPUT_PATH.joinpath("collection.json").resolve()


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
        self._record = self._records.get_by_slug(self._slug)
        self._layer = self._layers.get_by_slug(self._slug)

        identification = Identification(
            title=self._record.title,
            dates=self._dates,
            edition=self._record.edition,
            identifiers=[
                CatIdentifier(
                    identifier=self._record.gitlab_issue,
                    href=self._record.gitlab_issue,
                    namespace="gitlab.data.bas.ac.uk",
                ),
            ],
            abstract=self._record.abstract,
            purpose=self._record.summary,
            contacts=[magic_contact(roles=[ContactRoleCode.AUTHOR, ContactRoleCode.PUBLISHER])],
            constraints=[OPEN_ACCESS, OGL_V3],
            extents=[self._layers.get_extent_by_slug(self._slug)],
            aggregations=[make_in_bas_cat_collection(self._config.EXPORTER_DATA_CATALOGUE_COLLECTION_RECORD_ID)],
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

    @property
    def output_path(self) -> Path:
        """Record output path."""
        return self._config.EXPORTER_DATA_CATALOGUE_OUTPUT_PATH.joinpath(f"{self._slug}.json").resolve()


class DataCatalogueExporter(Exporter):
    """Exports metadata records for the BAS Data Catalogue."""

    def __init__(self, config: Config, db: DatabaseClient, logger: logging.Logger) -> None:
        self._config = config
        self._logger = logger
        self._db = db
        self._layers = LayersClient(db_client=db, logger=logger)

    def _get_records(self) -> list[LayerRecord]:
        """Metadata records to export."""
        collection = CollectionRecord(self._config, self._db, self._logger)
        layers = [LayerRecord(self._config, self._db, self._logger, slug) for slug in self._layers.list_slugs()]
        return [collection, *layers]

    def export(self) -> None:
        """
        Export metadata records as JSON files to the configured output directory.

        Any missing parent directories to this output path will be created.
        """
        for exporter_record in self._get_records():
            self._logger.debug("Ensuring record '%s' is valid", exporter_record.file_identifier)
            exporter_record.validate()

            self._logger.debug("Ensuring parent path '%s' exists", exporter_record.output_path.parent.resolve())
            exporter_record.output_path.parent.mkdir(parents=True, exist_ok=True)

            self._logger.info("Writing metadata record to '%s'", exporter_record.output_path.resolve())
            with exporter_record.output_path.open("w") as f:
                # noinspection PyTypeChecker
                json_dump(exporter_record.dumps(), f, indent=2, sort_keys=False)
