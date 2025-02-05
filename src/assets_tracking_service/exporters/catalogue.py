import logging
from json import dump as json_dump
from typing import Self

from assets_tracking_service.config import Config
from assets_tracking_service.db import DatabaseClient
from assets_tracking_service.exporters.base_exporter import Exporter


class DataCatalogueExporter(Exporter):
    """Exports metadata records for the BAS Data Catalogue."""

    def __init__(self: Self, config: Config, db: DatabaseClient, logger: logging.Logger) -> None:
        self._config = config
        self._logger = logger
        self._db = db

        self._path = config.EXPORTER_DATA_CATALOGUE_OUTPUT_PATH

    @property
    def metadata(self) -> dict:
        """
        Generate metadata record for the summary layer.

        Combines static content (title, abstract, etc.) along with dynamic information from the `summary_metadata`
        view to produce a metadata record describing the summary layer as a dataset resource.
        """
        return {"id": self._config.EXPORTER_DATA_CATALOGUE_RECORD_ID}  # temp content

    def export(self) -> None:
        """
        Export metadata record as a JSON file to the configured output directory.

        Any missing parent directories to this output path will be created.
        """
        path = self._path

        self._logger.info("Ensuring parent path '%s' exists", path.parent.resolve())
        path.parent.mkdir(parents=True, exist_ok=True)

        data = self.metadata

        self._logger.info("Writing metadata record to '%s'", path.resolve())
        with path.open("w") as f:
            # noinspection PyTypeChecker
            json_dump(data, f, indent=2, sort_keys=False)
