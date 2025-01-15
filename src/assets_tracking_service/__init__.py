import warnings

from assets_tracking_service.log import init as init_logging
from assets_tracking_service.log import init_sentry

warnings.filterwarnings("ignore", category=FutureWarning, module="dask.*")  # from ArcGIS module

init_logging()
init_sentry()
