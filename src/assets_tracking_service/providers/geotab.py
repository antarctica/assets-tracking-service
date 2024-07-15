import logging
from datetime import datetime
from typing import Generator, TypedDict

# noinspection PyPep8Naming
from mygeotab import API as Geotab, MyGeotabException, TimeoutException
from shapely import Point

from assets_tracking_service.models.asset import AssetNew, Asset
from assets_tracking_service.models.label import Labels, Label, LabelRelation
from assets_tracking_service.models.position import PositionNew
from assets_tracking_service.models.provider import Provider
from assets_tracking_service.units import UnitsConverter


class GeotabConfig(TypedDict):
    username: str
    password: str
    database: str
    nvs_l06_group_mappings: dict[str, str]


class GeotabProvider(Provider):
    name = "geotab"
    prefix = name
    version = "2024-07-02"
    distinguishing_asset_label_scheme = f"{prefix}:device_id"
    distinguishing_position_label_scheme = f"{prefix}:log_record_id"

    def __init__(self, config: GeotabConfig, logger: logging.Logger):
        self._units = UnitsConverter()
        self._logger = logger

        self._logger.debug("Setting Geotab configuration...")
        self._check_config(config)
        self._config = config
        self._logger.debug("Geotab configuration ok.")

        self._logger.debug("Creating Geotab SDK client...")
        try:
            self._client = Geotab(
                username=self._config["username"], password=self._config["password"], database=self._config["database"]
            )
            self._logger.debug("Geotab SDK client created.")
            self._logger.debug("Authenticating Geotab SDK client.")
            self._client.authenticate()
            self._logger.debug("Geotab SDK client authenticated.")
        except (MyGeotabException, TimeoutException) as e:
            raise RuntimeError("Failed to initialise Geotab Provider.") from e

    def _check_config(self, config: GeotabConfig) -> None:
        for key in ["username", "password", "database", "nvs_l06_group_mappings"]:
            if key not in config:
                msg = f"Missing required config key: '{key}'"
                self._logger.error(msg)
                raise RuntimeError(msg)

    def _fetch_devices(self) -> list[dict[str, str]]:
        self._logger.info("Fetching Geotab devices...")

        try:
            devices = self._client.get("Device")
        except (MyGeotabException, TimeoutException) as e:
            raise RuntimeError("Failed to fetch devices.") from e

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
        self._logger.info("Fetching Geotab devices statuses...")

        try:
            device_statues = self._client.get("DeviceStatusInfo")
        except (MyGeotabException, TimeoutException) as e:
            raise RuntimeError("Failed to fetch device statues.") from e

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
        except (MyGeotabException, TimeoutException) as e:
            raise RuntimeError("Failed to fetch LogRecord.") from e

        if len(results) == 0:
            raise IndexError(f"No log record found for device ID '{device_id}' at time '{time}'.")
        if len(results) > 1:
            raise IndexError(f"Multiple log records found for device ID '{device_id}' at time '{time}'.")

        self._logger.info(
            "Fetched log record ID: '%s' for device ID: '%s'", results[0]["id"], results[0]["device"]["id"]
        )
        return results[0]

    def fetch_active_assets(self) -> Generator[AssetNew, None, None]:
        self._logger.info("Fetching Geotab devices as assets...")

        try:
            devices = self._fetch_devices()
        except RuntimeError as e:
            msg = "Failed to fetch devices from Geotab."
            self._logger.error(msg)
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
                self._config["nvs_l06_group_mappings"][group_id]
                for group_id in device["device_group_ids"].split(",")
                if group_id in self._config["nvs_l06_group_mappings"]
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
        self._logger.info("Fetching status of Geotab devices as positions...")

        indexed_assets = self._index_assets(assets)

        try:
            device_statuses = self._fetch_device_statuses()
        except RuntimeError as e:
            msg = "Failed to fetch device statuses from Geotab."
            self._logger.error(msg)
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
