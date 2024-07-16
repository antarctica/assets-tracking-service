from pytest_mock import MockerFixture
from typer.testing import CliRunner

from assets_tracking_service.cli import app_cli as cli
from assets_tracking_service.exporters.geojson import GeoJsonExporter
from assets_tracking_service.providers.providers_manager import ProvidersManager


class TestCliData:
    """Data CLI commands."""

    def test_cli_data_fetch(
        self, mocker: MockerFixture, fx_cli: CliRunner, fx_providers_manager_eg_provider: ProvidersManager
    ) -> None:
        """Fetches assets and positions."""
        mocker.patch("assets_tracking_service.cli.data.ProvidersManager", return_value=fx_providers_manager_eg_provider)

        result = fx_cli.invoke(app=cli, args=["data", "fetch"])

        assert result.exit_code == 0
        assert "Command exited normally" in result.output

    def test_cli_data_export(
        self, mocker: MockerFixture, fx_cli: CliRunner, fx_exporter_geojson: GeoJsonExporter
    ) -> None:
        """Exports data."""
        mocker.patch("assets_tracking_service.cli.data.GeoJsonExporter", return_value=fx_exporter_geojson)

        result = fx_cli.invoke(app=cli, args=["data", "export"])

        assert result.exit_code == 0
        assert "Command exited normally" in result.output
