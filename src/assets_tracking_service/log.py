import logging
from importlib.metadata import version

import sentry_sdk


def init() -> None:
    """Initialize application logging."""
    # noinspection SpellCheckingInspection
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    logging.getLogger("app")


def init_sentry() -> None:
    """
    Initialize Sentry SDK if enabled.

    The DSN is embedded here as the config class is not yet available based on when this method is called.
    """
    # can't import Config normally due to circular imports
    from assets_tracking_service.config import Config

    config = Config()

    dsn = config.SENTRY_DSN
    disabled = not config.ENABLE_FEATURE_SENTRY
    if disabled:  # pragma: no branch
        dsn = ""  # empty DSN disables Sentry

    sentry_sdk.init(
        dsn=dsn,
        traces_sample_rate=0.1,  # 10%
        profiles_sample_rate=0.1,  # 10%
        release=version("assets-tracking-service"),
        environment=config.SENTRY_ENVIRONMENT,
    )
