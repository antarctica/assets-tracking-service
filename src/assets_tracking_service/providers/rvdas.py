import json
import logging
from collections.abc import Generator
from datetime import datetime
from hashlib import md5
from json import JSONDecodeError

import requests
from requests import HTTPError
from shapely.geometry.point import Point

from assets_tracking_service.config import Config
from assets_tracking_service.models.asset import Asset, AssetNew
from assets_tracking_service.models.label import Label, LabelRelation, Labels
from assets_tracking_service.models.position import PositionNew
from assets_tracking_service.providers.base_provider import Provider
from assets_tracking_service.units import UnitsConverter


class RvdasProvider(Provider):
    """
    Provider for the (Open) Research Vessel Data Acquisition System (RVDAS) data logging system.

    As used on the Sir David Attenborough.
    """

    name = "rvdas"
    prefix = name
    version = "2025-04-12"
    distinguishing_asset_label_scheme = f"{prefix}:_fake_vessel_id"
    distinguishing_position_label_scheme = f"{prefix}:_fake_position_id"

    def __init__(self, config: Config, logger: logging.Logger) -> None:
        self._units = UnitsConverter()
        self._logger = logger

        self._logger.debug("Setting RVDAS configuration...")
        self._config = config
        self._logger.debug("RVDAS configuration ok.")

        self._fake_vessel_id = "1"

    def _fetch_vessels(self) -> list[dict[str, str]]:
        """Fetch hard-coded asset as this provider tracks a single, known, asset."""
        self._logger.info("Fetching vessel positions...")
        self._logger.info("Fetched vessel '1'")

        return [
            {
                "_fake_vessel_id": self._fake_vessel_id,
                "name": "SIR DAVID ATTENBOROUGH",
                "imo": "9798222",
            }
        ]

    def _fetch_data(self) -> dict:
        """
        Fetch endpoint data from provider.

        Split out to allow for easier testing.
        """
        try:
            r = requests.get(self._config.PROVIDER_RVDAS_URL, timeout=30)
            r.raise_for_status()
            try:
                return r.json()
            except JSONDecodeError as e:
                msg = "Failed to parse HTTP response as JSON."
                raise RuntimeError(msg) from e
        except HTTPError as e:
            msg = "Failed to fetch HTTP response."
            raise RuntimeError(msg) from e

    def _fetch_latest_positions(self) -> list[dict[str, str | int | float]]:
        """
        Fetch vessel positions from provider.

        This provider doesn't assign IDs to positions, so we generate a fake one based on position data.

        From OGC API - Features endpoint.
        """
        self._logger.info("Fetching vessel positions...")
        features = self._fetch_data()

        try:
            if len(features["features"]) != 1:
                msg = f"Expected exactly 1 feature in feature collection, found {len(features['features'])}."
                raise RuntimeError(msg) from None
            if features["features"][0]["geometry"]["type"] != "Point":
                msg = "Expected feature to use a Point geometry."
                raise RuntimeError(msg) from None
        except KeyError as e:
            msg = "Failed to parse feature collection."
            self._logger.exception(msg)
            raise RuntimeError(msg) from e

        _positions = []
        for position in features["features"]:
            try:
                _position = {
                    "longitude": float(position["geometry"]["coordinates"][0]),
                    "latitude": float(position["geometry"]["coordinates"][1]),
                    "speedknots": float(position["properties"]["speedknots"]),
                    "headingtrue": float(position["properties"]["headingtrue"]),
                    "gps_time": str(position["properties"]["gps_time"]),
                    "_fake_vessel_id": self._fake_vessel_id,
                }
                # hash _position to generate a fake position ID
                _position["_fake_position_id"] = md5(json.dumps(_position, sort_keys=True).encode()).hexdigest()  # noqa: S324

                self._logger.info("Fetched position for vessel ID: '%s'", _position["_fake_vessel_id"])
                _positions.append(_position)
            except KeyError:
                self._logger.warning(
                    "Skipping position for vessel ID: '%s' due to missing required fields.", self._fake_vessel_id
                )
                self._logger.debug("Skipped position: '%s'", position)
                continue

        return _positions

    def fetch_active_assets(self) -> Generator[AssetNew, None, None]:
        """
        Acquire vessels as assets.

        - all Assets returned by this provider are considered active
        - Assets can be easily distinguished via an ID
        - as only vessels (research vessels) are returned, the platform type can be hard coded.
        """
        self._logger.info("Fetching vessels as assets...")

        try:
            vessels = self._fetch_vessels()
        except RuntimeError as e:
            msg = "Failed to fetch vessels from provider."
            self._logger.exception(msg)
            raise RuntimeError(msg) from e

        for vessel in vessels:
            id_label = Label(
                rel=LabelRelation.SELF, scheme=self.distinguishing_asset_label_scheme, value=vessel["_fake_vessel_id"]
            )
            pref_label = Label(rel=LabelRelation.SELF, scheme="skos:prefLabel", value=vessel["name"])
            platform_label = Label(
                rel=LabelRelation.SELF,
                scheme="nvs:L06",
                scheme_uri="http://vocab.nerc.ac.uk/collection/L06/current",
                value="31",
                value_uri="http://vocab.nerc.ac.uk/collection/L06/current/31",
            )

            device_labels = [
                Label(rel=LabelRelation.SELF, scheme=f"{self.prefix}:{key}", value=value)
                for key, value in vessel.items()
            ]

            labels = Labels([id_label, pref_label, platform_label, *device_labels, *self.provider_labels])
            self._logger.debug("Asset labels: '%s'", labels.unstructure())

            yield AssetNew(labels=labels)

    def fetch_latest_positions(self, assets: list[Asset]) -> Generator[PositionNew, None, None]:
        """
        Acquire vessel positions as asset positions.

        - Positions can be easily distinguished via a derived/fake ID.
        """
        self._logger.info("Fetching position of vessels...")

        indexed_assets = self._index_assets(assets)

        try:
            positions = self._fetch_latest_positions()
        except RuntimeError as e:
            msg = "Failed to fetch vessel positions from provider."
            self._logger.exception(msg)
            raise RuntimeError(msg) from e

        for position in positions:
            try:
                self._logger.debug("Getting corresponding asset for vessel in position...")
                asset = indexed_assets[position["_fake_vessel_id"]]
                self._logger.debug("Asset ID: '%s'", asset.id)
            except KeyError:
                self._logger.warning(
                    "Skipping position for vessel ID: '%s' as asset not available.", position["_fake_vessel_id"]
                )
                continue

            id_label = Label(
                rel=LabelRelation.SELF,
                scheme=self.distinguishing_position_label_scheme,
                value=position["_fake_position_id"],
            )

            position_labels = [
                Label(rel=LabelRelation.SELF, scheme=f"{self.prefix}:{key}", value=value)
                for key, value in position.items()
            ]

            labels = Labels([id_label, *position_labels, *self.provider_labels])
            self._logger.debug("Position labels: '%s'", labels.unstructure())

            time = datetime.fromisoformat(position["gps_time"]).replace(microsecond=0)

            yield PositionNew(
                asset_id=asset.id,
                time=time,
                geom=Point(position["longitude"], position["latitude"]),
                velocity=self._units.knots_to_meters_per_second(position["speedknots"]),
                heading=position["headingtrue"],
                labels=labels,
            )
