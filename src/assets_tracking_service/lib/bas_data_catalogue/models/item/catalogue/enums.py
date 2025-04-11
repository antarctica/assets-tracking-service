from enum import Enum


class ResourceTypeIcon(Enum):
    """Partial mapping of Hierarchical Level code list terms to Font Awesome icon classes."""

    COLLECTION = "fa-fw far fa-shapes"
    DATASET = "fa-fw far fa-cube"
    PRODUCT = "fa-fw far fa-map"


class DistributionType(Enum):
    """Catalogue specific distribution types."""

    ARCGIS_FEATURE_LAYER = "ArcGIS Feature Layer"
    ARCGIS_OGC_FEATURE_LAYER = "OGC API Features (ArcGIS)"
