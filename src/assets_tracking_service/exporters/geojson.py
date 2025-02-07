import logging
from pathlib import Path
from typing import Self

from geojson import FeatureCollection
from geojson import dump as geojson_dump
from geojson import loads as geojson_loads
from psycopg.sql import SQL

from assets_tracking_service.config import Config
from assets_tracking_service.db import DatabaseClient
from assets_tracking_service.exporters.base_exporter import Exporter


class GeoJsonExporter(Exporter):
    """
    Exports data as GeoJSON.

    Limited to a single collection of a summary information for assets and their latest position.
    """

    def __init__(self: Self, config: Config, db: DatabaseClient, logger: logging.Logger) -> None:
        self._config = config
        self._logger = logger
        self._db = db

        self._path = config.EXPORTER_GEOJSON_OUTPUT_PATH

    @property
    def data(self: Self) -> FeatureCollection:
        """
        Get data from database as a feature collection.

        Uses the `v_latest_asset_pos_geojson` view which contains a PostGIS generated feature collection.
        This is parsed and validated as a FeatureCollection type (wrapper around a dict).
        """
        result = self._db.get_query_result(
            SQL("""SELECT geojson_feature_collection::text FROM v_latest_asset_pos_geojson;""")
        )
        self._logger.debug("Raw GeoJSON data: %s", result[0][0])

        if result[0][0] == '{"type" : "FeatureCollection", "features" : null}':
            self._logger.debug("Features list is empty, convert from `None` to `[]`.")
            result = (('{"type" : "FeatureCollection", "features" : []}',),)

        fc: FeatureCollection = geojson_loads(result[0][0])
        self._logger.debug("Parsed GeoJSON data: %s", fc)
        self._logger.info("Loaded FeatureCollection with '%d' features.", len(fc["features"]))

        return fc

    def export(self: Self, path: Path | None = None) -> None:
        """
        Export data to GeoJSON file.

        The configured output path is used unless a specific path is given.
        Any missing parent directories to this path will be created.
        """
        path = path or self._path

        self._logger.info("Ensuring parent path '%s' exists", path.parent.resolve())
        path.parent.mkdir(parents=True, exist_ok=True)

        data = self.data

        self._logger.info("Writing data to '%s'", path.resolve())
        with path.open("w") as f:
            geojson_dump(data, f, indent=2, sort_keys=False)
