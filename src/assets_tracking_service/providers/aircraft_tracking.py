import logging
from collections.abc import Generator
from datetime import UTC, datetime
from typing import Self, TypedDict

from assets_tracking_service_aircraft_provider.providers.aircraft_tracking import (
    AircraftTrackerProvider as AircraftTrackerClient,
)
from requests import HTTPError
from shapely import Point

from assets_tracking_service.models.asset import Asset, AssetNew
from assets_tracking_service.models.label import Label, LabelRelation, Labels
from assets_tracking_service.models.position import PositionNew
from assets_tracking_service.providers.base_provider import Provider
from assets_tracking_service.units import UnitsConverter


class AircraftTrackingConfig(TypedDict):
    """Configuration for `AircraftTrackingProvider`."""

    username: str
    password: str
    api_key: str


class AircraftTrackingProvider(Provider):
    """Provider for Aircraft Tracking service."""

    name = "aircraft_tracking"
    prefix = name
    version = "2024-07-05"
    distinguishing_asset_label_scheme = f"{prefix}:aircraft_id"
    distinguishing_position_label_scheme = f"{prefix}:position_id"

    def __init__(self: Self, config: AircraftTrackingConfig, logger: logging.Logger) -> None:
        self._units = UnitsConverter()
        self._logger = logger

        self._logger.debug("Setting Aircraft Tracking configuration...")
        self._check_config(config)
        self._config = config
        self._logger.debug("Aircraft Tracking configuration ok.")

        self._logger.debug("Creating Aircraft Tracking SDK client...")
        self.client = AircraftTrackerClient(
            eclair=self._config["username"], croissant=self._config["password"], baguette=self._config["api_key"]
        )
        self._logger.debug("Aircraft Tracking SDK client created.")

    def _check_config(self: Self, config: AircraftTrackingConfig) -> None:
        """Check credentials are provided."""
        for key in ["username", "password", "api_key"]:
            if key not in config:
                msg = f"Missing required config key: '{key}'"
                self._logger.error(msg)
                raise RuntimeError(msg)

    def _fetch_aircraft(self: Self) -> list[dict[str, str]]:
        """
        Fetch aircraft from provider.

        An aircraft  represents an asset.

        Properties are obscured for legal reasons and need converting back into something useful.
        """
        self._logger.info("Fetching aircraft...")

        try:
            aircraft = self.client.get_active_aircraft()
        except HTTPError as e:
            msg = "Failed to fetch aircraft."
            raise RuntimeError(msg) from e

        _aircraft = []
        for airplane in aircraft:
            try:
                _airplane = {
                    "aircraft_id": str(airplane["oak"]),
                    "esn": airplane["elm"],
                    "msisdn": airplane["yew"],
                    "name": airplane["ash"],
                    "registration": airplane["teak"],
                }
                self._logger.info("Fetched aircraft: '%s'", airplane["oak"])
                _aircraft.append(_airplane)
            except KeyError:
                self._logger.warning(
                    "Skipping aircraft: '%s' due to missing required fields.", airplane.get("oak", "unknown")
                )
                self._logger.debug("Skipped aircraft: '%s'", airplane)
                continue

        return _aircraft

    def _fetch_latest_positions(self: Self) -> list[dict[str, str | int | float]]:
        """
        Fetch aircraft positions from provider.

        Properties are obscured for legal reasons and need converting back into something useful.
        """
        self._logger.info("Fetching aircraft positions...")

        try:
            positions = self.client.get_last_aircraft_positions()
        except HTTPError as e:
            msg = "Failed to fetch aircraft positions."
            raise RuntimeError(msg) from e

        _positions = []
        for position in positions:
            try:
                _position = {
                    "longitude": float(position["cheesecake"]),
                    "latitude": float(position["fudge"]),
                    "altitude_feet": float(position["fruit"]),
                    "speed_knots": float(position["christmas"]),
                    "heading_degrees": float(position["lemon_drizzle"]),
                    "utc_milliseconds": int(position["victoria"]),
                    "aircraft_id": str(position["banana"]),
                    "position_id": str(position["battenberg"]),
                }
                self._logger.info("Fetched position for aircraft ID: '%s'", position["banana"])
                _positions.append(_position)
            except KeyError:
                self._logger.warning(
                    "Skipping position ID '%s' for aircraft ID: '%s' due to missing required fields.",
                    position.get("battenberg", "unknown"),
                    position.get("banana", "unknown"),
                )
                self._logger.debug("Skipped position: '%s'", position)
                continue

        return _positions

    def fetch_active_assets(self: Self) -> Generator[AssetNew, None, None]:
        """
        Acquire aircraft as assets.

        - all assets returned by this provider are considered active
        - Assets can be easily distinguished via an ID
        - as only aircraft are returned, the platform type can be hard coded.
        """
        self._logger.info("Fetching aircraft as assets...")

        try:
            aircraft = self._fetch_aircraft()
        except RuntimeError as e:
            msg = "Failed to fetch aircraft from provider."
            self._logger.exception(msg)
            raise RuntimeError(msg) from e

        for aeroplane in aircraft:
            id_label = Label(
                rel=LabelRelation.SELF, scheme=self.distinguishing_asset_label_scheme, value=aeroplane["aircraft_id"]
            )
            pref_label = Label(rel=LabelRelation.SELF, scheme="skos:prefLabel", value=aeroplane["name"])
            platform_label = Label(
                rel=LabelRelation.SELF,
                scheme="nvs:L06",
                scheme_uri="http://vocab.nerc.ac.uk/collection/L06/current",
                value="62",
                value_uri="http://vocab.nerc.ac.uk/collection/L06/current/62",
            )

            device_labels = [
                Label(rel=LabelRelation.SELF, scheme=f"{self.prefix}:{key}", value=value)
                for key, value in aeroplane.items()
            ]

            labels = Labels([id_label, pref_label, platform_label, *device_labels, *self.provider_labels])
            self._logger.debug("Asset labels: '%s'", labels.unstructure())

            yield AssetNew(labels=labels)

    def fetch_latest_positions(self: Self, assets: list[Asset]) -> Generator[PositionNew, None, None]:
        """
        Acquire aircraft positions as asset positions.

        - Positions can be easily distinguished via an ID.
        """
        self._logger.info("Fetching position of Aircraft...")

        indexed_assets = self._index_assets(assets)

        try:
            positions = self._fetch_latest_positions()
        except RuntimeError as e:
            msg = "Failed to fetch aircraft positions from provider."
            self._logger.exception(msg)
            raise RuntimeError(msg) from e

        for position in positions:
            try:
                self._logger.debug("Getting corresponding asset for aircraft in position...")
                asset = indexed_assets[position["aircraft_id"]]
                self._logger.debug("Asset ID: '%s'", asset.id)
            except KeyError:
                self._logger.warning(
                    "Skipping position for aircraft ID: '%s' as asset not available.", position["aircraft_id"]
                )
                continue

            id_label = Label(
                rel=LabelRelation.SELF, scheme=self.distinguishing_position_label_scheme, value=position["position_id"]
            )

            position_labels = [
                Label(rel=LabelRelation.SELF, scheme=f"{self.prefix}:{key}", value=value)
                for key, value in position.items()
            ]

            labels = Labels([id_label, *position_labels, *self.provider_labels])
            self._logger.debug("Position labels: '%s'", labels.unstructure())

            time = datetime.fromtimestamp(
                self._units.timestamp_milliseconds_to_timestamp(position["utc_milliseconds"]),
                tz=UTC,
            )
            elevation = self._units.feet_to_meters(position["altitude_feet"])

            yield PositionNew(
                asset_id=asset.id,
                time=time,
                geom=Point(position["longitude"], position["latitude"], elevation),
                velocity=self._units.knots_to_meters_per_second(position["speed_knots"]),
                heading=position["heading_degrees"],
                labels=labels,
            )
