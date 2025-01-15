import warnings

from assets_tracking_service.logging import init as init_logging
from assets_tracking_service.logging import init_sentry

warnings.filterwarnings("ignore", category=FutureWarning, module="dask.*")

init_logging()
init_sentry()
