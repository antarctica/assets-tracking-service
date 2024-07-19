from typing import Self

from pytest_mock import MockerFixture
from typer.testing import CliRunner

from assets_tracking_service.cli import app_cli as cli
from assets_tracking_service.exporters.exporters_manager import ExportersManager
from assets_tracking_service.providers.providers_manager import ProvidersManager


class TestCliData:
    """Data CLI commands."""

    def test_cli_data_fetch(
        self: Self, mocker: MockerFixture, fx_cli: CliRunner, fx_providers_manager_eg_provider: ProvidersManager
    ) -> None:
        """Fetches assets and positions."""
        mocker.patch("assets_tracking_service.cli.data.ProvidersManager", return_value=fx_providers_manager_eg_provider)

        result = fx_cli.invoke(app=cli, args=["data", "fetch"])

        assert result.exit_code == 0
        assert "Command exited normally" in result.output

    def test_cli_data_export(
        self: Self, mocker: MockerFixture, fx_cli: CliRunner, fx_exporters_manager_eg_exporter: ExportersManager
    ) -> None:
        """Exports data."""
        mocker.patch("assets_tracking_service.cli.data.ExportersManager", return_value=fx_exporters_manager_eg_exporter)

        result = fx_cli.invoke(app=cli, args=["data", "export"])

        assert result.exit_code == 0
        assert "Command exited normally" in result.output
