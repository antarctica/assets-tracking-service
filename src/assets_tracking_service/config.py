from importlib.metadata import version
from typing import TypedDict

from environs import Env, EnvError
import dsnparse


class EditableDsn(dsnparse.ParseResult):
    """
    dsnparse result class to allow database (path) and password (secret) to be updated.
    """

    @property
    def database(self) -> str:
        return super().database

    @database.setter
    def database(self, value: str) -> None:
        self.fields["path"] = f"/{value}"

    @property
    def secret(self) -> str:
        return super().secret

    @secret.setter
    def secret(self, value: str) -> None:
        self.fields["password"] = value


class ConfigurationError(Exception):
    pass


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

    def validate(self) -> None:
        """
        Validate configuration.

        This validation is basic/limited. E.g. We check that the DSN is in a valid format, not that we can make a valid
        database connection.

        If invalid a ConfigurationError is raised.
        """
        try:
            _ = self.DB_DSN
        except EnvError as e:
            raise ConfigurationError("DB_DSN must be set.") from e
        except (ValueError, TypeError) as e:
            raise ConfigurationError("DB_DSN is invalid.") from e

        if self.ENABLE_PROVIDER_AIRCRAFT_TRACKING:
            try:
                _ = self.PROVIDER_AIRCRAFT_TRACKING_USERNAME
            except EnvError as e:
                raise ConfigurationError("PROVIDER_AIRCRAFT_TRACKING_USERNAME must be set.") from e
            try:
                _ = self.PROVIDER_AIRCRAFT_TRACKING_PASSWORD
            except EnvError as e:
                raise ConfigurationError("PROVIDER_AIRCRAFT_TRACKING_PASSWORD must be set.") from e
            try:
                _ = self.PROVIDER_AIRCRAFT_TRACKING_API_KEY
            except EnvError as e:
                raise ConfigurationError("PROVIDER_AIRCRAFT_TRACKING_API_KEY must be set.") from e

        if self.ENABLE_PROVIDER_GEOTAB:
            try:
                _ = self.PROVIDER_GEOTAB_USERNAME
            except EnvError as e:
                raise ConfigurationError("PROVIDER_GEOTAB_USERNAME must be set.") from e
            try:
                _ = self.PROVIDER_GEOTAB_PASSWORD
            except EnvError as e:
                raise ConfigurationError("PROVIDER_GEOTAB_PASSWORD must be set.") from e
            try:
                _ = self.PROVIDER_GEOTAB_DATABASE
            except EnvError as e:
                raise ConfigurationError("PROVIDER_GEOTAB_DATABASE must be set.") from e

    class ConfigDumpSafe(TypedDict):
        version: str
        db_dsn: str
        enable_provider_geotab: bool
        enable_provider_aircraft_tracking: bool
        enabled_providers: list[str]
        provider_geotab_username: str
        provider_geotab_password: str
        provider_geotab_database: str
        provider_geotab_group_nvs_l06_code_mapping: dict[str, str]
        provider_aircraft_tracking_username: str
        provider_aircraft_tracking_password: str
        provider_aircraft_tracking_api_key: str

    def dumps_safe(self) -> ConfigDumpSafe:
        """Dump config for output to the user with sensitive data redacted."""
        return {
            "version": self.version,
            "db_dsn": self.db_dsn_safe,
            "enable_provider_geotab": self.ENABLE_PROVIDER_GEOTAB,
            "enable_provider_aircraft_tracking": self.ENABLE_PROVIDER_AIRCRAFT_TRACKING,
            "enabled_providers": self.enabled_providers,
            "provider_geotab_username": self.PROVIDER_GEOTAB_USERNAME,
            "provider_geotab_password": self.provider_geotab_password_safe,
            "provider_geotab_database": self.PROVIDER_GEOTAB_DATABASE,
            "provider_geotab_group_nvs_l06_code_mapping": self.provider_geotab_group_nvs_l06_code_mapping,
            "provider_aircraft_tracking_username": self.PROVIDER_AIRCRAFT_TRACKING_USERNAME,
            "provider_aircraft_tracking_password": self.provider_aircraft_tracking_password_safe,
            "provider_aircraft_tracking_api_key": self.provider_aircraft_tracking_api_key_safe,
        }

    @property
    def version(self) -> str:
        """
        Application version.

        Read from package metadata.
        """
        return version(self._app_package)

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
    def db_dsn_safe(self) -> str:
        """DB_DSN with password redacted."""
        dsn_parsed = dsnparse.parse(self.DB_DSN, EditableDsn)
        dsn_parsed.secret = self._safe_value
        return dsn_parsed.geturl()

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
    def enabled_providers(self) -> list[str]:
        """List of enabled providers."""
        providers = []

        if self.ENABLE_PROVIDER_GEOTAB:
            providers.append("geotab")

        if self.ENABLE_PROVIDER_AIRCRAFT_TRACKING:
            providers.append("aircraft_tracking")

        return providers

    @property
    def PROVIDER_GEOTAB_USERNAME(self) -> str:
        """Username for Geotab SDK."""
        with self.env.prefixed(self._app_prefix):
            with self.env.prefixed("PROVIDER_GEOTAB_"):
                return self.env.str("USERNAME")

    @property
    def PROVIDER_GEOTAB_PASSWORD(self) -> str:
        """Password for Geotab SDK."""
        with self.env.prefixed(self._app_prefix):
            with self.env.prefixed("PROVIDER_GEOTAB_"):
                return self.env.str("PASSWORD")

    @property
    def provider_geotab_password_safe(self) -> str:
        """PROVIDER_GEOTAB_PASSWORD with value redacted."""
        return self._safe_value

    @property
    def PROVIDER_GEOTAB_DATABASE(self) -> str:
        """Database name for Geotab SDK."""
        with self.env.prefixed(self._app_prefix):
            with self.env.prefixed("PROVIDER_GEOTAB_"):
                return self.env.str("DATABASE")

    @property
    def provider_geotab_group_nvs_l06_code_mapping(self) -> dict[str, str]:
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
    def PROVIDER_AIRCRAFT_TRACKING_USERNAME(self) -> str:
        """Username for Aircraft Tracking provider."""
        with self.env.prefixed(self._app_prefix):
            with self.env.prefixed("PROVIDER_AIRCRAFT_TRACKING_"):
                return self.env.str("USERNAME")

    @property
    def PROVIDER_AIRCRAFT_TRACKING_PASSWORD(self) -> str:
        """Password for Aircraft Tracking provider."""
        with self.env.prefixed(self._app_prefix):
            with self.env.prefixed("PROVIDER_AIRCRAFT_TRACKING_"):
                return self.env.str("PASSWORD")

    @property
    def provider_aircraft_tracking_password_safe(self) -> str:
        """PROVIDER_AIRCRAFT_TRACKING_PASSWORD with value redacted."""
        return self._safe_value

    @property
    def PROVIDER_AIRCRAFT_TRACKING_API_KEY(self) -> str:
        """API key for Aircraft Tracking provider."""
        with self.env.prefixed(self._app_prefix):
            with self.env.prefixed("PROVIDER_AIRCRAFT_TRACKING_"):
                return self.env.str("API_KEY")

    @property
    def provider_aircraft_tracking_api_key_safe(self) -> str:
        """PROVIDER_AIRCRAFT_TRACKING_API_KEY with value redacted."""
        return self._safe_value
