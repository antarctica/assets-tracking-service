import base64
import re
from abc import ABC, abstractmethod

from assets_tracking_service.lib.bas_data_catalogue.models.item.base.elements import Link
from assets_tracking_service.lib.bas_data_catalogue.models.item.catalogue.enums import DistributionType
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.distribution import (
    Distribution as RecordDistribution,
)


class Distribution(ABC):
    """
    Item Catalogue Distribution.

    Represents a distribution type supported by the BAS Data Catalogue. Types include both file downloads and services.
    Some types are composites, combing multiple Record distributions into a single Item distribution.

    Classes use a `matches()` class method to determine if a Record has the required distribution options.
    """

    @classmethod
    @abstractmethod
    def matches(cls, option: RecordDistribution, other_options: list[RecordDistribution]) -> bool:
        """Whether this class matches the distribution option."""
        ...

    @staticmethod
    def _encode_url(url: str) -> str:
        """
        Encode URL for use as a DOM selector.

        Base64 encodes URL and removes any non-alphanumeric characters.
        """
        return re.sub(r"\W", "", base64.b64encode(url.encode("utf-8")).decode("utf-8"))

    @property
    @abstractmethod
    def format_type(self) -> DistributionType:
        """Format type including label."""
        ...

    @property
    @abstractmethod
    def size(self) -> str:
        """Size if applicable."""
        ...

    @property
    @abstractmethod
    def action(self) -> Link:
        """
        Link to distribution if applicable.

        Where an `access_trigger` is set, the returned `Link.href` should be set to None.
        """
        ...

    @property
    def action_btn_variant(self) -> str:
        """
        Variant of button to display for action link or trigger.

        See https://style-kit.web.bas.ac.uk/core/buttons/#variants for available variants.
        """
        return "default"

    @property
    def action_btn_icon(self) -> str:
        """
        Font Awesome icon classes to display in action link or trigger.

        See https://fontawesome.com/v5/search?o=r&s=regular for choices (in available version and recommended style).
        """
        return "far fa-download"

    @property
    @abstractmethod
    def access_target(self) -> str | None:
        """Optional DOM selector of element showing more information on accessing distribution."""
        ...


class ArcGisFeatureLayer(Distribution):
    """
    ArcGIS Feature Layer distribution option.

    Consisting of a Feature Service and Feature Layer option.
    """

    def __init__(self, option: RecordDistribution, other_options: list[RecordDistribution]) -> None:
        self._layer = option
        self._service = self._get_service_option(other_options)

    @classmethod
    def matches(cls, option: RecordDistribution, other_options: list[RecordDistribution]) -> bool:
        """Whether this class matches the distribution option."""
        target_hrefs = [
            "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+feature",
            "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+feature",
        ]
        item_hrefs = [
            option.format.href
            for option in [option, *other_options]
            if hasattr(option, "format") and hasattr(option.format, "href")
        ]

        match = all(href in item_hrefs for href in target_hrefs)
        # avoid matching for each target href by only returning True if the first target matches
        return match and option.format.href == target_hrefs[0]

    @staticmethod
    def _get_service_option(options: list[RecordDistribution]) -> RecordDistribution:
        """Get corresponding service option for layer."""
        target_href = "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+feature"
        try:
            return next(option for option in options if option.format.href == target_href)
        except StopIteration:
            msg = "Required corresponding service option not found in resource distributions."
            raise ValueError(msg) from None

    @property
    def format_type(self) -> DistributionType:
        """Format type."""
        return DistributionType.ARCGIS_FEATURE_LAYER

    @property
    def size(self) -> str:
        """Not applicable."""
        return "N/A"

    @property
    def item_link(self) -> Link:
        """Link to portal item."""
        href = self._layer.transfer_option.online_resource.href
        return Link(value=href, href=href)

    @property
    def service_endpoint(self) -> str:
        """Link to service endpoint."""
        return self._service.transfer_option.online_resource.href

    @property
    def action(self) -> Link:
        """Link to distribution without href due to using `access_trigger`."""
        return Link(value="Add to GIS", href=None)

    @property
    def action_btn_variant(self) -> str:
        """Action button variant."""
        return "primary"

    @property
    def action_btn_icon(self) -> str:
        """Action button icon classes."""
        return "far fa-layer-plus"

    @property
    def access_target(self) -> str:
        """DOM selector of element showing more information on accessing layer."""
        return f"#item-data-info-{self._encode_url(self.item_link.href)}"


class ArcGisOgcApiFeatures(Distribution):
    """
    ArcGIS OGC API Features distribution option.

    Represents an ArcGIS specific implementation of the OGC API Features standard.

    Consisting of an ArcGIS OGC Feature Service and ArcGIS OGC Feature Layer option.
    """

    def __init__(self, option: RecordDistribution, other_options: list[RecordDistribution]) -> None:
        self._layer = option
        self._service = self._get_service_option(other_options)

    @classmethod
    def matches(cls, option: RecordDistribution, other_options: list[RecordDistribution]) -> bool:
        """Whether this class matches the distribution option."""
        target_hrefs = [
            "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+feature+ogc",
            "https://metadata-resources.data.bas.ac.uk/media-types/x-service/ogc+api+feature",
        ]
        item_hrefs = [
            option.format.href
            for option in [option, *other_options]
            if hasattr(option, "format") and hasattr(option.format, "href")
        ]

        match = all(href in item_hrefs for href in target_hrefs)
        # avoid matching for each target href by only returning True if the first target matches
        return match and option.format.href == target_hrefs[0]

    @staticmethod
    def _get_service_option(options: list[RecordDistribution]) -> RecordDistribution:
        """Get corresponding service option for layer."""
        target_href = "https://metadata-resources.data.bas.ac.uk/media-types/x-service/ogc+api+feature"
        try:
            return next(option for option in options if option.format.href == target_href)
        except StopIteration:
            msg = "Required corresponding service option not found in resource distributions."
            raise ValueError(msg) from None

    @property
    def format_type(self) -> DistributionType:
        """Format type."""
        return DistributionType.ARCGIS_OGC_FEATURE_LAYER

    @property
    def size(self) -> str:
        """Not applicable."""
        return "N/A"

    @property
    def item_link(self) -> Link:
        """Link to portal item."""
        href = self._layer.transfer_option.online_resource.href
        return Link(value=href, href=href)

    @property
    def service_endpoint(self) -> str:
        """Link to service endpoint."""
        return self._service.transfer_option.online_resource.href

    @property
    def action(self) -> Link:
        """Link to distribution without href due to using `access_trigger`."""
        return Link(value="Add to GIS", href=None)

    @property
    def action_btn_variant(self) -> str:
        """Action button variant."""
        return "primary"

    @property
    def action_btn_icon(self) -> str:
        """Action button icon classes."""
        return "far fa-layer-plus"

    @property
    def access_target(self) -> str:
        """DOM selector of element showing more information on accessing layer."""
        return f"#item-data-info-{self._encode_url(self.item_link.href)}"
