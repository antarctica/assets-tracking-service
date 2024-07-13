from importlib.metadata import version

from typer.testing import CliRunner

from assets_tracking_service.cli import app_cli as cli


class TestCli:
    """Core CLI features."""

    def test_cli(self, fx_cli: CliRunner) -> None:
        """Empty call to CLI exits ok with no output."""
        result = fx_cli.invoke(app=cli)

        assert result.exit_code == 0
        assert result.output == ""

    def test_help(self, fx_cli: CliRunner) -> None:
        """The `--help` global option includes basic app details."""
        name = "ats-ctl"
        description = "Assets Tracking Service control CLI."

        result = fx_cli.invoke(app=cli, args=["--help"])

        assert result.exit_code == 0
        assert f"Usage: {name}" in result.output
        assert description in result.output

    def test_version(self, fx_cli: CliRunner) -> None:
        """The `--version` global option returns the app package version."""
        result = fx_cli.invoke(app=cli, args=["--version"])

        assert result.exit_code == 0
        assert result.output == f"{version('assets-tracking-service')}\n"
