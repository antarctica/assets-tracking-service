import json
import logging

from geojson import FeatureCollection, loads as geojson_loads, dump as geojson_dump
from psycopg.sql import SQL

from assets_tracking_service.config import Config
from assets_tracking_service.db import DatabaseClient
from assets_tracking_service.exporters.base_exporter import Exporter


class GeoJsonExporter(Exporter):
    def __init__(self, config: Config, db: DatabaseClient, logger: logging.Logger):
        self._config = config
        self._logger = logger
        self._db = db

        self._path = config.EXPORTER_GEOJSON_OUTPUT_PATH

    @property
    def data(self) -> FeatureCollection:
        result = self._db.get_query_result(SQL("""SELECT geojson_feature_collection FROM summary_geojson;"""))
        self._logger.debug("Raw GeoJSON data: %s", result[0][0])

        if result[0][0]["features"] is None:
            self._logger.debug("Features list is empty, convert from `None` to `[]`.")
            result[0][0]["features"] = []

        fc: FeatureCollection = geojson_loads(json.dumps(result[0][0]))
        self._logger.debug("Parsed GeoJSON data: %s", fc)
        self._logger.info("Loaded FeatureCollection with '%d' features.", len(fc["features"]))

        return fc

    def export(self):
        self._logger.info("Ensuring parent path '%s' exists", self._path.parent.resolve())
        self._path.parent.mkdir(parents=True, exist_ok=True)

        data = self.data

        self._logger.info("Writing data to '%s'", self._path.resolve())
        # print(geojson_dumps(self.data, indent=2, sort_keys=False))
        with self._path.open("w") as geojson_file:
            geojson_dump(data, geojson_file, indent=2, sort_keys=False)
