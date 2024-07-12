import pytest

from assets_tracking_service.config import Config


@pytest.fixture
def fx_config() -> Config:
    return Config()
