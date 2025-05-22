import logging
from importlib.metadata import version
from pathlib import Path
from typing import TypedDict

import dsnparse
from environs import Env, EnvError, EnvValidationError


class EditableDsn(dsnparse.ParseResult):
    """dsnparse result class to allow database (path) and password (secret) to be updated."""

    @property
    def database(self) -> str:
        """Database name."""
        return super().database

    @database.setter
    def database(self, value: str) -> None:
        self.fields["path"] = f"/{value}"

    @property
    def secret(self) -> str:
        """Database password."""
        return super().secret

    @secret.setter
    def secret(self, value: str) -> None:
        self.fields["password"] = value


class ConfigurationError(Exception):
    """Raised for configuration validation errors."""

    pass


class ArcGISGroupInfo(TypedDict):
    """Types for `EXPORTER_ARCGIS_GROUP_INFO`."""

    name: str
    summary: str
    description_file: str
    thumbnail_file: str


# noinspection PyPep8Naming
class Config:
    """Application configuration."""

    def __init__(self, read_env: bool = True) -> None:
        """Create Config instance and load options from possible .env file."""
        self._app_prefix = "ASSETS_TRACKING_SERVICE_"
        self._app_package = "assets-tracking-service"
        self._safe_value = "[**REDACTED**]"

        self.env = Env()
        if read_env:
            self.env.read_env()

    def validate(self) -> None:  # noqa: C901
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

        if self.ENABLE_PROVIDER_RVDAS:
            try:
                _ = self.PROVIDER_RVDAS_URL
            except EnvError as e:
                msg = "PROVIDER_RVDAS_URL must be set."
                raise ConfigurationError(msg) from e

        if self.ENABLE_EXPORTER_ARCGIS:
            if not self.ENABLE_EXPORTER_DATA_CATALOGUE:
                msg = "ENABLE_EXPORTER_ARCGIS requires ENABLE_EXPORTER_DATA_CATALOGUE to be True."
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
                _ = self.EXPORTER_ARCGIS_BASE_ENDPOINT_PORTAL
            except EnvError as e:
                msg = "EXPORTER_ARCGIS_BASE_ENDPOINT_PORTAL must be set."
                raise ConfigurationError(msg) from e
            try:
                _ = self.EXPORTER_ARCGIS_BASE_ENDPOINT_SERVER
            except EnvError as e:
                msg = "EXPORTER_ARCGIS_BASE_ENDPOINT_SERVER must be set."
                raise ConfigurationError(msg) from e

        if self.ENABLE_EXPORTER_DATA_CATALOGUE:
            try:
                _ = self.EXPORTER_DATA_CATALOGUE_OUTPUT_PATH
            except EnvError as e:
                msg = "EXPORTER_DATA_CATALOGUE_OUTPUT_PATH must be set."
                raise ConfigurationError(msg) from e

            try:
                _ = self.EXPORTER_DATA_CATALOGUE_AWS_ACCESS_ID
            except EnvError as e:
                msg = "EXPORTER_DATA_CATALOGUE_AWS_ACCESS_ID must be set."
                raise ConfigurationError(msg) from e

            try:
                _ = self.EXPORTER_DATA_CATALOGUE_AWS_ACCESS_SECRET
            except EnvError as e:
                msg = "EXPORTER_DATA_CATALOGUE_AWS_ACCESS_SECRET must be set."
                raise ConfigurationError(msg) from e

            try:
                _ = self.EXPORTER_DATA_CATALOGUE_AWS_S3_BUCKET
            except EnvError as e:
                msg = "EXPORTER_DATA_CATALOGUE_AWS_S3_BUCKET must be set."
                raise ConfigurationError(msg) from e

            try:
                _ = self.EXPORTER_DATA_CATALOGUE_ITEM_CONTACT_ENDPOINT
            except EnvError as e:
                msg = "EXPORTER_DATA_CATALOGUE_ITEM_CONTACT_ENDPOINT must be set."
                raise ConfigurationError(msg) from e

            if (
                Path(self.EXPORTER_DATA_CATALOGUE_OUTPUT_PATH).exists()
                and not Path(self.EXPORTER_DATA_CATALOGUE_OUTPUT_PATH).is_dir()
            ):
                msg = "EXPORTER_DATA_CATALOGUE_OUTPUT_PATH must be a directory."
                raise ConfigurationError(msg)

    class ConfigDumpSafe(TypedDict):
        """Types for `dumps_safe`."""

        VERSION: str
        LOG_LEVEL: int
        LOG_LEVEL_NAME: str
        DB_DSN: str
        SENTRY_DSN: str
        ENABLE_FEATURE_SENTRY: bool
        SENTRY_ENVIRONMENT: str
        SENTRY_MONITOR_CONFIG: dict[str, dict]
        ENABLE_PROVIDER_GEOTAB: bool
        ENABLE_PROVIDER_AIRCRAFT_TRACKING: bool
        ENABLE_PROVIDER_RVDAS: bool
        ENABLED_PROVIDERS: list[str]
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
        PROVIDER_RVDAS_URL: str
        EXPORTER_ARCGIS_USERNAME: str
        EXPORTER_ARCGIS_PASSWORD: str
        EXPORTER_ARCGIS_BASE_ENDPOINT_PORTAL: str
        EXPORTER_ARCGIS_BASE_ENDPOINT_SERVER: str
        EXPORTER_ARCGIS_FOLDER_NAME: str
        EXPORTER_ARCGIS_GROUP_INFO: ArcGISGroupInfo
        EXPORTER_DATA_CATALOGUE_OUTPUT_PATH: str
        EXPORTER_DATA_CATALOGUE_EMBEDDED_MAPS_ENDPOINT: str
        EXPORTER_DATA_CATALOGUE_ITEM_CONTACT_ENDPOINT: str
        EXPORTER_DATA_CATALOGUE_AWS_S3_BUCKET: str
        EXPORTER_DATA_CATALOGUE_AWS_ACCESS_ID: str
        EXPORTER_DATA_CATALOGUE_AWS_ACCESS_SECRET: str
        EXPORTER_DATA_CATALOGUE_SENTRY_SRC: str
        EXPORTER_DATA_CATALOGUE_PLAUSIBLE_DOMAIN: str

    def dumps_safe(self) -> ConfigDumpSafe:
        """Dump config for output to the user with sensitive data redacted."""
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
            "ENABLE_PROVIDER_RVDAS": self.ENABLE_PROVIDER_RVDAS,
            "ENABLED_PROVIDERS": self.ENABLED_PROVIDERS,
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
            "PROVIDER_RVDAS_URL": self.PROVIDER_RVDAS_URL,
            "EXPORTER_ARCGIS_USERNAME": self.EXPORTER_ARCGIS_USERNAME,
            "EXPORTER_ARCGIS_PASSWORD": self.EXPORTER_ARCGIS_PASSWORD_SAFE,
            "EXPORTER_ARCGIS_BASE_ENDPOINT_PORTAL": self.EXPORTER_ARCGIS_BASE_ENDPOINT_PORTAL,
            "EXPORTER_ARCGIS_BASE_ENDPOINT_SERVER": self.EXPORTER_ARCGIS_BASE_ENDPOINT_SERVER,
            "EXPORTER_ARCGIS_FOLDER_NAME": self.EXPORTER_ARCGIS_FOLDER_NAME,
            "EXPORTER_ARCGIS_GROUP_INFO": self.EXPORTER_ARCGIS_GROUP_INFO,
            "EXPORTER_DATA_CATALOGUE_OUTPUT_PATH": str(self.EXPORTER_DATA_CATALOGUE_OUTPUT_PATH.resolve()),
            "EXPORTER_DATA_CATALOGUE_EMBEDDED_MAPS_ENDPOINT": self.EXPORTER_DATA_CATALOGUE_EMBEDDED_MAPS_ENDPOINT,
            "EXPORTER_DATA_CATALOGUE_ITEM_CONTACT_ENDPOINT": self.EXPORTER_DATA_CATALOGUE_ITEM_CONTACT_ENDPOINT,
            "EXPORTER_DATA_CATALOGUE_AWS_S3_BUCKET": self.EXPORTER_DATA_CATALOGUE_AWS_S3_BUCKET,
            "EXPORTER_DATA_CATALOGUE_AWS_ACCESS_ID": self.EXPORTER_DATA_CATALOGUE_AWS_ACCESS_ID,
            "EXPORTER_DATA_CATALOGUE_AWS_ACCESS_SECRET": self.EXPORTER_DATA_CATALOGUE_AWS_ACCESS_SECRET_SAFE,
            "EXPORTER_DATA_CATALOGUE_SENTRY_SRC": self.EXPORTER_DATA_CATALOGUE_SENTRY_SRC,
            "EXPORTER_DATA_CATALOGUE_PLAUSIBLE_DOMAIN": self.EXPORTER_DATA_CATALOGUE_PLAUSIBLE_DOMAIN,
        }

    @property
    def VERSION(self) -> str:
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
    def LOG_LEVEL_NAME(self) -> str:
        """Logging level name."""
        return logging.getLevelName(self.LOG_LEVEL)

    @property
    def DB_DSN(self) -> str:
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
    def DB_DSN_SAFE(self) -> str:
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
    def ENABLE_PROVIDER_GEOTAB(self) -> bool:
        """Controls whether Geotab provider is used."""
        with self.env.prefixed(self._app_prefix):
            return self.env.bool("ENABLE_PROVIDER_GEOTAB", True)

    @property
    def ENABLE_PROVIDER_AIRCRAFT_TRACKING(self) -> bool:
        """Controls whether Aircraft Tracking provider is used."""
        with self.env.prefixed(self._app_prefix):
            return self.env.bool("ENABLE_PROVIDER_AIRCRAFT_TRACKING", True)

    @property
    def ENABLE_PROVIDER_RVDAS(self) -> bool:
        """Controls whether RVDAS provider is used."""
        with self.env.prefixed(self._app_prefix):
            return self.env.bool("ENABLE_PROVIDER_RVDAS", True)

    @property
    def ENABLED_PROVIDERS(self) -> list[str]:
        """List of enabled providers."""
        providers = []

        if self.ENABLE_PROVIDER_GEOTAB:
            providers.append("geotab")
        if self.ENABLE_PROVIDER_AIRCRAFT_TRACKING:
            providers.append("aircraft_tracking")
        if self.ENABLE_PROVIDER_RVDAS:
            providers.append("rvdas")

        return providers

    @property
    def ENABLE_EXPORTER_ARCGIS(self) -> bool:
        """Controls whether ArcGIS exporter is used."""
        with self.env.prefixed(self._app_prefix):
            return self.env.bool("ENABLE_EXPORTER_ARCGIS", True)

    @property
    def ENABLE_EXPORTER_DATA_CATALOGUE(self) -> bool:
        """Controls whether Data Catalogue exporter is used."""
        with self.env.prefixed(self._app_prefix):
            return self.env.bool("ENABLE_EXPORTER_DATA_CATALOGUE", True)

    @property
    def ENABLED_EXPORTERS(self) -> list[str]:
        """List of enabled exporters."""
        exporters = []

        if self.ENABLE_EXPORTER_ARCGIS:
            exporters.append("arcgis")

        if self.ENABLE_EXPORTER_DATA_CATALOGUE:
            exporters.append("data_catalogue")

        return exporters

    @property
    def PROVIDER_GEOTAB_USERNAME(self) -> str:
        """Username for Geotab SDK."""
        with self.env.prefixed(self._app_prefix), self.env.prefixed("PROVIDER_GEOTAB_"):
            return self.env.str("USERNAME")

    @property
    def PROVIDER_GEOTAB_PASSWORD(self) -> str:
        """Password for Geotab SDK."""
        with self.env.prefixed(self._app_prefix), self.env.prefixed("PROVIDER_GEOTAB_"):
            return self.env.str("PASSWORD")

    @property
    def PROVIDER_GEOTAB_PASSWORD_SAFE(self) -> str:
        """PROVIDER_GEOTAB_PASSWORD with value redacted."""
        return self._safe_value

    @property
    def PROVIDER_GEOTAB_DATABASE(self) -> str:
        """Database name for Geotab SDK."""
        with self.env.prefixed(self._app_prefix), self.env.prefixed("PROVIDER_GEOTAB_"):
            return self.env.str("DATABASE")

    @property
    def PROVIDER_GEOTAB_GROUP_NVS_LO6_CODE_MAPPING(self) -> dict[str, str]:
        """
        Mapping of Geotab group names to NVS L06 codes.

        Needed as Geotab tracks multiple types of vehicle.

        See http://vocab.nerc.ac.uk/collection/L06/current/ for allowed codes and descriptions.
        """
        return {
            "b2795": "98",  # snowmobile
            "b2794": "31",  # ship, research vessel
            "b2796": "97",  # snowcat (Pistonbully)
        }

    @property
    def PROVIDER_AIRCRAFT_TRACKING_USERNAME(self) -> str:
        """Username for Aircraft Tracking provider."""
        with self.env.prefixed(self._app_prefix), self.env.prefixed("PROVIDER_AIRCRAFT_TRACKING_"):
            return self.env.str("USERNAME")

    @property
    def PROVIDER_AIRCRAFT_TRACKING_PASSWORD(self) -> str:
        """Password for Aircraft Tracking provider."""
        with self.env.prefixed(self._app_prefix), self.env.prefixed("PROVIDER_AIRCRAFT_TRACKING_"):
            return self.env.str("PASSWORD")

    @property
    def PROVIDER_AIRCRAFT_TRACKING_PASSWORD_SAFE(self) -> str:
        """PROVIDER_AIRCRAFT_TRACKING_PASSWORD with value redacted."""
        return self._safe_value

    @property
    def PROVIDER_AIRCRAFT_TRACKING_API_KEY(self) -> str:
        """API key for Aircraft Tracking provider."""
        with self.env.prefixed(self._app_prefix), self.env.prefixed("PROVIDER_AIRCRAFT_TRACKING_"):
            return self.env.str("API_KEY")

    @property
    def PROVIDER_AIRCRAFT_TRACKING_API_KEY_SAFE(self) -> str:
        """PROVIDER_AIRCRAFT_TRACKING_API_KEY with value redacted."""
        return self._safe_value

    @property
    def PROVIDER_RVDAS_URL(self) -> str:
        """
        URL for RVDAS provider.

        Must be items endpoint, as JSON, within a relevant collection in an OGC API - Features service.
        E.g. https://example.com/collections/x/items.json.
        """
        with self.env.prefixed(self._app_prefix), self.env.prefixed("PROVIDER_RVDAS_"):
            return self.env.str("URL")

    @property
    def EXPORTER_ARCGIS_USERNAME(self) -> str:
        """Username of user used to publish ArcGIS exporter outputs."""
        with self.env.prefixed(self._app_prefix), self.env.prefixed("EXPORTER_ARCGIS_"):
            return self.env.str("USERNAME")

    @property
    def EXPORTER_ARCGIS_PASSWORD(self) -> str:
        """Password of user used to publish ArcGIS exporter outputs."""
        with self.env.prefixed(self._app_prefix), self.env.prefixed("EXPORTER_ARCGIS_"):
            return self.env.str("PASSWORD")

    @property
    def EXPORTER_ARCGIS_PASSWORD_SAFE(self) -> str:
        """EXPORTER_ARCGIS_PASSWORD with value redacted."""
        return self._safe_value

    @property
    def EXPORTER_ARCGIS_BASE_ENDPOINT_PORTAL(self) -> str:
        """
        Base endpoint for ArcGIS items.

        E.g. 'https://bas.maps.arcgis.com' for 'https://bas.maps.arcgis.com/home/item.html?id=...'.
        """
        with self.env.prefixed(self._app_prefix), self.env.prefixed("EXPORTER_ARCGIS_"):
            return self.env.str("BASE_ENDPOINT_PORTAL")

    @property
    def EXPORTER_ARCGIS_BASE_ENDPOINT_SERVER(self) -> str:
        """
        Base endpoint for ArcGIS hosted services.

        E.g. 'https://services7.arcgis.com/tPxy1hrFDhJfZ0Mf/arcgis'
        for 'https://services7.arcgis.com/tPxy1hrFDhJfZ0Mf/arcgis/rest/services/.../FeatureServer'.
        """
        with self.env.prefixed(self._app_prefix), self.env.prefixed("EXPORTER_ARCGIS_"):
            return self.env.str("BASE_ENDPOINT_SERVER")

    @property
    def EXPORTER_ARCGIS_FOLDER_NAME(self) -> str:
        """
        Name of folder ArcGIS items will be stored in.

        Contained within ArcGIS user specified by `EXPORTER_ARCGIS_USERNAME`.
        """
        return "prj-assets-tracking-service"

    @property
    def EXPORTER_ARCGIS_GROUP_INFO(self) -> ArcGISGroupInfo:
        """Details for the group ArcGIS items will be published to."""
        return {
            "name": "Assets Tracking Service",
            "summary": "Resources pertaining to the BAS Assets Tracking Service, a service to track the location of BAS assets, including ships, aircraft, and vehicles.",
            "description_file": "description.md",
            "thumbnail_file": "thumbnail.png",
        }

    @property
    def EXPORTER_DATA_CATALOGUE_OUTPUT_PATH(self) -> Path:
        """Path to Data Catalogue site output."""
        with self.env.prefixed(self._app_prefix), self.env.prefixed("EXPORTER_DATA_CATALOGUE_"):
            return self.env.path("OUTPUT_PATH")

    @property
    def EXPORTER_DATA_CATALOGUE_EMBEDDED_MAPS_ENDPOINT(self) -> str:
        """Endpoint for Embedded Maps Service used to generate extent maps in item catalogue pages."""
        with self.env.prefixed(self._app_prefix), self.env.prefixed("EXPORTER_DATA_CATALOGUE_"):
            return self.env("EMBEDDED_MAPS_ENDPOINT", default="https://embedded-maps.data.bas.ac.uk/v1")

    @property
    def EXPORTER_DATA_CATALOGUE_ITEM_CONTACT_ENDPOINT(self) -> str:
        """Endpoint for Embedded Maps Service used to generate extent maps in item catalogue pages."""
        with self.env.prefixed(self._app_prefix), self.env.prefixed("EXPORTER_DATA_CATALOGUE_"):
            return self.env("ITEM_CONTACT_ENDPOINT")

    @property
    def EXPORTER_DATA_CATALOGUE_AWS_S3_BUCKET(self) -> str:
        """S3 bucket for published catalogue output."""
        with self.env.prefixed(self._app_prefix), self.env.prefixed("EXPORTER_DATA_CATALOGUE_"):
            return self.env("AWS_S3_BUCKET")

    @property
    def EXPORTER_DATA_CATALOGUE_AWS_ACCESS_ID(self) -> str:
        """ID for AWS IAM access key used to publish catalogue output to S3."""
        with self.env.prefixed(self._app_prefix), self.env.prefixed("EXPORTER_DATA_CATALOGUE_"):
            return self.env("AWS_ACCESS_ID")

    @property
    def EXPORTER_DATA_CATALOGUE_AWS_ACCESS_SECRET(self) -> str:
        """Secret for AWS IAM access key used to publish catalogue output to S3."""
        with self.env.prefixed(self._app_prefix), self.env.prefixed("EXPORTER_DATA_CATALOGUE_"):
            return self.env("AWS_ACCESS_SECRET")

    @property
    def EXPORTER_DATA_CATALOGUE_AWS_ACCESS_SECRET_SAFE(self) -> str:
        """EXPORTER_DATA_CATALOGUE_AWS_ACCESS_SECRET with value redacted."""
        return self._safe_value

    @property
    def EXPORTER_DATA_CATALOGUE_SENTRY_SRC(self) -> str:
        """Sentry dynamic CDN script."""
        with self.env.prefixed(self._app_prefix), self.env.prefixed("EXPORTER_DATA_CATALOGUE_"):
            return self.env("SENTRY_SRC")

    @property
    def EXPORTER_DATA_CATALOGUE_PLAUSIBLE_DOMAIN(self) -> str:
        """Plausible site/domain name."""
        with self.env.prefixed(self._app_prefix), self.env.prefixed("EXPORTER_DATA_CATALOGUE_"):
            return self.env("PLAUSIBLE_DOMAIN")
