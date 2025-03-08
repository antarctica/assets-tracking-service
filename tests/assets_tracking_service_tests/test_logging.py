import logging

import pytest

import assets_tracking_service  # noqa: F401


class TestLogging:
    """Tests for  app logging."""

    def test_log(self, caplog: pytest.LogCaptureFixture):
        """Logs are recorded."""
        caplog.set_level(logging.INFO, logger="app")

        logger = logging.getLogger("app")
        logger.info("Test Log")

        assert "Test Log" in caplog.text
