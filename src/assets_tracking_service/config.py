from importlib.metadata import version
from pathlib import Path
from typing import Self, TypedDict

import dsnparse
from environs import Env, EnvError


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

    class ConfigDumpSafe(TypedDict):
        """Types for `dumps_safe`."""

        version: str
        db_dsn: str
        sentry_dsn: str
        SENTRY_ENABLED: bool
        SENTRY_ENVIRONMENT: str
        sentry_monitor_slug_ats_run: str
        enable_provider_geotab: bool
        enable_provider_aircraft_tracking: bool
        enabled_providers: list[str]
        enable_exporter_geojson: bool
        enable_exporter_arcgis: bool
        enabled_exporters: list[str]
        provider_geotab_username: str
        provider_geotab_password: str
        provider_geotab_database: str
        provider_geotab_group_nvs_l06_code_mapping: dict[str, str]
        provider_aircraft_tracking_username: str
        provider_aircraft_tracking_password: str
        provider_aircraft_tracking_api_key: str
        exporter_geojson_output_path: str
        exporter_arcgis_username: str
        exporter_arcgis_password: str
        exporter_arcgis_item_id: str

    def dumps_safe(self: Self) -> ConfigDumpSafe:
        """Dump config for output to the user with sensitive data redacted."""
        # noinspection PyTestUnpassedFixture
        return {
            "version": self.version,
            "db_dsn": self.db_dsn_safe,
            "sentry_dsn": self.sentry_dsn,
            "enable_feature_sentry": self.ENABLE_FEATURE_SENTRY,
            "sentry_environment": self.SENTRY_ENVIRONMENT,
            "sentry_monitor_slug_ats_run": self.sentry_monitor_slug_ats_run,
            "enable_provider_geotab": self.ENABLE_PROVIDER_GEOTAB,
            "enable_provider_aircraft_tracking": self.ENABLE_PROVIDER_AIRCRAFT_TRACKING,
            "enabled_providers": self.enabled_providers,
            "enable_exporter_geojson": self.ENABLE_EXPORTER_GEOJSON,
            "enable_exporter_arcgis": self.ENABLE_EXPORTER_ARCGIS,
            "enabled_exporters": self.enabled_exporters,
            "provider_geotab_username": self.PROVIDER_GEOTAB_USERNAME,
            "provider_geotab_password": self.provider_geotab_password_safe,
            "provider_geotab_database": self.PROVIDER_GEOTAB_DATABASE,
            "provider_geotab_group_nvs_l06_code_mapping": self.provider_geotab_group_nvs_l06_code_mapping,
            "provider_aircraft_tracking_username": self.PROVIDER_AIRCRAFT_TRACKING_USERNAME,
            "provider_aircraft_tracking_password": self.provider_aircraft_tracking_password_safe,
            "provider_aircraft_tracking_api_key": self.provider_aircraft_tracking_api_key_safe,
            "exporter_geojson_output_path": str(self.EXPORTER_GEOJSON_OUTPUT_PATH.resolve()),
            "exporter_arcgis_username": self.EXPORTER_ARCGIS_USERNAME,
            "exporter_arcgis_password": self.exporter_arcgis_password_safe,
            "exporter_arcgis_item_id": self.EXPORTER_ARCGIS_ITEM_ID,
        }

    @property
    def version(self: Self) -> str:
        """
        Application version.

        Read from package metadata.
        """
        return version(self._app_package)

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
    def db_dsn_safe(self: Self) -> str:
        """DB_DSN with password redacted."""
        dsn_parsed = dsnparse.parse(self.DB_DSN, EditableDsn)
        dsn_parsed.secret = self._safe_value
        return dsn_parsed.geturl()

    @property
    def sentry_dsn(self) -> str:
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
    def sentry_monitor_slug_ats_run(self) -> str:
        """Slug for the Sentry monitor used to track fetch-export runs of the application."""
        return "ats-run"

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
    def enabled_providers(self: Self) -> list[str]:
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
    def enabled_exporters(self: Self) -> list[str]:
        """List of enabled exporters."""
        exporters = []

        if self.ENABLE_EXPORTER_ARCGIS:
            exporters.append("arcgis")

        if self.ENABLE_EXPORTER_GEOJSON:
            exporters.append("geojson")

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
    def provider_geotab_password_safe(self: Self) -> str:
        """PROVIDER_GEOTAB_PASSWORD with value redacted."""
        return self._safe_value

    @property
    def PROVIDER_GEOTAB_DATABASE(self: Self) -> str:
        """Database name for Geotab SDK."""
        with self.env.prefixed(self._app_prefix), self.env.prefixed("PROVIDER_GEOTAB_"):
            return self.env.str("DATABASE")

    @property
    def provider_geotab_group_nvs_l06_code_mapping(self: Self) -> dict[str, str]:
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
    def provider_aircraft_tracking_password_safe(self: Self) -> str:
        """PROVIDER_AIRCRAFT_TRACKING_PASSWORD with value redacted."""
        return self._safe_value

    @property
    def PROVIDER_AIRCRAFT_TRACKING_API_KEY(self: Self) -> str:
        """API key for Aircraft Tracking provider."""
        with self.env.prefixed(self._app_prefix), self.env.prefixed("PROVIDER_AIRCRAFT_TRACKING_"):
            return self.env.str("API_KEY")

    @property
    def provider_aircraft_tracking_api_key_safe(self: Self) -> str:
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
    def exporter_arcgis_password_safe(self: Self) -> str:
        """EXPORTER_ARCGIS_PASSWORD with value redacted."""
        return self._safe_value

    @property
    def EXPORTER_ARCGIS_ITEM_ID(self: Self) -> str:
        """Item ID of ArcGIS feature service updated by ArcGIS exporter."""
        with self.env.prefixed(self._app_prefix), self.env.prefixed("EXPORTER_ARCGIS_"):
            return self.env.str("ITEM_ID")
