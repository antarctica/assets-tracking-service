import os
from importlib.metadata import version
from pathlib import Path
from typing import Any, Self

import dsnparse
import pytest

from assets_tracking_service.config import Config, ConfigurationError, EditableDsn


class TestEditableDsn:
    """Test custom dsnparse.ParseResult class."""

    @pytest.mark.cov()
    def test_database(self: Self):
        """Can get database property."""
        db = "assets_tracking_test"
        dsn = f"postgresql://test:password@localhost:5432/{db}"
        dsn_parsed = dsnparse.parse(dsn, EditableDsn)

        assert dsn_parsed.database == db

    @pytest.mark.cov()
    def test_secret(self: Self):
        """Can get secret property."""
        password = "password"  # noqa: S105
        dsn = f"postgresql://test:{password}@localhost:5432/assets_tracking_test"
        dsn_parsed = dsnparse.parse(dsn, EditableDsn)

        assert dsn_parsed.secret == password


class TestConfig:
    """Test app config."""

    @staticmethod
    def _set_envs(envs: dict) -> dict:
        envs_bck = {}

        for env in envs:
            # backup environment variable if set
            value = os.environ.get(env, None)
            if value is not None:
                envs_bck[env] = value
            # unset environment variable if set
            if env in os.environ:
                del os.environ[env]
            # set environment variable to test value
            if envs[env] is not None:
                os.environ[env] = envs[env]

        return envs_bck

    @staticmethod
    def _unset_envs(envs: dict, envs_bck: dict) -> None:
        # unset environment variable
        for env in envs:
            if env in os.environ:
                del os.environ[env]
        # restore environment variables if set outside of test
        for env in envs:
            if env in envs_bck:
                os.environ[env] = str(envs_bck[env])

    def test_db_dsn(self: Self):
        """
        Gets DB DSN from environment.

        This has previously proved unreliable in CI so has a dedicated test we can run.
        """
        config = Config()

        assert "postgresql://" in config.DB_DSN

        config.validate()

    def test_db_dsn_explicit(self: Self):
        """Gets DB DSN when set explicitly as part of test."""
        dsn = "postgresql://test:password@localhost:5432/assets_tracking_dev"
        envs = {"ASSETS_TRACKING_SERVICE_DB_DSN": dsn, "ASSETS_TRACKING_SERVICE_DB_DATABASE": None}
        envs_bck = self._set_envs(envs)

        config = Config()
        assert dsn == config.DB_DSN

        self._unset_envs(envs, envs_bck)

    def test_db_dsn_app_db(self: Self):
        """Gets DB DSN with overridden database name."""
        dsn = "postgresql://test:password@localhost:5432/assets-tracking-foo"
        name = "assets-tracking-bar"

        envs = {"ASSETS_TRACKING_SERVICE_DB_DSN": dsn, "ASSETS_TRACKING_SERVICE_DB_DATABASE": name}
        envs_bck = self._set_envs(envs)

        config = Config()
        assert dsn.replace("assets-tracking-foo", name) == config.DB_DSN

        self._unset_envs(envs, envs_bck)

    def test_db_safe(self: Self):
        """Gets DB DSN with password redacted."""
        password = "password"  # noqa: S105
        dsn = f"postgresql://test:{password}@localhost:5432/assets_tracking_test"
        safe_dsn = dsn.replace(password, "[**REDACTED**]")

        envs = {"ASSETS_TRACKING_SERVICE_DB_DSN": dsn}
        envs_bck = self._set_envs(envs)

        config = Config()
        assert dsn == config.DB_DSN
        assert safe_dsn == config.DB_DSN_SAFE

        self._unset_envs(envs, envs_bck)

    def test_version(self: Self):
        """Version is read from package metadata."""
        config = Config()
        assert version("assets-tracking-service") == config.VERSION

    def test_dumps_safe(self: Self, fx_package_version: str, fx_config: Config):
        """Config can be exported to a dict with sensitive values redacted."""
        redacted_value = "[**REDACTED**]"

        expected: fx_config.ConfigDumpSafe = {
            "VERSION": fx_package_version,
            "LOG_LEVEL": 20,
            "LOG_LEVEL_NAME": "INFO",
            "DB_DSN": fx_config.DB_DSN_SAFE,
            "SENTRY_DSN": fx_config.SENTRY_DSN,
            "ENABLE_FEATURE_SENTRY": False,  # would be True by default but Sentry disabled in tests
            "SENTRY_ENVIRONMENT": "development",
            "SENTRY_MONITOR_CONFIG": fx_config.SENTRY_MONITOR_CONFIG,
            "ENABLE_PROVIDER_AIRCRAFT_TRACKING": True,
            "ENABLE_PROVIDER_GEOTAB": True,
            "ENABLED_PROVIDERS": ["aircraft_tracking", "geotab"],
            "PROVIDER_AIRCRAFT_TRACKING_API_KEY": redacted_value,
            "PROVIDER_AIRCRAFT_TRACKING_PASSWORD": redacted_value,
            "PROVIDER_AIRCRAFT_TRACKING_USERNAME": "x",
            "PROVIDER_GEOTAB_DATABASE": "x",
            "PROVIDER_GEOTAB_GROUP_NVS_LO6_CODE_MAPPING": fx_config.PROVIDER_GEOTAB_GROUP_NVS_LO6_CODE_MAPPING,
            "PROVIDER_GEOTAB_PASSWORD": redacted_value,
            "PROVIDER_GEOTAB_USERNAME": "x",
            "ENABLE_EXPORTER_ARCGIS": True,
            "ENABLE_EXPORTER_GEOJSON": True,
            "ENABLE_EXPORTER_DATA_CATALOGUE": True,
            "ENABLED_EXPORTERS": ["arcgis", "geojson", "data_catalogue"],
            "EXPORTER_ARCGIS_USERNAME": "x",
            "EXPORTER_ARCGIS_PASSWORD": redacted_value,
            "EXPORTER_ARCGIS_BASE_ENDPOINT_PORTAL": "https://example.com",
            "EXPORTER_ARCGIS_BASE_ENDPOINT_SERVER": "https://example.com/arcgis",
            "EXPORTER_GEOJSON_OUTPUT_PATH": str(fx_config.EXPORTER_GEOJSON_OUTPUT_PATH.resolve()),
            "EXPORTER_DATA_CATALOGUE_OUTPUT_PATH": str(fx_config.EXPORTER_DATA_CATALOGUE_OUTPUT_PATH.resolve()),
            "EXPORTER_DATA_CATALOGUE_COLLECTION_RECORD_ID": "125d6ae8-0b9a-4c89-88e2-f3ec59723e52",
        }

        output = fx_config.dumps_safe()
        assert output == expected
        assert redacted_value in output["DB_DSN"]
        assert "export.geojson" in output["EXPORTER_GEOJSON_OUTPUT_PATH"]

    def test_validate(self: Self, fx_config: Config):
        """Valid configuration is ok."""
        fx_config.validate()

    def test_validate_invalid_logging_level(self: Self):
        """Validation fails where logging level is invalid."""
        envs = {"ASSETS_TRACKING_SERVICE_LOG_LEVEL": "INVALID"}
        envs_bck = self._set_envs(envs)

        config = Config(read_env=False)

        with pytest.raises(ConfigurationError):
            _ = config.LOG_LEVEL

        self._unset_envs(envs, envs_bck)

    def test_validate_missing_db_dsn(self: Self):
        """Validation fails where DB DSN is missing."""
        envs = {"ASSETS_TRACKING_SERVICE_DB_DSN": None}
        envs_bck = self._set_envs(envs)

        config = Config(read_env=False)

        with pytest.raises(ConfigurationError):
            config.validate()

        self._unset_envs(envs, envs_bck)

    def test_validate_invalid_db_dsn(self: Self):
        """Validation fails where DB DSN is invalid."""
        envs = {"ASSETS_TRACKING_SERVICE_DB_DSN": "postgresql://"}
        envs_bck = self._set_envs(envs)

        config = Config(read_env=False)

        with pytest.raises(ConfigurationError):
            config.validate()

        self._unset_envs(envs, envs_bck)

    def test_validate_invalid_catalogue_path(self):
        """Validation fails where catalogue path is invalid."""
        envs = {"ASSETS_TRACKING_SERVICE_EXPORTER_DATA_CATALOGUE_OUTPUT_PATH": str(Path(__file__).resolve())}
        envs_bck = self._set_envs(envs)

        config = Config(read_env=False)

        with pytest.raises(ConfigurationError):
            config.validate()

        self._unset_envs(envs, envs_bck)

    @pytest.mark.parametrize(
        ("provider_name", "input_value", "expected_value"),
        [
            ("AIRCRAFT_TRACKING", "true", True),
            ("AIRCRAFT_TRACKING", "false", False),
            ("AIRCRAFT_TRACKING", None, True),
            ("GEOTAB", "true", True),
            ("GEOTAB", "false", False),
            ("GEOTAB", None, True),
        ],
    )
    def test_enable_provider(self: Self, provider_name: str, input_value: str, expected_value: bool):
        """Providers are correctly enabled by default and with explicit values."""
        envs = {f"ASSETS_TRACKING_SERVICE_ENABLE_PROVIDER_{provider_name}": input_value}
        envs_bck = self._set_envs(envs)

        config = Config()
        assert getattr(config, f"ENABLE_PROVIDER_{provider_name}") == expected_value

        self._unset_envs(envs, envs_bck)

    @pytest.mark.parametrize(
        ("envs", "expected"),
        [
            (
                {
                    "ASSETS_TRACKING_SERVICE_ENABLE_PROVIDER_AIRCRAFT_TRACKING": "true",
                    "ASSETS_TRACKING_SERVICE_ENABLE_PROVIDER_GEOTAB": "true",
                },
                ["aircraft_tracking", "geotab"],
            ),
            (
                {
                    "ASSETS_TRACKING_SERVICE_ENABLE_PROVIDER_AIRCRAFT_TRACKING": "true",
                    "ASSETS_TRACKING_SERVICE_ENABLE_PROVIDER_GEOTAB": "false",
                },
                ["aircraft_tracking"],
            ),
            (
                {
                    "ASSETS_TRACKING_SERVICE_ENABLE_PROVIDER_AIRCRAFT_TRACKING": "false",
                    "ASSETS_TRACKING_SERVICE_ENABLE_PROVIDER_GEOTAB": "true",
                },
                ["geotab"],
            ),
            (
                {
                    "ASSETS_TRACKING_SERVICE_ENABLE_PROVIDER_AIRCRAFT_TRACKING": "false",
                    "ASSETS_TRACKING_SERVICE_ENABLE_PROVIDER_GEOTAB": "false",
                },
                [],
            ),
        ],
    )
    def test_enabled_providers(self: Self, envs: dict[str, str], expected: list[str]):
        """Enabled providers derived property is correctly constructed."""
        envs_bck = self._set_envs(envs)

        config = Config()
        assert expected == config.ENABLED_PROVIDERS

        self._unset_envs(envs, envs_bck)

    @pytest.mark.parametrize(
        ("exporter_name", "input_value", "expected_value"),
        [
            ("ARCGIS", "true", True),
            ("ARCGIS", "false", False),
            ("ARCGIS", None, True),
            ("GEOJSON", "true", True),
            ("GEOJSON", "false", False),
            ("GEOJSON", None, True),
            ("DATA_CATALOGUE", "true", True),
            ("DATA_CATALOGUE", "false", False),
            ("DATA_CATALOGUE", None, True),
        ],
    )
    def test_enable_exporter(self: Self, exporter_name: str, input_value: str, expected_value: bool):
        """Exporters are correctly enabled by default and with explicit values."""
        envs = {f"ASSETS_TRACKING_SERVICE_ENABLE_EXPORTER_{exporter_name}": input_value}
        envs_bck = self._set_envs(envs)

        config = Config()
        assert getattr(config, f"ENABLE_EXPORTER_{exporter_name}") == expected_value

        self._unset_envs(envs, envs_bck)

    @pytest.mark.parametrize(
        ("envs", "expected"),
        [
            (
                {
                    "ASSETS_TRACKING_SERVICE_ENABLE_EXPORTER_ARCGIS": "true",
                    "ASSETS_TRACKING_SERVICE_ENABLE_EXPORTER_GEOJSON": "true",
                    "ASSETS_TRACKING_SERVICE_ENABLE_EXPORTER_DATA_CATALOGUE": "true",
                },
                ["arcgis", "geojson", "data_catalogue"],
            ),
            (
                {
                    "ASSETS_TRACKING_SERVICE_ENABLE_EXPORTER_ARCGIS": "true",
                    "ASSETS_TRACKING_SERVICE_ENABLE_EXPORTER_GEOJSON": "false",
                    "ASSETS_TRACKING_SERVICE_ENABLE_EXPORTER_DATA_CATALOGUE": "false",
                },
                ["arcgis"],
            ),
            (
                {
                    "ASSETS_TRACKING_SERVICE_ENABLE_EXPORTER_ARCGIS": "false",
                    "ASSETS_TRACKING_SERVICE_ENABLE_EXPORTER_GEOJSON": "true",
                    "ASSETS_TRACKING_SERVICE_ENABLE_EXPORTER_DATA_CATALOGUE": "false",
                },
                ["geojson"],
            ),
            (
                {
                    "ASSETS_TRACKING_SERVICE_ENABLE_EXPORTER_ARCGIS": "false",
                    "ASSETS_TRACKING_SERVICE_ENABLE_EXPORTER_GEOJSON": "false",
                    "ASSETS_TRACKING_SERVICE_ENABLE_EXPORTER_DATA_CATALOGUE": "true",
                },
                ["data_catalogue"],
            ),
            (
                {
                    "ASSETS_TRACKING_SERVICE_ENABLE_EXPORTER_ARCGIS": "true",
                    "ASSETS_TRACKING_SERVICE_ENABLE_EXPORTER_GEOJSON": "true",
                    "ASSETS_TRACKING_SERVICE_ENABLE_EXPORTER_DATA_CATALOGUE": "false",
                },
                ["arcgis", "geojson"],
            ),
            (
                {
                    "ASSETS_TRACKING_SERVICE_ENABLE_EXPORTER_ARCGIS": "true",
                    "ASSETS_TRACKING_SERVICE_ENABLE_EXPORTER_GEOJSON": "false",
                    "ASSETS_TRACKING_SERVICE_ENABLE_EXPORTER_DATA_CATALOGUE": "true",
                },
                ["arcgis", "data_catalogue"],
            ),
            (
                {
                    "ASSETS_TRACKING_SERVICE_ENABLE_EXPORTER_ARCGIS": "false",
                    "ASSETS_TRACKING_SERVICE_ENABLE_EXPORTER_GEOJSON": "true",
                    "ASSETS_TRACKING_SERVICE_ENABLE_EXPORTER_DATA_CATALOGUE": "true",
                },
                ["geojson", "data_catalogue"],
            ),
            (
                {
                    "ASSETS_TRACKING_SERVICE_ENABLE_EXPORTER_ARCGIS": "false",
                    "ASSETS_TRACKING_SERVICE_ENABLE_EXPORTER_GEOJSON": "false",
                    "ASSETS_TRACKING_SERVICE_ENABLE_EXPORTER_DATA_CATALOGUE": "false",
                },
                [],
            ),
        ],
    )
    def test_enabled_exporters(self: Self, envs: dict[str, str], expected: list[str]):
        """Enabled exporters derived property is correctly constructed."""
        envs_bck = self._set_envs(envs)

        config = Config()
        assert expected == config.ENABLED_EXPORTERS

        self._unset_envs(envs, envs_bck)

    @pytest.mark.parametrize(
        ("property_name", "expected", "sensitive"),
        [
            ("PROVIDER_AIRCRAFT_TRACKING_USERNAME", "x", False),
            ("PROVIDER_AIRCRAFT_TRACKING_PASSWORD", "x", True),
            ("PROVIDER_AIRCRAFT_TRACKING_API_KEY", "x", True),
            ("PROVIDER_GEOTAB_USERNAME", "x", False),
            ("PROVIDER_GEOTAB_PASSWORD", "x", True),
            ("PROVIDER_GEOTAB_DATABASE", "x", False),
            ("EXPORTER_ARCGIS_USERNAME", "x", False),
            ("EXPORTER_ARCGIS_PASSWORD", "x", True),
            ("EXPORTER_ARCGIS_BASE_ENDPOINT_PORTAL", "https://example.com", False),
            ("EXPORTER_ARCGIS_BASE_ENDPOINT_SERVER", "https://example.com/arcgis", False),
            ("EXPORTER_GEOJSON_OUTPUT_PATH", Path("export.geojson"), False),
            ("EXPORTER_DATA_CATALOGUE_OUTPUT_PATH", Path("records"), False),
        ],
    )
    def test_configurable_property(self: Self, property_name: str, expected: Any, sensitive: bool):
        """Configurable properties can be accessed."""
        envs = {f"ASSETS_TRACKING_SERVICE_{property_name}": str(expected)}
        envs_bck = self._set_envs(envs)

        config = Config()
        assert getattr(config, property_name) == expected

        if sensitive:
            assert getattr(config, f"{property_name}_SAFE") == "[**REDACTED**]"

        self._unset_envs(envs, envs_bck)

    @pytest.mark.cov()
    def test_provider_geotab_group_nvs_l06_code_mapping(self: Self):
        """For completeness."""
        config = Config()
        assert isinstance(config.PROVIDER_GEOTAB_GROUP_NVS_LO6_CODE_MAPPING, dict)

    @pytest.mark.cov()
    def test_validate_providers_disabled(self: Self):
        """Needed to satisfy coverage that config is valid when all providers can be disabled."""
        envs = {
            "ASSETS_TRACKING_SERVICE_ENABLE_PROVIDER_AIRCRAFT_TRACKING": "false",
            "ASSETS_TRACKING_SERVICE_ENABLE_PROVIDER_GEOTAB": "false",
        }
        envs_bck = self._set_envs(envs)

        config = Config()
        config.validate()

        self._unset_envs(envs, envs_bck)

    @pytest.mark.cov()
    def test_validate_exporters_disabled(self: Self):
        """Needed to satisfy coverage that config is valid when all exporters can be disabled."""
        envs = {
            "ASSETS_TRACKING_SERVICE_ENABLE_EXPORTER_ARCGIS": "false",
            "ASSETS_TRACKING_SERVICE_ENABLE_EXPORTER_GEOJSON": "false",
            "ASSETS_TRACKING_SERVICE_ENABLE_EXPORTER_DATA_CATALOGUE": "false",
        }
        envs_bck = self._set_envs(envs)

        config = Config()
        config.validate()

        self._unset_envs(envs, envs_bck)

    @pytest.mark.parametrize(
        "envs",
        [
            (
                {
                    "ASSETS_TRACKING_SERVICE_ENABLE_PROVIDER_AIRCRAFT_TRACKING": "true",
                    "ASSETS_TRACKING_SERVICE_PROVIDER_AIRCRAFT_TRACKING_USERNAME": None,
                    "ASSETS_TRACKING_SERVICE_PROVIDER_AIRCRAFT_TRACKING_PASSWORD": "x",
                    "ASSETS_TRACKING_SERVICE_PROVIDER_AIRCRAFT_TRACKING_API_KEY": "x",
                }
            ),
            (
                {
                    "ASSETS_TRACKING_SERVICE_ENABLE_PROVIDER_AIRCRAFT_TRACKING": "true",
                    "ASSETS_TRACKING_SERVICE_PROVIDER_AIRCRAFT_TRACKING_USERNAME": "x",
                    "ASSETS_TRACKING_SERVICE_PROVIDER_AIRCRAFT_TRACKING_PASSWORD": None,
                    "ASSETS_TRACKING_SERVICE_PROVIDER_AIRCRAFT_TRACKING_API_KEY": "x",
                }
            ),
            (
                {
                    "ASSETS_TRACKING_SERVICE_ENABLE_PROVIDER_AIRCRAFT_TRACKING": "true",
                    "ASSETS_TRACKING_SERVICE_PROVIDER_AIRCRAFT_TRACKING_USERNAME": "x",
                    "ASSETS_TRACKING_SERVICE_PROVIDER_AIRCRAFT_TRACKING_PASSWORD": "x",
                    "ASSETS_TRACKING_SERVICE_PROVIDER_AIRCRAFT_TRACKING_API_KEY": None,
                }
            ),
            (
                {
                    "ASSETS_TRACKING_SERVICE_ENABLE_PROVIDER_GEOTAB": "true",
                    "ASSETS_TRACKING_SERVICE_PROVIDER_GEOTAB_USERNAME": None,
                    "ASSETS_TRACKING_SERVICE_PROVIDER_GEOTAB_PASSWORD": "x",
                    "ASSETS_TRACKING_SERVICE_PROVIDER_GEOTAB_DATABASE": "x",
                }
            ),
            (
                {
                    "ASSETS_TRACKING_SERVICE_ENABLE_PROVIDER_GEOTAB": "true",
                    "ASSETS_TRACKING_SERVICE_PROVIDER_GEOTAB_USERNAME": "x",
                    "ASSETS_TRACKING_SERVICE_PROVIDER_GEOTAB_PASSWORD": None,
                    "ASSETS_TRACKING_SERVICE_PROVIDER_GEOTAB_DATABASE": "x",
                }
            ),
            (
                {
                    "ASSETS_TRACKING_SERVICE_ENABLE_PROVIDER_GEOTAB": "true",
                    "ASSETS_TRACKING_SERVICE_PROVIDER_GEOTAB_USERNAME": "x",
                    "ASSETS_TRACKING_SERVICE_PROVIDER_GEOTAB_PASSWORD": "x",
                    "ASSETS_TRACKING_SERVICE_PROVIDER_GEOTAB_DATABASE": None,
                }
            ),
            (
                {
                    "ASSETS_TRACKING_SERVICE_ENABLE_EXPORTER_ARCGIS": "true",
                    "ASSETS_TRACKING_SERVICE_EXPORTER_ARCGIS_USERNAME": None,
                    "ASSETS_TRACKING_SERVICE_EXPORTER_ARCGIS_PASSWORD": "x",
                    "ASSETS_TRACKING_SERVICE_EXPORTER_ARCGIS_BASE_ENDPOINT_PORTAL": "https://example.com",
                    "ASSETS_TRACKING_SERVICE_EXPORTER_ARCGIS_BASE_ENDPOINT_SERVER": "https://example.com/arcgis",
                }
            ),
            (
                {
                    "ASSETS_TRACKING_SERVICE_ENABLE_EXPORTER_ARCGIS": "true",
                    "ASSETS_TRACKING_SERVICE_EXPORTER_ARCGIS_USERNAME": "x",
                    "ASSETS_TRACKING_SERVICE_EXPORTER_ARCGIS_PASSWORD": None,
                    "ASSETS_TRACKING_SERVICE_EXPORTER_ARCGIS_BASE_ENDPOINT_PORTAL": "https://example.com",
                    "ASSETS_TRACKING_SERVICE_EXPORTER_ARCGIS_BASE_ENDPOINT_SERVER": "https://example.com/arcgis",
                }
            ),
            (
                {
                    "ASSETS_TRACKING_SERVICE_ENABLE_EXPORTER_ARCGIS": "true",
                    "ASSETS_TRACKING_SERVICE_EXPORTER_ARCGIS_USERNAME": "x",
                    "ASSETS_TRACKING_SERVICE_EXPORTER_ARCGIS_PASSWORD": "x",
                    "ASSETS_TRACKING_SERVICE_EXPORTER_ARCGIS_BASE_ENDPOINT_PORTAL": None,
                    "ASSETS_TRACKING_SERVICE_EXPORTER_ARCGIS_BASE_ENDPOINT_SERVER": "https://example.com/arcgis",
                }
            ),
            (
                {
                    "ASSETS_TRACKING_SERVICE_ENABLE_EXPORTER_ARCGIS": "true",
                    "ASSETS_TRACKING_SERVICE_EXPORTER_ARCGIS_USERNAME": "x",
                    "ASSETS_TRACKING_SERVICE_EXPORTER_ARCGIS_PASSWORD": "x",
                    "ASSETS_TRACKING_SERVICE_EXPORTER_ARCGIS_BASE_ENDPOINT_PORTAL": "https://example.com",
                    "ASSETS_TRACKING_SERVICE_EXPORTER_ARCGIS_BASE_ENDPOINT_SERVER": None,
                }
            ),
            (
                {
                    "ASSETS_TRACKING_SERVICE_ENABLE_EXPORTER_GEOJSON": "true",
                    "ASSETS_TRACKING_SERVICE_EXPORTER_GEOJSON_OUTPUT_PATH": None,
                }
            ),
            (
                {
                    "ASSETS_TRACKING_SERVICE_ENABLE_EXPORTER_DATA_CATALOGUE": "true",
                    "ASSETS_TRACKING_SERVICE_EXPORTER_DATA_CATALOGUE_OUTPUT_PATH": None,
                }
            ),
        ],
    )
    def test_validate_missing_required_option(self: Self, envs: dict):
        """
        Validation fails where a required provider or exporter config option is missing.

        Note: The `ASSETS_TRACKING_SERVICE_DB_DSN` option is trickier to check and covered by a specific test.
        """
        static_env = {"ASSETS_TRACKING_SERVICE_DB_DSN": "postgresql://postgres@localhost:5432/assets_tracking_test"}
        envs = {**static_env, **envs}
        envs_bck = self._set_envs(envs)

        config = Config(read_env=False)

        with pytest.raises(ConfigurationError):
            config.validate()

        self._unset_envs(envs, envs_bck)

    @pytest.mark.parametrize(
        "envs",
        [
            {
                "ASSETS_TRACKING_SERVICE_ENABLE_EXPORTER_DATA_CATALOGUE": "false",
                "ASSETS_TRACKING_SERVICE_ENABLE_EXPORTER_ARCGIS": "true",
            },
        ],
    )
    def test_validate_exporter_disabled_dependency(self: Self, envs: dict[str, str]):
        """Validation fails where an exporter that another exporter depends on is disabled."""
        envs_bck = self._set_envs(envs)

        config = Config()
        with pytest.raises(ConfigurationError):
            config.validate()

        self._unset_envs(envs, envs_bck)
