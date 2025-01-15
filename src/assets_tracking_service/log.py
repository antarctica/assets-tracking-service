import logging
from importlib.metadata import version

import sentry_sdk
from environs import Env


def init() -> None:
    """Initialize application logging."""
    # noinspection SpellCheckingInspection
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    logging.getLogger("app")


def init_sentry() -> None:
    """Initialize Sentry SDK if applicable."""
    env = Env()

    dsn = "https://57698b6483c7ac43b7c9c905cdb79943@o39753.ingest.us.sentry.io/4507581411229696"
    disabled = not env.bool("ASSETS_TRACKING_SERVICE_ENABLE_FEATURE_SENTRY", True)
    if disabled:  # pragma: no branch
        dsn = ""  # empty DSN disables Sentry

    sentry_sdk.init(
        dsn=dsn,
        traces_sample_rate=0.1,  # 10%
        profiles_sample_rate=0.1,  # 10%
        release=version("assets-tracking-service"),
        environment=env.str("ASSETS_TRACKING_SERVICE_SENTRY_ENVIRONMENT", "development"),
    )
