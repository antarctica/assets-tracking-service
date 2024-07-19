import logging
from typing import Self

from assets_tracking_service.config import Config
from assets_tracking_service.db import DatabaseClient
from assets_tracking_service.exporters.arcgis import ArcGISExporter
from assets_tracking_service.exporters.base_exporter import Exporter
from assets_tracking_service.exporters.geojson import GeoJsonExporter


class ExportersManager:
    """Coordinates exporting data to a variety of services and file formats."""

    def __init__(self: Self, config: Config, db: DatabaseClient, logger: logging.Logger) -> None:
        self._config = config
        self._logger = logger
        self._db = db

        self._exporters: list[Exporter] = self._make_exporters(self._config.enabled_exporters)

    def _make_exporters(self: Self, exporter_names: list[str]) -> list[Exporter]:
        """Create instances for enabled exporters."""
        self._logger.info("Creating exporters...")
        exporters = []

        if "arcgis" in exporter_names:
            self._logger.info("Creating ArcGIS exporter...")
            exporters.append(ArcGISExporter(config=self._config, db=self._db, logger=self._logger))
            self._logger.info("Created ArcGIS exporter.")

        if "geojson" in exporter_names:
            self._logger.info("Creating GeoJSON exporter...")
            exporters.append(GeoJsonExporter(config=self._config, db=self._db, logger=self._logger))
            self._logger.info("Created GeoJSON provider.")

        self._logger.info("Exporters created.")
        return exporters

    def export(self: Self) -> None:
        """Run enabled exporters."""
        self._logger.info("Exporting data...")

        for exporter in self._exporters:
            exporter.export()
