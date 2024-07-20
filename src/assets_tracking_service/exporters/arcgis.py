import logging
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Self

from arcgis import GIS
from arcgis.features import FeatureLayerCollection
from arcgis.gis import Item

from assets_tracking_service.config import Config
from assets_tracking_service.db import DatabaseClient
from assets_tracking_service.exporters.base_exporter import Exporter
from assets_tracking_service.exporters.geojson import GeoJsonExporter


class ArcGISAuthenticationError(Exception):
    """Raised when ArcGIS authentication fails."""

    pass


class ArcGISExporter(Exporter):
    """
    Exports data as an ArcGIS Feature Service.

    Limited to a single collection of a summary information for assets and their latest position.
    """

    def __init__(self: Self, config: Config, db: DatabaseClient, logger: logging.Logger) -> None:
        self._output_path: TemporaryDirectory | None = None
        self._config = config
        self._logger = logger
        self._db = db

        try:
            self._arcgis = GIS(
                username=self._config.EXPORTER_ARCGIS_USERNAME, password=self._config.EXPORTER_ARCGIS_PASSWORD
            )
        except Exception as e:
            if "Invalid username or password" in str(e):
                raise ArcGISAuthenticationError() from e

        self._geojson = GeoJsonExporter(config, db, logger)

    def _get_data_with_name(self: Self, name: Path) -> Path:
        """
        Export GeoJSON data to a temporary file with a given name.

        Uses the GeoJSON exporter to get common data.

        To overwrite all data in a Feature Service using `arcgis` the replacement data MUST:
        - be written to a file that is the same type as the original (for this application, in GeoJSON format)
        - be in a file named the same as the original file (e.g. `foo.geojson`, not `foo-update.geojson`)
        """
        self._output_path = TemporaryDirectory()
        self._logger.debug("Temporary directory created at: %s", self._output_path.name)

        path = Path(self._output_path.name) / name
        self._logger.debug("Temporary file path: %s", path)

        self._geojson.export(path)
        return path

    def _overwrite_fs_data(self: Self) -> None:
        """
        Overwrite data in a ArcGIS Feature Service.

        This method replaces all data within a given feature service. Other Feature Service information, such as
        symbology, and Item details, such as description, are not changed or lost.

        THis method only works with Feature Services that have a single layer and originally made from an uploaded
        file (for this application, in GeoJSON format).

        Steps:
        - gets the Item for a Feature Service specified by its Item ID
        - queries related Items to find the Item it was created from (the origin data file)
        - exports data to a GeoJSON file, with the same name as the origin data file
        - overwrites data in the Feature Service with the new GeoJSON file
        """
        self._logger.debug("Looking for item ID: %s", self._config.EXPORTER_ARCGIS_ITEM_ID)
        item: Item = self._arcgis.content.get(self._config.EXPORTER_ARCGIS_ITEM_ID)
        self._logger.info("Item ID: %s, Title: %s", item.id, item.title)

        self._logger.debug("Looking for related items")
        results = item.related_items(rel_type="Service2Data", direction="forward")
        self._logger.debug("Related items results: %s", results)
        origin_item = results[0]
        self._logger.info(
            "Origin item ID: %s, Title: %s, Name: %s", origin_item.id, origin_item.title, origin_item.name
        )
        replacement_path = str(self._get_data_with_name(origin_item.name))
        self._logger.info("Replacement path: %s", replacement_path)

        self._logger.info("Overwriting item layer features...")
        collection = FeatureLayerCollection.fromitem(item)
        result = collection.manager.overwrite(str(replacement_path))
        self._logger.info("Overwrite result: %s", result)

    def export(self: Self) -> None:
        """
        Export data to an ArcGIS Feature Service.

        Part of exporter public interface.
        """
        self._overwrite_fs_data()

        self._logger.debug("Clearing temporary directory at: %s", self._output_path.name)
        self._output_path.cleanup()
        self._output_path = None
