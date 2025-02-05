import logging
from importlib.metadata import version
from pathlib import Path
from typing import Self, TypedDict

import dsnparse
from environs import Env, EnvError, EnvValidationError


class EditableDsn(dsnparse.ParseResult):
    """dsnparse result class to allow database (path) and password (secret) to be updated."""

    @property
    def database(self: Self) -> str:
        """Database name."""
        return super().database

    @database.setter
    def database(self: Self, value: str) -> None:
        self.fields["path"] = f"/{value}"

    @property
    def secret(self: Self) -> str:
        """Database password."""
        return super().secret

    @secret.setter
    def secret(self: Self, value: str) -> None:
        self.fields["password"] = value


class ConfigurationError(Exception):
    """Raised for configuration validation errors."""

    pass


# noinspection PyPep8Naming
class Config:
    """Application configuration."""

    def __init__(self: Self, read_env: bool = True) -> None:
        """Create Config instance and load options from possible .env file."""
        self._app_prefix = "ASSETS_TRACKING_SERVICE_"
        self._app_package = "assets-tracking-service"
        self._safe_value = "[**REDACTED**]"

        self.env = Env()
        if read_env:
            self.env.read_env()

    def validate(self: Self) -> None:  # noqa: C901
        """
        Validate configuration.

        This validation is basic/limited. E.g. We check that the DSN is in a valid format, not that we can make a valid
        database connection.

        Note: Logging level is validated at the point of access by environs automatically.

        If invalid a ConfigurationError is raised.
        """
        try:
            _ = self.DB_DSN
        except EnvError as e:
            msg = "DB_DSN must be set."
            raise ConfigurationError(msg) from e
        except (ValueError, TypeError) as e:
            msg = "DB_DSN is invalid."
            raise ConfigurationError(msg) from e

        if self.ENABLE_PROVIDER_AIRCRAFT_TRACKING:
            try:
                _ = self.PROVIDER_AIRCRAFT_TRACKING_USERNAME
            except EnvError as e:
                msg = "PROVIDER_AIRCRAFT_TRACKING_USERNAME must be set."
                raise ConfigurationError(msg) from e
            try:
                _ = self.PROVIDER_AIRCRAFT_TRACKING_PASSWORD
            except EnvError as e:
                msg = "PROVIDER_AIRCRAFT_TRACKING_PASSWORD must be set."
                raise ConfigurationError(msg) from e
            try:
                _ = self.PROVIDER_AIRCRAFT_TRACKING_API_KEY
            except EnvError as e:
                msg = "PROVIDER_AIRCRAFT_TRACKING_API_KEY must be set."
                raise ConfigurationError(msg) from e

        if self.ENABLE_PROVIDER_GEOTAB:
            try:
                _ = self.PROVIDER_GEOTAB_USERNAME
            except EnvError as e:
                msg = "PROVIDER_GEOTAB_USERNAME must be set."
                raise ConfigurationError(msg) from e
            try:
                _ = self.PROVIDER_GEOTAB_PASSWORD
            except EnvError as e:
                msg = "PROVIDER_GEOTAB_PASSWORD must be set."
                raise ConfigurationError(msg) from e
            try:
                _ = self.PROVIDER_GEOTAB_DATABASE
            except EnvError as e:
                msg = "PROVIDER_GEOTAB_DATABASE must be set."
                raise ConfigurationError(msg) from e

        if self.ENABLE_EXPORTER_GEOJSON:
            try:
                _ = self.EXPORTER_GEOJSON_OUTPUT_PATH
            except EnvError as e:
                msg = "EXPORTER_GEOJSON_OUTPUT_PATH must be set."
                raise ConfigurationError(msg) from e

        if self.ENABLE_EXPORTER_ARCGIS:
            if not self.ENABLE_EXPORTER_GEOJSON:
                msg = "ENABLE_EXPORTER_ARCGIS requires ENABLE_EXPORTER_GEOJSON to be True."
                raise ConfigurationError(msg)

            try:
                _ = self.EXPORTER_ARCGIS_USERNAME
            except EnvError as e:
                msg = "EXPORTER_ARCGIS_USERNAME must be set."
                raise ConfigurationError(msg) from e
            try:
                _ = self.EXPORTER_ARCGIS_PASSWORD
            except EnvError as e:
                msg = "EXPORTER_ARCGIS_PASSWORD must be set."
                raise ConfigurationError(msg) from e
            try:
                _ = self.EXPORTER_ARCGIS_ITEM_ID
            except EnvError as e:
                msg = "EXPORTER_ARCGIS_ITEM_ID must be set."
                raise ConfigurationError(msg) from e

        if self.ENABLE_EXPORTER_DATA_CATALOGUE:
            if not self.ENABLE_EXPORTER_ARCGIS:
                msg = "ENABLE_EXPORTER_DATA_CATALOGUE requires ENABLE_EXPORTER_ARCGIS to be True."
                raise ConfigurationError(msg)

            try:
                _ = self.EXPORTER_DATA_CATALOGUE_OUTPUT_PATH
            except EnvError as e:
                msg = "EXPORTER_DATA_CATALOGUE_OUTPUT_PATH must be set."
                raise ConfigurationError(msg) from e

            # can't check if EXPORTER_DATA_CATALOGUE_OUTPUT_PATH is a file as it's created by the exporter

    class ConfigDumpSafe(TypedDict):
        """Types for `dumps_safe`."""

        VERSION: str
        LOG_LEVEL: int
        LOG_LEVEL_NAME: str
        DB_DSN: str
        SENTRY_DSN: str
        SENTRY_ENABLED: bool
        SENTRY_ENVIRONMENT: str
        SENTRY_MONITOR_CONFIG: dict[str, dict]
        ENABLE_PROVIDER_GEOTAB: bool
        ENABLE_PROVIDER_AIRCRAFT_TRACKING: bool
        ENABLED_PROVIDERS: list[str]
        ENABLE_EXPORTER_GEOJSON: bool
        ENABLE_EXPORTER_ARCGIS: bool
        ENABLE_EXPORTER_DATA_CATALOGUE: bool
        ENABLED_EXPORTERS: list[str]
        PROVIDER_GEOTAB_USERNAME: str
        PROVIDER_GEOTAB_PASSWORD: str
        PROVIDER_GEOTAB_DATABASE: str
        PROVIDER_GEOTAB_GROUP_NVS_LO6_CODE_MAPPING: dict[str, str]
        PROVIDER_AIRCRAFT_TRACKING_USERNAME: str
        PROVIDER_AIRCRAFT_TRACKING_PASSWORD: str
        PROVIDER_AIRCRAFT_TRACKING_API_KEY: str
        EXPORTER_GEOJSON_OUTPUT_PATH: str
        EXPORTER_ARCGIS_USERNAME: str
        EXPORTER_ARCGIS_PASSWORD: str
        EXPORTER_ARCGIS_ITEM_ID: str
        EXPORTER_DATA_CATALOGUE_OUTPUT_PATH: str
        EXPORTER_DATA_CATALOGUE_RECORD_ID: str

    def dumps_safe(self: Self) -> ConfigDumpSafe:
        """Dump config for output to the user with sensitive data redacted."""
        # noinspection PyTestUnpassedFixture
        return {
            "VERSION": self.VERSION,
            "LOG_LEVEL": self.LOG_LEVEL,
            "LOG_LEVEL_NAME": self.LOG_LEVEL_NAME,
            "DB_DSN": self.DB_DSN_SAFE,
            "SENTRY_DSN": self.SENTRY_DSN,
            "ENABLE_FEATURE_SENTRY": self.ENABLE_FEATURE_SENTRY,
            "SENTRY_ENVIRONMENT": self.SENTRY_ENVIRONMENT,
            "SENTRY_MONITOR_CONFIG": self.SENTRY_MONITOR_CONFIG,
            "ENABLE_PROVIDER_GEOTAB": self.ENABLE_PROVIDER_GEOTAB,
            "ENABLE_PROVIDER_AIRCRAFT_TRACKING": self.ENABLE_PROVIDER_AIRCRAFT_TRACKING,
            "ENABLED_PROVIDERS": self.ENABLED_PROVIDERS,
            "ENABLE_EXPORTER_GEOJSON": self.ENABLE_EXPORTER_GEOJSON,
            "ENABLE_EXPORTER_ARCGIS": self.ENABLE_EXPORTER_ARCGIS,
            "ENABLE_EXPORTER_DATA_CATALOGUE": self.ENABLE_EXPORTER_DATA_CATALOGUE,
            "ENABLED_EXPORTERS": self.ENABLED_EXPORTERS,
            "PROVIDER_GEOTAB_USERNAME": self.PROVIDER_GEOTAB_USERNAME,
            "PROVIDER_GEOTAB_PASSWORD": self.PROVIDER_GEOTAB_PASSWORD_SAFE,
            "PROVIDER_GEOTAB_DATABASE": self.PROVIDER_GEOTAB_DATABASE,
            "PROVIDER_GEOTAB_GROUP_NVS_LO6_CODE_MAPPING": self.PROVIDER_GEOTAB_GROUP_NVS_LO6_CODE_MAPPING,
            "PROVIDER_AIRCRAFT_TRACKING_USERNAME": self.PROVIDER_AIRCRAFT_TRACKING_USERNAME,
            "PROVIDER_AIRCRAFT_TRACKING_PASSWORD": self.PROVIDER_AIRCRAFT_TRACKING_PASSWORD_SAFE,
            "PROVIDER_AIRCRAFT_TRACKING_API_KEY": self.PROVIDER_AIRCRAFT_TRACKING_API_KEY_SAFE,
            "EXPORTER_GEOJSON_OUTPUT_PATH": str(self.EXPORTER_GEOJSON_OUTPUT_PATH.resolve()),
            "EXPORTER_ARCGIS_USERNAME": self.EXPORTER_ARCGIS_USERNAME,
            "EXPORTER_ARCGIS_PASSWORD": self.EXPORTER_ARCGIS_PASSWORD_SAFE,
            "EXPORTER_ARCGIS_ITEM_ID": self.EXPORTER_ARCGIS_ITEM_ID,
            "EXPORTER_DATA_CATALOGUE_OUTPUT_PATH": str(self.EXPORTER_DATA_CATALOGUE_OUTPUT_PATH.resolve()),
            "EXPORTER_DATA_CATALOGUE_RECORD_ID": self.EXPORTER_DATA_CATALOGUE_RECORD_ID,
        }

    @property
    def VERSION(self: Self) -> str:
        """
        Application version.

        Read from package metadata.
        """
        return version(self._app_package)

    @property
    def LOG_LEVEL(self) -> int:
        """Logging level."""
        with self.env.prefixed(self._app_prefix):
            try:
                return self.env.log_level("LOG_LEVEL", logging.WARNING)
            except EnvValidationError as e:
                msg = "LOG_LEVEL is invalid."
                raise ConfigurationError(msg) from e

    @property
    def LOG_LEVEL_NAME(self: Self) -> str:
        """Logging level name."""
        # noinspection PyTypeChecker
        return logging.getLevelName(self.LOG_LEVEL)

    @property
    def DB_DSN(self: Self) -> str:
        """
        Psycopg connection string for app database connection.

        Optional `DB_DATABASE` overrides the database name which is needed in tests.
        """
        with self.env.prefixed(self._app_prefix):
            dsn = self.env.str("DB_DSN")
            db = self.env.str("DB_DATABASE", None)

        if db:
            dsn_parsed = dsnparse.parse(dsn, EditableDsn)
            dsn_parsed.database = db
            dsn = dsn_parsed.geturl()

        return dsn

    @property
    def DB_DSN_SAFE(self: Self) -> str:
        """DB_DSN with password redacted."""
        dsn_parsed = dsnparse.parse(self.DB_DSN, EditableDsn)
        dsn_parsed.secret = self._safe_value
        return dsn_parsed.geturl()

    @property
    def SENTRY_DSN(self) -> str:
        """Connection string for Sentry monitoring."""
        return "https://57698b6483c7ac43b7c9c905cdb79943@o39753.ingest.us.sentry.io/4507581411229696"

    @property
    def ENABLE_FEATURE_SENTRY(self) -> bool:
        """Controls whether Sentry monitoring is used."""
        with self.env.prefixed(self._app_prefix):
            return self.env.bool("ENABLE_FEATURE_SENTRY", True)

    @property
    def SENTRY_ENVIRONMENT(self) -> str:
        """Controls whether Sentry monitoring is used."""
        with self.env.prefixed(self._app_prefix):
            return self.env.str("SENTRY_ENVIRONMENT", "development")

    @property
    def SENTRY_MONITOR_CONFIG(self) -> dict[str, dict]:
        """Configuration for Sentry task monitoring."""
        return {
            "ats-run": {
                "schedule": {"type": "crontab", "value": "*/5 * * * *"},
                "timezone": "UTC",
                "checkin_margin": 2,
                "max_runtime": 5,
                "failure_issue_threshold": 3,
                "recovery_threshold": 1,
            }
        }

    @property
    def ENABLE_PROVIDER_GEOTAB(self: Self) -> bool:
        """Controls whether Geotab provider is used."""
        with self.env.prefixed(self._app_prefix):
            return self.env.bool("ENABLE_PROVIDER_GEOTAB", True)

    @property
    def ENABLE_PROVIDER_AIRCRAFT_TRACKING(self: Self) -> bool:
        """Controls whether Aircraft Tracking provider is used."""
        with self.env.prefixed(self._app_prefix):
            return self.env.bool("ENABLE_PROVIDER_AIRCRAFT_TRACKING", True)

    @property
    def ENABLED_PROVIDERS(self: Self) -> list[str]:
        """List of enabled providers."""
        providers = []

        if self.ENABLE_PROVIDER_AIRCRAFT_TRACKING:
            providers.append("aircraft_tracking")

        if self.ENABLE_PROVIDER_GEOTAB:
            providers.append("geotab")

        return providers

    @property
    def ENABLE_EXPORTER_GEOJSON(self: Self) -> bool:
        """Controls whether GeoJSON exporter is used."""
        with self.env.prefixed(self._app_prefix):
            return self.env.bool("ENABLE_EXPORTER_GEOJSON", True)

    @property
    def ENABLE_EXPORTER_ARCGIS(self: Self) -> bool:
        """Controls whether ArcGIS exporter is used."""
        with self.env.prefixed(self._app_prefix):
            return self.env.bool("ENABLE_EXPORTER_ARCGIS", True)

    @property
    def ENABLE_EXPORTER_DATA_CATALOGUE(self: Self) -> bool:
        """Controls whether Data Catalogue exporter is used."""
        with self.env.prefixed(self._app_prefix):
            return self.env.bool("ENABLE_EXPORTER_DATA_CATALOGUE", True)

    @property
    def ENABLED_EXPORTERS(self: Self) -> list[str]:
        """List of enabled exporters."""
        exporters = []

        if self.ENABLE_EXPORTER_ARCGIS:
            exporters.append("arcgis")

        if self.ENABLE_EXPORTER_GEOJSON:
            exporters.append("geojson")

        if self.ENABLE_EXPORTER_DATA_CATALOGUE:
            exporters.append("data_catalogue")

        return exporters

    @property
    def PROVIDER_GEOTAB_USERNAME(self: Self) -> str:
        """Username for Geotab SDK."""
        with self.env.prefixed(self._app_prefix), self.env.prefixed("PROVIDER_GEOTAB_"):
            return self.env.str("USERNAME")

    @property
    def PROVIDER_GEOTAB_PASSWORD(self: Self) -> str:
        """Password for Geotab SDK."""
        with self.env.prefixed(self._app_prefix), self.env.prefixed("PROVIDER_GEOTAB_"):
            return self.env.str("PASSWORD")

    @property
    def PROVIDER_GEOTAB_PASSWORD_SAFE(self: Self) -> str:
        """PROVIDER_GEOTAB_PASSWORD with value redacted."""
        return self._safe_value

    @property
    def PROVIDER_GEOTAB_DATABASE(self: Self) -> str:
        """Database name for Geotab SDK."""
        with self.env.prefixed(self._app_prefix), self.env.prefixed("PROVIDER_GEOTAB_"):
            return self.env.str("DATABASE")

    @property
    def PROVIDER_GEOTAB_GROUP_NVS_LO6_CODE_MAPPING(self: Self) -> dict[str, str]:
        """
        Mapping of Geotab group names to NVS L06 codes.

        Needed as Geotab tracks multiple types of vehicle.

        See http://vocab.nerc.ac.uk/collection/L06/current/ for allowed codes and descriptions.
        """
        return {
            "b2795": "15",  # snowmobiles, land/onshore vehicle - awaiting specific term
            "b2794": "31",  # ship, research vessel
            "b2796": "15",  # Pistonbully's, land/onshore vehicle - awaiting specific term
        }

    @property
    def PROVIDER_AIRCRAFT_TRACKING_USERNAME(self: Self) -> str:
        """Username for Aircraft Tracking provider."""
        with self.env.prefixed(self._app_prefix), self.env.prefixed("PROVIDER_AIRCRAFT_TRACKING_"):
            return self.env.str("USERNAME")

    @property
    def PROVIDER_AIRCRAFT_TRACKING_PASSWORD(self: Self) -> str:
        """Password for Aircraft Tracking provider."""
        with self.env.prefixed(self._app_prefix), self.env.prefixed("PROVIDER_AIRCRAFT_TRACKING_"):
            return self.env.str("PASSWORD")

    @property
    def PROVIDER_AIRCRAFT_TRACKING_PASSWORD_SAFE(self: Self) -> str:
        """PROVIDER_AIRCRAFT_TRACKING_PASSWORD with value redacted."""
        return self._safe_value

    @property
    def PROVIDER_AIRCRAFT_TRACKING_API_KEY(self: Self) -> str:
        """API key for Aircraft Tracking provider."""
        with self.env.prefixed(self._app_prefix), self.env.prefixed("PROVIDER_AIRCRAFT_TRACKING_"):
            return self.env.str("API_KEY")

    @property
    def PROVIDER_AIRCRAFT_TRACKING_API_KEY_SAFE(self: Self) -> str:
        """PROVIDER_AIRCRAFT_TRACKING_API_KEY with value redacted."""
        return self._safe_value

    @property
    def EXPORTER_GEOJSON_OUTPUT_PATH(self: Self) -> Path:
        """API key for Aircraft Tracking provider."""
        with self.env.prefixed(self._app_prefix), self.env.prefixed("EXPORTER_GEOJSON_"):
            return self.env.path("OUTPUT_PATH")

    @property
    def EXPORTER_ARCGIS_USERNAME(self: Self) -> str:
        """Username of user used to publish ArcGIS exporter outputs."""
        with self.env.prefixed(self._app_prefix), self.env.prefixed("EXPORTER_ARCGIS_"):
            return self.env.str("USERNAME")

    @property
    def EXPORTER_ARCGIS_PASSWORD(self: Self) -> str:
        """Password of user used to publish ArcGIS exporter outputs."""
        with self.env.prefixed(self._app_prefix), self.env.prefixed("EXPORTER_ARCGIS_"):
            return self.env.str("PASSWORD")

    @property
    def EXPORTER_ARCGIS_PASSWORD_SAFE(self: Self) -> str:
        """EXPORTER_ARCGIS_PASSWORD with value redacted."""
        return self._safe_value

    @property
    def EXPORTER_ARCGIS_ITEM_ID(self: Self) -> str:
        """Item ID of ArcGIS feature service updated by ArcGIS exporter."""
        with self.env.prefixed(self._app_prefix), self.env.prefixed("EXPORTER_ARCGIS_"):
            return self.env.str("ITEM_ID")

    @property
    def EXPORTER_DATA_CATALOGUE_OUTPUT_PATH(self: Self) -> Path:
        """Path to Data Catalogue output file."""
        with self.env.prefixed(self._app_prefix), self.env.prefixed("EXPORTER_DATA_CATALOGUE_"):
            return self.env.path("OUTPUT_PATH")

    @property
    def EXPORTER_DATA_CATALOGUE_RECORD_ID(self) -> str:
        """Record ID of Data Catalogue record updated by the Data Catalogue exporter."""
        with self.env.prefixed(self._app_prefix), self.env.prefixed("EXPORTER_DATA_CATALOGUE_"):
            return self.env.str("RECORD_ID")
