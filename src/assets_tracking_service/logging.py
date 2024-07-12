import logging


def init() -> None:
    """Initialize application logging."""
    # noinspection SpellCheckingInspection
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    logging.getLogger("app")
