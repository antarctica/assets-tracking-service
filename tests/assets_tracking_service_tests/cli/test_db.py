from typing import Self

from pytest_mock import MockerFixture
from typer.testing import CliRunner

from assets_tracking_service.cli import app_cli as cli
from assets_tracking_service.db import DatabaseError, DatabaseMigrationError


class TestCliDb:
    """DB CLI commands."""

    def test_cli_db_check(self: Self, fx_cli: CliRunner) -> None:
        """App DB accessible."""
        result = fx_cli.invoke(app=cli, args=["db", "check"])

        assert result.exit_code == 0
        assert "Database ok" in result.output

    def test_cli_db_check_error(self: Self, mocker: MockerFixture, fx_cli: CliRunner) -> None:
        """Issue accessing app DB gives error."""
        mock_db_client = mocker.MagicMock(auto_spec=True)
        mock_db_client.execute.side_effect = DatabaseError
        mocker.patch("assets_tracking_service.cli.db.DatabaseClient", return_value=mock_db_client)

        result = fx_cli.invoke(app=cli, args=["db", "check"])

        assert result.exit_code == 1
        assert "Error accessing database" in result.output

    def test_cli_db_migrate(self: Self, fx_cli_tmp_db: CliRunner) -> None:
        """App DB migrations."""
        result = fx_cli_tmp_db.invoke(app=cli, args=["db", "migrate"])

        assert result.exit_code == 0
        assert "Database migrated" in result.output

    def test_cli_db_migrate_error(self: Self, mocker: MockerFixture, fx_cli_tmp_db: CliRunner) -> None:
        """Issue migrating App DB gives error."""
        mock_db_client = mocker.MagicMock(auto_spec=True)
        mock_db_client.migrate_upgrade.side_effect = DatabaseMigrationError
        mocker.patch("assets_tracking_service.cli.db.DatabaseClient", return_value=mock_db_client)

        result = fx_cli_tmp_db.invoke(app=cli, args=["db", "migrate"])

        assert result.exit_code == 1
        assert "Error migrating database" in result.output

    def test_cli_db_rollback(self: Self, fx_cli_tmp_db_mig: CliRunner) -> None:
        """App DB rollback."""
        result = fx_cli_tmp_db_mig.invoke(app=cli, args=["db", "rollback"], input="y\n")

        assert result.exit_code == 0
        assert "DB rolled back" in result.output

    def test_cli_db_rollback_cancelled(self: Self, fx_cli_tmp_db_mig: CliRunner) -> None:
        """Cancelled app DB rollback aborts."""
        result = fx_cli_tmp_db_mig.invoke(app=cli, args=["db", "rollback"], input="n\n")

        assert result.exit_code == 0
        assert "Aborted" in result.output

    def test_cli_db_rollback_error(self: Self, mocker: MockerFixture, fx_cli_tmp_db_mig: CliRunner) -> None:
        """Issue rolling back App DB gives error."""
        mock_db_client = mocker.MagicMock(auto_spec=True)
        mock_db_client.migrate_downgrade.side_effect = DatabaseMigrationError
        mocker.patch("assets_tracking_service.cli.db.DatabaseClient", return_value=mock_db_client)

        result = fx_cli_tmp_db_mig.invoke(app=cli, args=["db", "rollback"], input="y\n")

        assert result.exit_code == 1
        assert "Error rolling back database" in result.output
