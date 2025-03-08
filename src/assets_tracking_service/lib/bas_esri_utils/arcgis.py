import logging
from pathlib import Path
from tempfile import TemporaryDirectory

from arcgis import GIS
from arcgis.features import FeatureLayerCollection
from arcgis.gis import Item, ItemTypeEnum
from geojson import FeatureCollection
from geojson import dump as geojson_dump

from assets_tracking_service.lib.bas_esri_utils.models.item import Item as CatalogueItemArcGis


class ArcGISInternalServerError(Exception):
    """Raised when an internal server error occurs within an ArcGIS service."""

    pass


class ArcGisItemNotSpecifiedError(Exception):
    """Raised when an ArcGIS item is not specified but is required."""

    pass


class ArcGisItemNotFoundError(Exception):
    """Raised when an ArcGIS item cannot be found."""

    pass


class ArcGisClient:
    def __init__(self, arcgis: GIS, logger: logging.Logger | None = None) -> None:
        self._logger = logger
        self._client = arcgis

    def _dump_metadata(self, base_path: Path, cat_item_arc: CatalogueItemArcGis) -> Path:
        self._logger.info("Writing out ArcGIS metadata...")
        metadata_path = base_path / "metadata.xml"
        self._logger.debug("Writing ArcGIS metadata to: ", metadata_path.resolve())
        self._logger.debug("ArcGIS metadata:")
        self._logger.debug(cat_item_arc.metadata)
        metadata_path.write_text(cat_item_arc.metadata)
        return metadata_path

    def _dump_data(self, base_path: Path, data: FeatureCollection, file_name: str) -> Path:
        data_path = base_path / file_name
        self._logger.debug("Writing item source data to: ", data_path.resolve())
        self._logger.debug("Data:")
        self._logger.debug(data)
        with data_path.open(mode="w") as f:
            geojson_dump(data, f)
        return data_path

    def get_item(self, item_id: str) -> Item:
        """Get ArcGIS item."""
        item = self._client.content.get(item_id)

        if item is None:
            msg = f"Item [{item_id}] not found"
            raise ArcGisItemNotFoundError(msg)

        self._logger.info("Item [%s] '%s'", item.id, item.title)
        return item

    def create_item(self, cat_item_arc: CatalogueItemArcGis, data: FeatureCollection) -> Item:
        """Create ArcGIS item."""
        self._logger.info("Creating ArcGIS item '%s' ...", cat_item_arc.title_plain)

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            metadata_path = self._dump_metadata(temp_path, cat_item_arc)
            data_path = self._dump_data(temp_path, data, "features.geojson")

            root_folder = self._client.content.folders.get()
            self._logger.info("Adding item to root folder '%s' ...", root_folder)
            self._logger.debug("Item properties:")
            self._logger.debug(cat_item_arc.item_properties)
            result = root_folder.add(item_properties=cat_item_arc.item_properties, file=str(data_path))
            new_item = result.result()
            self._logger.info("New item created [%s] '%s'", new_item.id, new_item.title)

            self._logger.debug("Setting item sharing level to: '%s' ...", cat_item_arc.sharing_level)
            new_item.sharing.sharing_level = cat_item_arc.sharing_level
            # `Folder.add` method doesn't support setting ArcGIS item metadata and thumbnail so update these separately
            self._logger.debug("Setting item thumbnail to: '%s' ...", cat_item_arc.thumbnail_href)
            new_item.update(
                thumbnail=cat_item_arc.thumbnail_href,
                metadata=str(metadata_path),
            )

            return new_item

    def publish_item(self, src_cat_item: CatalogueItemArcGis, dest_cat_item: CatalogueItemArcGis) -> Item:
        """Publish ArcGIS item as a service."""
        self._logger.debug("Publishing ArcGIS item '%s' as a %s ...", src_cat_item.item_id, dest_cat_item.item_type)

        if src_cat_item.item_id is None:
            raise ArcGisItemNotSpecifiedError() from None

        # restrict item types
        # error if src and dest items are the same

        params = {"publish_parameters": {"name": dest_cat_item.item_name}}
        if src_cat_item.item_type == ItemTypeEnum.FEATURE_SERVICE:
            params["file_type"] = "featureService"
        if dest_cat_item.item_type == ItemTypeEnum.OGCFEATURESERVER:
            params["output_type"] = "OGCFeatureService"
        self._logger.debug("Publishing parameters:")
        self._logger.debug(params)

        src_item = self.get_item(src_cat_item.item_id)
        new_item = src_item.publish(**params)
        # Set metadata link for new item
        with TemporaryDirectory() as temp_dir:
            metadata_path = self._dump_metadata(Path(temp_dir), dest_cat_item)
            new_item.update(metadata=str(metadata_path))

        self._logger.debug("Item [%s] published as a %s [%s]", src_item.id, dest_cat_item.item_type, new_item.id)
        # Apply metadata to new item
        self.update_item(dest_cat_item, new_item.id)
        return new_item

    def update_item(self, cat_item_arc: CatalogueItemArcGis, item_id: str | None = None) -> Item:
        """Update ArcGIS item details."""
        item_id = item_id or cat_item_arc.item_id
        self._logger.debug("Updating ArcGIS item '%s'...", item_id)

        item = self.get_item(item_id)
        item.update(
            item_properties=cat_item_arc.item_properties,
            thumbnail=cat_item_arc.thumbnail_href,
        )
        item.sharing.sharing_level = cat_item_arc.sharing_level
        return self.get_item(item_id)

    def overwrite_service_features(self, features_id: str, geojson_id: str, data: FeatureCollection) -> None:
        """Overwrite features in an ArcGIS feature layer."""
        self._logger.info("Overwriting features in ArcGIS item '%s' via source item '%s'...", features_id, geojson_id)
        feature_item = self.get_item(features_id)
        collection = FeatureLayerCollection.fromitem(feature_item)

        geojson_item = self.get_item(geojson_id)
        with TemporaryDirectory() as temp_dir:
            self._logger.debug("Writing out layer data to temporary file for upload...")
            data_path = self._dump_data(Path(temp_dir), data, geojson_item.name)

            try:
                result = collection.manager.overwrite(str(data_path))
                self._logger.debug("Overwrite result: %s", result)
            except Exception as e:
                if "Internal Server Error" in str(e):
                    self._logger.exception("Overwrite failed", exc_info=e)
                    raise ArcGISInternalServerError() from e

                self._logger.exception("Overwrite failed", exc_info=e)
                raise e from e
