import logging

from assets_tracking_service.config import Config
from assets_tracking_service.db import DatabaseClient
from assets_tracking_service.exporters.arcgis import ArcGisExporter
from assets_tracking_service.exporters.base_exporter import Exporter
from assets_tracking_service.exporters.catalogue import DataCatalogueExporter
from assets_tracking_service.exporters.geojson import GeoJsonExporter


class ExportersManager:
    """Coordinates exporting data to a variety of services and file formats."""

    def __init__(self, config: Config, db: DatabaseClient, logger: logging.Logger) -> None:
        self._config = config
        self._logger = logger
        self._db = db

        self._exporters: list[Exporter] = self._make_exporters(self._config.ENABLED_EXPORTERS)

    def _make_exporters(self, exporter_names: list[str]) -> list[Exporter]:
        """Create instances for enabled exporters."""
        self._logger.info("Creating exporters...")
        exporters = []

        if "arcgis" in exporter_names:
            self._logger.info("Creating ArcGIS exporter...")
            exporters.append(ArcGisExporter(config=self._config, db=self._db, logger=self._logger))
            self._logger.info("Created ArcGIS exporter.")

        if "geojson" in exporter_names:
            self._logger.info("Creating GeoJSON exporter...")
            exporters.append(GeoJsonExporter(config=self._config, db=self._db, logger=self._logger))
            self._logger.info("Created GeoJSON provider.")

        if "data_catalogue" in exporter_names:
            self._logger.info("Creating Data Catalogue exporter...")
            exporters.append(DataCatalogueExporter(config=self._config, db=self._db, logger=self._logger))
            self._logger.info("Created Data Catalogue exporter.")

        self._logger.info("Exporters created.")
        return exporters

    def export(self) -> None:
        """Run enabled exporters."""
        self._logger.info("Exporting data...")

        for exporter in self._exporters:
            exporter.export()
