import os
import logging
from importlib.metadata import version

import sentry_sdk


def init() -> None:
    """Initialize application logging."""
    # noinspection SpellCheckingInspection
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    logging.getLogger("app")


def init_sentry() -> None:
    """Initialize Sentry SDK."""
    sentry_sdk.init(
        dsn="https://57698b6483c7ac43b7c9c905cdb79943@o39753.ingest.us.sentry.io/4507581411229696",
        traces_sample_rate=0.1,  # 10%
        profiles_sample_rate=0.1,  # 10%
        release=version("assets-tracking-service"),
        environment=os.environ.get("ASSETS_TRACKING_SERVICE_SENTRY_ENVIRONMENT", "development"),
    )
