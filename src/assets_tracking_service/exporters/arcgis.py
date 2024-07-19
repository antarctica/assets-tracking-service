import logging
from pathlib import Path
from tempfile import TemporaryDirectory

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
    def __init__(self, config: Config, db: DatabaseClient, logger: logging.Logger):
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

    def _get_data_with_name(self, name: Path) -> Path:
        self._output_path = TemporaryDirectory()
        self._logger.debug("Temporary directory created at: %s", self._output_path.name)

        path = Path(self._output_path.name) / name
        self._logger.debug("Temporary file path: %s", path)

        self._geojson.export(path)
        return path

    def _overwrite_fs_data(self):
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

        self._logger.debug("Overwriting item layer features...")
        collection = FeatureLayerCollection.fromitem(item)
        result = collection.manager.overwrite(str(replacement_path))
        self._logger.info("Overwrite result: %s", result)

    def export(self):
        self._overwrite_fs_data()

        self._logger.debug("Clearing temporary directory at: %s", self._output_path.name)
        self._output_path.cleanup()
        self._output_path = None
