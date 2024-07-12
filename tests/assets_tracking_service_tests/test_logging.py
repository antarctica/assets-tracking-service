import logging

import pytest

import assets_tracking_service  # noqa: F401


class TestLogging:
    def test_log(self, caplog: pytest.LogCaptureFixture):
        caplog.set_level(logging.INFO, logger="app")

        logger = logging.getLogger("app")
        logger.info("Test Log")

        assert "Test Log" in caplog.text
