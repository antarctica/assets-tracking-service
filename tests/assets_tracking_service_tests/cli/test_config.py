from pytest_mock import MockerFixture
from typer.testing import CliRunner

from assets_tracking_service.cli import app_cli as cli
from assets_tracking_service.config import Config, ConfigurationError


class TestCliConfig:
    """Config CLI commands."""

    def test_cli_config_show(self, fx_config: Config, fx_cli: CliRunner) -> None:
        """Shows app configuration."""
        config = Config()

        result = fx_cli.invoke(app=cli, args=["config", "show"])

        assert result.exit_code == 0
        assert config.db_dsn_safe in result.output

    def test_cli_config_check(self, fx_config: Config, fx_cli: CliRunner) -> None:
        """App configuration validates."""
        result = fx_cli.invoke(app=cli, args=["config", "check"])

        assert result.exit_code == 0
        assert "Configuration ok" in result.output

    def test_cli_config_check_error(self, mocker: MockerFixture, fx_config: Config, fx_cli: CliRunner) -> None:
        """Invalid App configuration gives error."""
        mock_config = mocker.MagicMock(auto_spec=True)
        mock_config.validate.side_effect = ConfigurationError
        mocker.patch("assets_tracking_service.cli.config.Config", return_value=mock_config)

        result = fx_cli.invoke(app=cli, args=["config", "check"])

        assert result.exit_code == 1
        assert "Configuration invalid" in result.output
