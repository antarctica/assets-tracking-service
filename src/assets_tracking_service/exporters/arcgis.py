import json
import logging
from datetime import UTC, datetime
from tempfile import TemporaryDirectory

from arcgis import GIS
from arcgis.gis import Group, ItemTypeEnum, SharingLevel
from arcgis.gis import Item as ArcGISItem
from geojson import FeatureCollection
from geojson import loads as geojson_loads
from importlib_resources import as_file as resources_as_file
from importlib_resources import files as resources_files
from psycopg.sql import SQL, Identifier

from assets_tracking_service.config import Config
from assets_tracking_service.db import DatabaseClient
from assets_tracking_service.exporters.base_exporter import Exporter
from assets_tracking_service.exporters.catalogue import LayerRecord
from assets_tracking_service.lib.bas_data_catalogue.models.item.base.enums import AccessType
from assets_tracking_service.lib.bas_esri_utils.client import ArcGisClient
from assets_tracking_service.lib.bas_esri_utils.models.item import Item as CatalogueItemArcGis
from assets_tracking_service.models.layer import Layer, LayersClient


class ArcGISAuthenticationError(Exception):
    """Raised when ArcGIS authentication fails."""

    pass


class ArcGisExporterLayer:
    """Represents an ArcGIS layer managed by this exporter."""

    def __init__(
        self,
        config: Config,
        db: DatabaseClient,
        logger: logging.Logger,
        arcgis: GIS,
        layers: LayersClient,
        layer_slug: str,
    ) -> None:
        self._config = config
        self._logger = logger
        self._db = db
        self._layers = layers
        self._arcgis = arcgis
        self._arcgis_client = ArcGisClient(arcgis=self._arcgis, logger=self._logger)

        self._slug = layer_slug
        self._layer = self._get_layer()
        self._logger.info("exporter class for layer '%s' created.", self._slug)

    @property
    def _catalogue_item_arc_geojson(self) -> CatalogueItemArcGis:
        """Data Catalogue ArcGIS item for resource as an ArcGIS GeoJSON file."""
        record = LayerRecord(config=self._config, db=self._db, logger=self._logger, layer_slug=self._slug)
        return CatalogueItemArcGis(
            record=record,
            arcgis_item_id=self._layer.agol_id_geojson,
            arcgis_item_name=self._slug,
            arcgis_item_type=ItemTypeEnum.GEOJSON,
            access_type=AccessType.NONE,
        )

    @property
    def _catalogue_item_arc_feature(self) -> CatalogueItemArcGis:
        """Data Catalogue ArcGIS item for resource as an ArcGIS feature layer."""
        record = LayerRecord(config=self._config, db=self._db, logger=self._logger, layer_slug=self._slug)
        return CatalogueItemArcGis(
            record=record,
            arcgis_item_id=self._layer.agol_id_feature,
            arcgis_item_name=self._slug,
            arcgis_item_type=ItemTypeEnum.FEATURE_SERVICE,
        )

    @property
    def _catalogue_item_arc_ogc_feature(self) -> CatalogueItemArcGis:
        """Data Catalogue ArcGIS item for resource as an ArcGIS OGC feature layer."""
        record = LayerRecord(config=self._config, db=self._db, logger=self._logger, layer_slug=self._slug)
        return CatalogueItemArcGis(
            record=record,
            arcgis_item_id=self._layer.agol_id_feature,
            arcgis_item_name=self._slug,
            arcgis_item_type=ItemTypeEnum.OGCFEATURESERVER,
        )

    def _get_layer(self) -> Layer:
        """Get model for layer."""
        return self._layers.get_by_slug(self._slug)

    def _get_data(self) -> FeatureCollection:
        """
        Fetch data for layer from specified source.

        The source view:
        - MUST contain a single row
        - MUST contain a single column named 'geojson'
        The 'geojson' column:
        - MUST contain a GeoJSON feature collection, which MAY be empty

        Views MUST be named in the form `{layer.source_view}_geojson`. (E.g. `v_foo_geojson` for a source view `v_foo`).
        """
        source_view = f"{self._layer.source_view}_geojson"

        # noinspection SqlResolve
        result = self._db.get_query_result(
            query=SQL("""SELECT geojson::text FROM {view};""").format(view=Identifier(source_view))
        )
        self._logger.debug("Raw fetched data: %s", result[0])

        # handle empty result
        if result[0][0] == '{"type" : "FeatureCollection", "features" : null}':
            self._logger.debug("Features list is empty, convert from `None` to `[]`.")
            result = (('{"type" : "FeatureCollection", "features" : []}',),)

        data = geojson_loads(result[0][0])
        self._logger.info("Fetched %s layer features from source view '%s'.", len(data["features"]), source_view)

        return data

    def _get_group(self) -> Group:
        """
        Get application ArcGIS group or create if missing.

        This group is used for all layers and so likely to already exist.
        """
        group_info = self._config.EXPORTER_ARCGIS_GROUP_INFO
        with resources_as_file(resources_files("assets_tracking_service.resources.arcgis_group")) as resources_path:
            thumbnail_path = resources_path / group_info["thumbnail_file"]

            description_path = resources_path / group_info["description_file"]
            with description_path.open() as f:
                description = f.read()

            return self._arcgis_client.create_group(
                title=group_info["name"],
                snippet=group_info["summary"],
                description=description,
                thumbnail_path=thumbnail_path,
                sharing_level=SharingLevel.EVERYONE,
            )

    def _get_portrayal(self) -> dict:
        """Get portrayal information (symbology, fields, popups) for layer from a resource file."""
        with resources_as_file(resources_files("assets_tracking_service.resources.arcgis_layers")) as resources_path:
            data_path = resources_path / f"{self._slug}" / "portrayal.json"
            with data_path.open() as f:
                return json.load(f)

    def _log_last_refreshed(self) -> None:
        data_ = self._layer.data_last_refreshed
        if isinstance(data_, datetime):
            data_ = data_.isoformat()
        metadata_ = self._layer.metadata_last_refreshed
        if isinstance(metadata_, datetime):
            metadata_ = metadata_.isoformat()
        self._logger.debug(f"Layer.data_last_refreshed now '{data_}'.")
        self._logger.debug(f"Layer.metadata_last_refreshed now '{metadata_}'.")

    def _set_refreshed_at(self, arc_item: ArcGISItem) -> None:
        """Update layer last_refreshed timestamps based on ArcGIS item."""
        self._logger.debug(f"Updating layer.data_last_refreshed based on arc item '{arc_item.id}'...")
        # noinspection PyProtectedMember
        if arc_item._has_layers():
            self._logger.debug(f"Updating layer.data_last_refreshed based on arc item '{arc_item.id}'...")
            dt = datetime.fromtimestamp(arc_item.layers[0].properties.editingInfo.dataLastEditDate / 1000, tz=UTC)
            self._layers.set_last_refreshed(self._slug, data_refreshed=dt)

        self._logger.debug(f"Updating layer.metadata_last_refreshed based on arc item '{arc_item.id}'...")
        t = datetime.fromtimestamp(arc_item.modified / 1000, tz=UTC)
        self._layers.set_last_refreshed(self._slug, metadata_refreshed=t)

        # re-fetch layer to reflect 'last_refreshed' property values
        self._layer = self._get_layer()
        self._log_last_refreshed()

    def setup(self) -> None:
        """
        Create ArcGIS items for layer and if needed, their containing folder and group.

        Feature layers require a data source which is currently a GeoJSON file populated from the source view.
        """
        group = self._get_group()

        if self._layer.agol_id_geojson is None:
            self._logger.info("Creating Arc GeoJSON item...")
            geojson_item = self._arcgis_client.create_item(
                folder_name=self._config.EXPORTER_ARCGIS_FOLDER_NAME,
                cat_item_arc=self._catalogue_item_arc_geojson,
                data=self._get_data(),
            )
            # GeoJSON item is an implementation detail of the feature layer and so not added to the group
            self._layers.set_item_id(self._slug, geojson_id=geojson_item.id)
            self._logger.info("Created Arc GeoJSON item [%s].", geojson_item.id)
            self._set_refreshed_at(geojson_item)

        if self._layer.agol_id_feature is None:
            self._logger.info("Publishing Arc feature layer item...")
            feature_item = self._arcgis_client.publish_item(
                self._catalogue_item_arc_geojson, self._catalogue_item_arc_feature
            )
            self._arcgis_client.add_item_to_group(item=feature_item, group=group)
            self._layers.set_item_id(self._slug, feature_id=feature_item.id)
            self._logger.info("Published Arc feature layer item [%s].", feature_item.id)
            self._set_refreshed_at(feature_item)

        if self._layer.agol_id_feature_ogc is None:
            self._logger.info("Publishing Arc OGC feature layer item...")
            ogc_feature_item = self._arcgis_client.publish_item(
                self._catalogue_item_arc_feature, self._catalogue_item_arc_ogc_feature
            )
            self._arcgis_client.add_item_to_group(item=ogc_feature_item, group=group)
            self._layers.set_item_id(self._slug, feature_ogc_id=ogc_feature_item.id)
            self._logger.info("Published Arc OGC feature layer item [%s].", ogc_feature_item.id)
            self._set_refreshed_at(ogc_feature_item)

    def update(self) -> None:
        """
        Refresh data in ArcGIS sources for layer.

        Steps:
        - refreshes the data in the backing GeoJSON item from the source view via the feature service
        - updates metadata for the GeoJSON, feature layer and OGC feature layer items
        - updates the `last_refreshed` timestamp for the app layer to record a successful update
        """
        _refresh_item = None

        if self._layer.agol_id_feature is not None:
            self._logger.debug("Overwriting features in Arc feature layer...")
            self._arcgis_client.overwrite_service_features(
                geojson_id=self._layer.agol_id_geojson, features_id=self._layer.agol_id_feature, data=self._get_data()
            )
            self._logger.debug("Features in Arc feature layer [%s] overwritten.", self._layer.agol_id_feature)

            self._logger.info("Updating metadata for source Arc GeoJSON item...")
            geojson_item = self._arcgis_client.update_item(self._catalogue_item_arc_geojson)
            self._logger.info("Arc geojson item [%s] details updated.", geojson_item.id)
            _refresh_item = geojson_item

            self._logger.info("Updating metadata for Arc feature layer item...")
            feature_item = self._arcgis_client.update_item(
                self._catalogue_item_arc_feature, item_portrayal=self._get_portrayal()
            )
            self._logger.info("Arc feature item [%s] details updated.", feature_item.id)
            _refresh_item = feature_item

        if self._layer.agol_id_feature_ogc is not None:
            self._logger.info("Updating metadata for Arc OGC feature layer item...")
            ogc_feature_item = self._arcgis_client.update_item(self._catalogue_item_arc_ogc_feature)
            self._logger.info("Arc OGC feature item [%s] details updated.", ogc_feature_item.id)
            _refresh_item = ogc_feature_item

        if _refresh_item is not None:
            self._set_refreshed_at(_refresh_item)


class ArcGisExporter(Exporter):
    """
    Exports data as an ArcGIS feature layer.

    Creates a hosted feature layer of all assets and their latest position.
    """

    def __init__(self, config: Config, db: DatabaseClient, logger: logging.Logger) -> None:
        self._output_path: TemporaryDirectory | None = None
        self._config = config
        self._logger = logger
        self._db = db

        self._layers = LayersClient(db_client=self._db, logger=self._logger)

        try:
            self._arcgis = GIS(
                username=self._config.EXPORTER_ARCGIS_USERNAME, password=self._config.EXPORTER_ARCGIS_PASSWORD
            )
        except Exception as e:
            if "Invalid username or password" in str(e):
                raise ArcGISAuthenticationError() from e

    def _get_layers(self) -> list[ArcGisExporterLayer]:
        """Layers to export."""
        layers = []

        self._logger.info("Creating exporter classes for each layer...")
        for slug in self._layers.list_slugs():
            layer = ArcGisExporterLayer(
                config=self._config,
                db=self._db,
                logger=self._logger,
                arcgis=self._arcgis,
                layers=self._layers,
                layer_slug=slug,
            )
            layers.append(layer)

        return layers

    def export(self) -> None:
        """
        Update each layers.

        Any missing items that form part of a layer are automatically created.

        Part of exporter public interface.
        """
        for layer in self._get_layers():
            layer.setup()
            layer.update()
