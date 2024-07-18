import os
from importlib.metadata import version
from pathlib import Path
from typing import Any

import dsnparse
import pytest

from assets_tracking_service.config import Config, EditableDsn, ConfigurationError


class TestEditableDsn:
    """Test custom dsnparse.ParseResult class."""

    @pytest.mark.cov
    def test_database(self):
        """Can get database property."""
        db = "assets-tracking-test"
        dsn = f"postgresql://test:password@localhost:5432/{db}"
        dsn_parsed = dsnparse.parse(dsn, EditableDsn)

        assert dsn_parsed.database == db

    @pytest.mark.cov
    def test_secret(self):
        """Can get secret property"""
        password = "password"
        dsn = f"postgresql://test:{password}@localhost:5432/assets-tracking-test"
        dsn_parsed = dsnparse.parse(dsn, EditableDsn)

        assert dsn_parsed.secret == password


class TestConfig:
    """Test app config."""

    @staticmethod
    def _set_envs(envs) -> dict:
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

    def test_db_dsn(self):
        """
        Gets DB DSN from environment.

        This has previously proved unreliable in CI so has a dedicated test we can run.
        """
        config = Config()

        assert "postgresql://" in config.DB_DSN

        config.validate()

    def test_db_dsn_explicit(self):
        """Gets DB DSN when set explicitly as part of test."""
        dsn = "postgresql://test:password@localhost:5432/assets-tracking-dev"
        envs = {"ASSETS_TRACKING_SERVICE_DB_DSN": dsn, "ASSETS_TRACKING_SERVICE_DB_DATABASE": None}
        envs_bck = self._set_envs(envs)

        config = Config()
        assert config.DB_DSN == dsn

        self._unset_envs(envs, envs_bck)

    def test_db_dsn_app_db(self):
        """Gets DB DSN with overridden database name."""
        dsn = "postgresql://test:password@localhost:5432/assets-tracking-foo"
        name = "assets-tracking-bar"

        envs = {"ASSETS_TRACKING_SERVICE_DB_DSN": dsn, "ASSETS_TRACKING_SERVICE_DB_DATABASE": name}
        envs_bck = self._set_envs(envs)

        config = Config()
        assert config.DB_DSN == dsn.replace("assets-tracking-foo", name)

        self._unset_envs(envs, envs_bck)

    def test_db_safe(self):
        """Gets DB DSN with password redacted."""
        password = "password"
        dsn = f"postgresql://test:{password}@localhost:5432/assets-tracking-test"
        safe_dsn = dsn.replace(password, "[**REDACTED**]")

        envs = {"ASSETS_TRACKING_SERVICE_DB_DSN": dsn}
        envs_bck = self._set_envs(envs)

        config = Config()
        assert config.DB_DSN == dsn
        assert config.db_dsn_safe == safe_dsn

        self._unset_envs(envs, envs_bck)

    def test_version(self):
        """Version is read from package metadata."""
        config = Config()
        assert config.version == version("assets-tracking-service")

    def test_dumps_safe(self, fx_package_version: str, fx_config: Config):
        """Config can be exported to a dict with sensitive values redacted."""
        redacted_value = "[**REDACTED**]"
        expected = {
            "version": fx_package_version,
            "db_dsn": fx_config.db_dsn_safe,
            "enable_provider_aircraft_tracking": True,
            "enable_provider_geotab": True,
            "enabled_providers": ["geotab", "aircraft_tracking"],
            "provider_aircraft_tracking_api_key": redacted_value,
            "provider_aircraft_tracking_password": redacted_value,
            "provider_aircraft_tracking_username": "x",
            "provider_geotab_database": "x",
            "provider_geotab_group_nvs_l06_code_mapping": fx_config.provider_geotab_group_nvs_l06_code_mapping,
            "provider_geotab_password": redacted_value,
            "provider_geotab_username": "x",
            "enable_exporter_arcgis": True,
            "enable_exporter_geojson": True,
            "enabled_exporters": ["arcgis", "geojson"],
            "exporter_arcgis_username": "x",
            "exporter_arcgis_password": redacted_value,
            "exporter_arcgis_item_id": "x",
            "exporter_geojson_output_path": Path("export.geojson"),
        }

        output = fx_config.dumps_safe()
        assert output == expected
        assert redacted_value in output["db_dsn"]

    def test_validate(self, fx_config: Config):
        """Valid configuration is ok."""
        fx_config.validate()

    def test_validate_missing_dsn(self):
        """Validation fails where DB DSN is missing."""
        envs = {"ASSETS_TRACKING_SERVICE_DB_DSN": None}
        envs_bck = self._set_envs(envs)

        config = Config(read_env=False)

        with pytest.raises(ConfigurationError):
            config.validate()

        self._unset_envs(envs, envs_bck)

    def test_validate_invalid_dsn(self):
        """Validation fails where DB DSN is invalid."""
        envs = {"ASSETS_TRACKING_SERVICE_DB_DSN": "postgresql://"}
        envs_bck = self._set_envs(envs)

        config = Config(read_env=False)

        with pytest.raises(ConfigurationError):
            config.validate()

        self._unset_envs(envs, envs_bck)

    @pytest.mark.parametrize(
        "provider_name,input_value,expected_value",
        [
            ("GEOTAB", "true", True),
            ("GEOTAB", "false", False),
            ("GEOTAB", None, True),
            ("AIRCRAFT_TRACKING", "true", True),
            ("AIRCRAFT_TRACKING", "false", False),
            ("AIRCRAFT_TRACKING", None, True),
        ],
    )
    def test_enable_provider(self, provider_name: str, input_value: str, expected_value: bool):
        """Providers are correctly enabled by default and with explicit values."""
        envs = {f"ASSETS_TRACKING_SERVICE_ENABLE_PROVIDER_{provider_name}": input_value}
        envs_bck = self._set_envs(envs)

        config = Config()
        assert getattr(config, f"ENABLE_PROVIDER_{provider_name}") == expected_value

        self._unset_envs(envs, envs_bck)

    @pytest.mark.parametrize(
        "envs,expected",
        [
            (
                {
                    "ASSETS_TRACKING_SERVICE_ENABLE_PROVIDER_GEOTAB": "true",
                    "ASSETS_TRACKING_SERVICE_ENABLE_PROVIDER_AIRCRAFT_TRACKING": "true",
                },
                ["geotab", "aircraft_tracking"],
            ),
            (
                {
                    "ASSETS_TRACKING_SERVICE_ENABLE_PROVIDER_GEOTAB": "true",
                    "ASSETS_TRACKING_SERVICE_ENABLE_PROVIDER_AIRCRAFT_TRACKING": "false",
                },
                ["geotab"],
            ),
            (
                {
                    "ASSETS_TRACKING_SERVICE_ENABLE_PROVIDER_GEOTAB": "false",
                    "ASSETS_TRACKING_SERVICE_ENABLE_PROVIDER_AIRCRAFT_TRACKING": "true",
                },
                ["aircraft_tracking"],
            ),
            (
                {
                    "ASSETS_TRACKING_SERVICE_ENABLE_PROVIDER_GEOTAB": "false",
                    "ASSETS_TRACKING_SERVICE_ENABLE_PROVIDER_AIRCRAFT_TRACKING": "false",
                },
                [],
            ),
        ],
    )
    def test_enabled_providers(self, envs: dict[str, str], expected: list[str]):
        """Enabled providers derived property is correctly constructed."""
        envs_bck = self._set_envs(envs)

        config = Config()
        assert config.enabled_providers == expected

        self._unset_envs(envs, envs_bck)

    @pytest.mark.parametrize(
        "exporter_name,input_value,expected_value",
        [
            ("ARCGIS", "true", True),
            ("ARCGIS", "false", False),
            ("ARCGIS", None, True),
            ("GEOJSON", "true", True),
            ("GEOJSON", "false", False),
            ("GEOJSON", None, True),
        ],
    )
    def test_enable_exporter(self, exporter_name: str, input_value: str, expected_value: bool):
        """Exporters are correctly enabled by default and with explicit values."""
        envs = {f"ASSETS_TRACKING_SERVICE_ENABLE_EXPORTER_{exporter_name}": input_value}
        envs_bck = self._set_envs(envs)

        config = Config()
        assert getattr(config, f"ENABLE_EXPORTER_{exporter_name}") == expected_value

        self._unset_envs(envs, envs_bck)

    @pytest.mark.parametrize(
        "envs,expected",
        [
            (
                {
                    "ASSETS_TRACKING_SERVICE_ENABLE_EXPORTER_ARCGIS": "true",
                    "ASSETS_TRACKING_SERVICE_ENABLE_EXPORTER_GEOJSON": "true",
                },
                ["arcgis", "geojson"],
            ),
            (
                {
                    "ASSETS_TRACKING_SERVICE_ENABLE_EXPORTER_ARCGIS": "true",
                    "ASSETS_TRACKING_SERVICE_ENABLE_EXPORTER_GEOJSON": "false",
                },
                ["arcgis"],
            ),
            (
                {
                    "ASSETS_TRACKING_SERVICE_ENABLE_EXPORTER_ARCGIS": "false",
                    "ASSETS_TRACKING_SERVICE_ENABLE_EXPORTER_GEOJSON": "true",
                },
                ["geojson"],
            ),
            (
                {
                    "ASSETS_TRACKING_SERVICE_ENABLE_EXPORTER_ARCGIS": "false",
                    "ASSETS_TRACKING_SERVICE_ENABLE_EXPORTER_GEOJSON": "false",
                },
                [],
            ),
        ],
    )
    def test_enabled_exporters(self, envs: dict[str, str], expected: list[str]):
        """Enabled exporters derived property is correctly constructed."""
        envs_bck = self._set_envs(envs)

        config = Config()
        assert config.enabled_exporters == expected

        self._unset_envs(envs, envs_bck)

    @pytest.mark.parametrize(
        "property_name,expected,sensitive",
        [
            ("PROVIDER_GEOTAB_USERNAME", "x", False),
            ("PROVIDER_GEOTAB_PASSWORD", "x", True),
            ("PROVIDER_GEOTAB_DATABASE", "x", False),
            ("PROVIDER_AIRCRAFT_TRACKING_USERNAME", "x", False),
            ("PROVIDER_AIRCRAFT_TRACKING_PASSWORD", "x", True),
            ("PROVIDER_AIRCRAFT_TRACKING_API_KEY", "x", True),
            ("EXPORTER_ARCGIS_USERNAME", "x", False),
            ("EXPORTER_ARCGIS_PASSWORD", "x", True),
            ("EXPORTER_ARCGIS_ITEM_ID", "x", False),
            ("EXPORTER_GEOJSON_OUTPUT_PATH", Path("export.geojson"), False),
        ],
    )
    def test_configurable_property(self, property_name: str, expected: Any, sensitive: bool):
        """Configurable properties can be accessed."""
        envs = {f"ASSETS_TRACKING_SERVICE_{property_name}": str(expected)}
        envs_bck = self._set_envs(envs)

        config = Config()
        assert getattr(config, property_name) == expected

        if sensitive:
            assert getattr(config, f"{property_name.lower()}_safe") == "[**REDACTED**]"

        self._unset_envs(envs, envs_bck)

    @pytest.mark.cov
    def test_provider_geotab_group_nvs_l06_code_mapping(self):
        """For completeness."""
        config = Config()
        assert isinstance(config.provider_geotab_group_nvs_l06_code_mapping, dict)

    @pytest.mark.cov
    def test_validate_providers_disabled(self):
        """Needed to satisfy coverage that config is valid when all providers can be disabled."""
        envs = {
            "ASSETS_TRACKING_SERVICE_ENABLE_PROVIDER_GEOTAB": "false",
            "ASSETS_TRACKING_SERVICE_ENABLE_PROVIDER_AIRCRAFT_TRACKING": "false",
        }
        envs_bck = self._set_envs(envs)

        config = Config()
        config.validate()

        self._unset_envs(envs, envs_bck)

    @pytest.mark.cov
    def test_validate_exporters_disabled(self):
        """Needed to satisfy coverage that config is valid when all exporters can be disabled."""
        envs = {
            "ASSETS_TRACKING_SERVICE_ENABLE_EXPORTER_ARCGIS": "false",
            "ASSETS_TRACKING_SERVICE_ENABLE_EXPORTER_GEOJSON": "false",
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
                    "ASSETS_TRACKING_SERVICE_ENABLE_PROVIDER_GEOTAB": "true",
                    "ASSETS_TRACKING_SERVICE_ENABLE_PROVIDER_AIRCRAFT_TRACKING": "false",
                    "ASSETS_TRACKING_SERVICE_PROVIDER_GEOTAB_USERNAME": None,
                    "ASSETS_TRACKING_SERVICE_PROVIDER_GEOTAB_PASSWORD": "x",
                    "ASSETS_TRACKING_SERVICE_PROVIDER_GEOTAB_DATABASE": "x",
                }
            ),
            (
                {
                    "ASSETS_TRACKING_SERVICE_ENABLE_PROVIDER_GEOTAB": "true",
                    "ASSETS_TRACKING_SERVICE_ENABLE_PROVIDER_AIRCRAFT_TRACKING": "false",
                    "ASSETS_TRACKING_SERVICE_PROVIDER_GEOTAB_USERNAME": "x",
                    "ASSETS_TRACKING_SERVICE_PROVIDER_GEOTAB_PASSWORD": None,
                    "ASSETS_TRACKING_SERVICE_PROVIDER_GEOTAB_DATABASE": "x",
                }
            ),
            (
                {
                    "ASSETS_TRACKING_SERVICE_ENABLE_PROVIDER_GEOTAB": "true",
                    "ASSETS_TRACKING_SERVICE_ENABLE_PROVIDER_AIRCRAFT_TRACKING": "false",
                    "ASSETS_TRACKING_SERVICE_PROVIDER_GEOTAB_USERNAME": "x",
                    "ASSETS_TRACKING_SERVICE_PROVIDER_GEOTAB_PASSWORD": "x",
                    "ASSETS_TRACKING_SERVICE_PROVIDER_GEOTAB_DATABASE": None,
                }
            ),
            (
                {
                    "ASSETS_TRACKING_SERVICE_ENABLE_PROVIDER_GEOTAB": "false",
                    "ASSETS_TRACKING_SERVICE_ENABLE_PROVIDER_AIRCRAFT_TRACKING": "true",
                    "ASSETS_TRACKING_SERVICE_PROVIDER_AIRCRAFT_TRACKING_USERNAME": None,
                    "ASSETS_TRACKING_SERVICE_PROVIDER_AIRCRAFT_TRACKING_PASSWORD": "x",
                    "ASSETS_TRACKING_SERVICE_PROVIDER_AIRCRAFT_TRACKING_API_KEY": "x",
                    "ASSETS_TRACKING_SERVICE_ENABLE_EXPORTER_ARCGIS": "true",
                    "ASSETS_TRACKING_SERVICE_EXPORTER_ARCGIS_USERNAME": None,
                    "ASSETS_TRACKING_SERVICE_EXPORTER_ARCGIS_PASSWORD": "x",
                    "ASSETS_TRACKING_SERVICE_EXPORTER_ARCGIS_ITEM_ID": "x",
                }
            ),
            (
                {
                    "ASSETS_TRACKING_SERVICE_ENABLE_PROVIDER_GEOTAB": "false",
                    "ASSETS_TRACKING_SERVICE_ENABLE_PROVIDER_AIRCRAFT_TRACKING": "true",
                    "ASSETS_TRACKING_SERVICE_PROVIDER_AIRCRAFT_TRACKING_USERNAME": "x",
                    "ASSETS_TRACKING_SERVICE_PROVIDER_AIRCRAFT_TRACKING_PASSWORD": None,
                    "ASSETS_TRACKING_SERVICE_PROVIDER_AIRCRAFT_TRACKING_API_KEY": "x",
                    "ASSETS_TRACKING_SERVICE_ENABLE_EXPORTER_ARCGIS": "true",
                    "ASSETS_TRACKING_SERVICE_EXPORTER_ARCGIS_USERNAME": "x",
                    "ASSETS_TRACKING_SERVICE_EXPORTER_ARCGIS_PASSWORD": None,
                    "ASSETS_TRACKING_SERVICE_EXPORTER_ARCGIS_ITEM_ID": "x",
                }
            ),
            (
                {
                    "ASSETS_TRACKING_SERVICE_ENABLE_PROVIDER_GEOTAB": "false",
                    "ASSETS_TRACKING_SERVICE_ENABLE_PROVIDER_AIRCRAFT_TRACKING": "true",
                    "ASSETS_TRACKING_SERVICE_PROVIDER_AIRCRAFT_TRACKING_USERNAME": "x",
                    "ASSETS_TRACKING_SERVICE_PROVIDER_AIRCRAFT_TRACKING_PASSWORD": "x",
                    "ASSETS_TRACKING_SERVICE_PROVIDER_AIRCRAFT_TRACKING_API_KEY": None,
                    "ASSETS_TRACKING_SERVICE_ENABLE_EXPORTER_ARCGIS": "true",
                    "ASSETS_TRACKING_SERVICE_EXPORTER_ARCGIS_USERNAME": "x",
                    "ASSETS_TRACKING_SERVICE_EXPORTER_ARCGIS_PASSWORD": "x",
                    "ASSETS_TRACKING_SERVICE_EXPORTER_ARCGIS_ITEM_ID": None,
                }
            ),
            (
                {
                    "ASSETS_TRACKING_SERVICE_ENABLE_EXPORTER_GEOJSON": "true",
                    "ASSETS_TRACKING_SERVICE_EXPORTER_GEOJSON_OUTPUT_PATH": None,
                }
            ),
        ],
    )
    def test_validate_missing_required_option(self, envs: dict):
        """
        Validation fails where a required provider or exporter config option is missing.

        Note: The `ASSETS_TRACKING_SERVICE_DB_DSN` option is trickier to check and covered by a specific test.
        """
        static_env = {"ASSETS_TRACKING_SERVICE_DB_DSN": "postgresql://postgres@localhost:5432/assets-tracking-test"}
        envs = {**static_env, **envs}
        envs_bck = self._set_envs(envs)

        config = Config(read_env=False)

        with pytest.raises(ConfigurationError):
            config.validate()

        self._unset_envs(envs, envs_bck)

    def test_validate_exporter_disabled_dependency(self):
        """Validation fails where an exporter that another exporter depends on is disabled."""
        envs = {
            "ASSETS_TRACKING_SERVICE_ENABLE_EXPORTER_ARCGIS": "true",
            "ASSETS_TRACKING_SERVICE_ENABLE_EXPORTER_GEOJSON": "false",
        }
        envs_bck = self._set_envs(envs)

        config = Config()
        with pytest.raises(ConfigurationError):
            config.validate()

        self._unset_envs(envs, envs_bck)
