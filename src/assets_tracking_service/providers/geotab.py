import logging
from collections.abc import Generator
from datetime import datetime

# noinspection PyPep8Naming
from mygeotab import API as Geotab  # noqa: N811
from mygeotab import MyGeotabException, TimeoutException
from requests import HTTPError
from shapely import Point

from assets_tracking_service.config import Config
from assets_tracking_service.models.asset import Asset, AssetNew
from assets_tracking_service.models.label import Label, LabelRelation, Labels
from assets_tracking_service.models.position import PositionNew
from assets_tracking_service.providers.base_provider import Provider
from assets_tracking_service.units import UnitsConverter


class GeotabProvider(Provider):
    """Provider for Geotab service."""

    name = "geotab"
    prefix = name
    version = "2024-07-02"
    distinguishing_asset_label_scheme = f"{prefix}:device_id"
    distinguishing_position_label_scheme = f"{prefix}:log_record_id"

    def __init__(self, config: Config, logger: logging.Logger) -> None:
        self._units = UnitsConverter()
        self._logger = logger

        self._logger.debug("Setting Geotab configuration...")
        self._config = config
        self._logger.debug("Geotab configuration ok.")

        self._logger.debug("Creating Geotab SDK client...")
        try:
            self._client = Geotab(
                username=self._config.PROVIDER_GEOTAB_USERNAME,
                password=self._config.PROVIDER_GEOTAB_PASSWORD,
                database=self._config.PROVIDER_GEOTAB_DATABASE,
            )
            self._logger.debug("Geotab SDK client created.")
            self._logger.debug("Authenticating Geotab SDK client.")
            self._client.authenticate()
            self._logger.debug("Geotab SDK client authenticated.")
        except (MyGeotabException, TimeoutException) as e:
            msg = "Failed to initialise Geotab Provider."
            raise RuntimeError(msg) from e

    def _fetch_devices(self) -> list[dict[str, str]]:
        """
        Fetch devices from provider.

        A device represents an asset.
        """
        self._logger.info("Fetching Geotab devices...")

        try:
            devices = self._client.get("Device")
        except (MyGeotabException, TimeoutException, HTTPError) as e:
            msg = "Failed to fetch devices."
            raise RuntimeError(msg) from e

        _devices = []
        for device in devices:
            try:
                _device = {
                    "device_id": device["id"],
                    "device_serial_number": device["serialNumber"],
                    "device_name": device.get("name", None),
                    "device_comment": device.get("name", None),
                    "device_group_ids": ",".join([group["id"] for group in device.get("groups", [])]),
                }
                self._logger.info("Fetched device: '%s'", device["id"])
                _devices.append(_device)
            except KeyError:
                self._logger.warning(
                    "Skipping device: '%s' due to missing required fields.", device.get("id", "unknown")
                )
                self._logger.debug("Skipped device: '%s'", device)
                continue

        return _devices

    def _fetch_device_statuses(self) -> list[dict[str, str | float | datetime]]:
        """
        Fetch the status for all devices from provider.

        A device status represents an asset position.

        Device status returns a large amount of information, most of which is not needed. Crucially it includes
        orientation which isn't part of other entities such as log records.

        Device status entities do not include a distinguishing property however and so need correlating with another
        entity type, such as a log record.
        """
        self._logger.info("Fetching Geotab devices statuses...")

        try:
            device_statues = self._client.get("DeviceStatusInfo")
        except (MyGeotabException, TimeoutException, HTTPError) as e:
            msg = "Failed to fetch device statues."
            raise RuntimeError(msg) from e

        _device_statues = []
        for device_status in device_statues:
            try:
                status = {
                    "bearing_degrees": float(device_status["bearing"]) if "bearing" in device_status else None,
                    "latitude": float(device_status["latitude"]),
                    "longitude": float(device_status["longitude"]),
                    "speed_km_h": float(device_status["speed"]) if "speed" in device_status else None,
                    "date": device_status["dateTime"],
                    "device_id": device_status["device"]["id"],
                }
                self._logger.info("Fetched status for device ID: '%s'", device_status["device"]["id"])
                _device_statues.append(status)
            except KeyError:
                self._logger.warning(
                    "Skipping status for device ID: '%s' due to missing required fields.",
                    device_status.get("device", {"id": "null"}).get("id", "unknown"),
                )
                self._logger.debug("Skipped status: '%s'", device_status)

        return _device_statues

    def _fetch_log_record(self, time: datetime, device_id: str) -> dict:
        """
        Fetch a log record for a device at a specific time.

        Log records include position and speed information. It also crucially includes a distinguishing property.
        A log record can be correlated with a device status using time and device ID properties.

        As this method is intended to return a proxy for a device status ID, if multiple log records are found, an
        exception is raised.
        """
        self._logger.debug("Fetching Geotab log record...")

        try:
            results = self._client.get(
                "LogRecord",
                search={
                    "fromDate": time,
                    "toDate": time,
                    "deviceSearch": {"id": device_id},
                },
            )
        except (MyGeotabException, TimeoutException, HTTPError) as e:
            msg = "Failed to fetch LogRecord."
            raise RuntimeError(msg) from e

        if len(results) == 0:
            msg = f"No log record found for device ID '{device_id}' at time '{time}'."
            raise IndexError(msg)
        if len(results) > 1:
            msg = f"Multiple log records found for device ID '{device_id}' at time '{time}'."
            raise IndexError(msg)

        self._logger.info(
            "Fetched log record ID: '%s' for device ID: '%s'", results[0]["id"], results[0]["device"]["id"]
        )
        return results[0]

    def fetch_active_assets(self) -> Generator[AssetNew, None, None]:
        """
        Acquire devices as assets.

        - all assets returned by this provider are assumed to be active
        - Assets can be easily distinguished via an ID
        - asset names are used as the preferred label, if available, otherwise the serial number is used
        - the platform type is determined by a machine type group assigned in the Geotab interface
        - some platform types do not yet have specific terms in the L06 vocabulary and so use a general class
        """
        self._logger.info("Fetching Geotab devices as assets...")

        try:
            devices = self._fetch_devices()
        except RuntimeError as e:
            msg = "Failed to fetch devices from Geotab."
            self._logger.exception(msg)
            raise RuntimeError(msg) from e

        for device in devices:
            self._logger.debug(
                "Determining prefLabel from name: '%s' and serial number: '%s'",
                device["device_name"],
                device["device_serial_number"],
            )
            pref_label_value = device["device_name"] if device["device_name"] else device["device_serial_number"]
            pref_label = Label(rel=LabelRelation.SELF, scheme="skos:prefLabel", value=pref_label_value)

            self._logger.debug("Determining platform type from group mappings...")
            self._logger.debug("Raw groups: '%s'", device["device_group_ids"])
            platform_types = [
                self._config.PROVIDER_GEOTAB_GROUP_NVS_LO6_CODE_MAPPING[group_id]
                for group_id in device["device_group_ids"].split(",")
                if group_id in self._config.PROVIDER_GEOTAB_GROUP_NVS_LO6_CODE_MAPPING
            ]
            self._logger.debug("Platform types: '%s'", platform_types)
            platform_type_value = platform_types[0] if len(platform_types) == 1 else "0"
            self._logger.debug("Platform type resolved to: '%s'", platform_type_value)
            platform_label = Label(
                rel=LabelRelation.SELF,
                scheme="nvs:L06",
                scheme_uri="http://vocab.nerc.ac.uk/collection/L06/current",
                value=platform_type_value,
                value_uri=f"http://vocab.nerc.ac.uk/collection/L06/current/{platform_type_value}",
            )

            device_labels = [
                Label(rel=LabelRelation.SELF, scheme=f"{self.prefix}:{key}", value=value)
                for key, value in device.items()
            ]

            labels = Labels([pref_label, platform_label, *device_labels, *self.provider_labels])
            self._logger.debug("Asset labels: '%s'", labels.unstructure())

            yield AssetNew(labels=labels)

    def fetch_latest_positions(self, assets: list[Asset]) -> Generator[PositionNew, None, None]:
        """
        Acquire device statuses as asset positions.

        - Positions can be cannot be distinguished via a device status alone
        - a log record correlating to each device status is used as a proxy to provide a distinguishing property
        - heading values can be unknown, determined using a sentinel value
        - the Geotab SDK uses Python dates which need to converting to JSON serializable strings for use in a label
        """
        self._logger.info("Fetching status of Geotab devices as positions...")

        indexed_assets = self._index_assets(assets)

        try:
            device_statuses = self._fetch_device_statuses()
        except RuntimeError as e:
            msg = "Failed to fetch device statuses from Geotab."
            self._logger.exception(msg)
            raise RuntimeError(msg) from e

        for device_status in device_statuses:
            try:
                self._logger.debug("Getting corresponding asset for device in status...")
                asset = indexed_assets[device_status["device_id"]]
                self._logger.debug("Asset ID: '%s'", asset.id)
            except KeyError:
                self._logger.warning(
                    "Skipping status for device ID: '%s' as asset not available.", device_status["device_id"]
                )
                continue

            try:
                self._logger.debug("Fetching corresponding Geotab LogRecord for status...")
                log_record = self._fetch_log_record(time=device_status["date"], device_id=device_status["device_id"])
                self._logger.debug("Fetched LogRecord ID: '%s'", log_record["id"])
                log_record_label = Label(
                    rel=LabelRelation.SELF, scheme=f"{self.prefix}:log_record_id", value=log_record["id"]
                )
            except (RuntimeError, IndexError):
                self._logger.warning(
                    "Skipping status for device ID: '%s' as LogRecord not available.", device_status["device_id"]
                )
                continue

            # headings can be unknown
            _heading = device_status["bearing_degrees"]
            if _heading == -1:
                self._logger.debug("Position heading is unknown (-1)")
                _heading = None
                device_status["bearing_unknown"] = True

            # values in labels need to be JSON serializable
            _time = device_status["date"]
            device_status["date"] = device_status["date"].isoformat()

            status_labels = [
                Label(rel=LabelRelation.SELF, scheme=f"{self.prefix}:{key}", value=value)
                for key, value in device_status.items()
            ]

            labels = Labels([log_record_label, *status_labels, *self.provider_labels])
            self._logger.debug("Position labels: '%s'", labels.unstructure())

            yield PositionNew(
                asset_id=asset.id,
                time=_time,
                geom=Point(device_status["longitude"], device_status["latitude"]),
                velocity=self._units.kilometers_per_hour_to_meters_per_second(device_status["speed_km_h"]),
                heading=_heading,
                labels=labels,
            )
