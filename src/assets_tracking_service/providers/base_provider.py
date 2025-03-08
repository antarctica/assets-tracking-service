from abc import ABC, abstractmethod
from collections.abc import Generator

from assets_tracking_service.models.asset import Asset, AssetNew
from assets_tracking_service.models.label import Label, LabelRelation, Labels
from assets_tracking_service.models.position import PositionNew


class Provider(ABC):
    """
    Abstract base class for providers.

    Defines a required interface all providers must implement to allow operations to be performed across a set of
    providers without knowledge of how each works.
    """

    # Class variables
    #

    # Short, unique name for provider, SHOULD be used as the label prefix so should be concise.
    name: str = ""  # e.g. "foo"

    # Prefix for name spacing labels, MUST be unique to provider.
    prefix: str = ""  # e.g. "foo"

    # Version of provider using CalVer (i.e. date of implementation).
    version: str = "YYYY-MM-DD"  # e.g. "2024-04-20"

    # Label scheme used to distinguish assets from provider - i.e. a serial number or other unique property.
    distinguishing_asset_label_scheme: str = f"{prefix}:"  # e.g. "foo:serial"

    # Label scheme used to distinguish positions from provider - i.e. a sequence or other unique property.
    distinguishing_position_label_scheme: str = f"{prefix}:"  # e.g. "foo:log_id"

    @property
    def provider_labels(self) -> Labels:
        """
        Concrete, public, method to get labels identifying the provider and its version.

        Dynamic to ensure Label creation dates reflect each Provider instance and to allow testing.
        """
        return Labels(
            [
                Label(rel=LabelRelation.PROVIDER, scheme="ats:provider_id", value=self.name),
                Label(rel=LabelRelation.PROVIDER, scheme="ats:provider_version", value=self.version),
            ]
        )

    def _index_assets(self, assets: list[Asset]) -> dict[str, Asset]:
        """Concrete utility method to index assets by their distinguishing label value."""
        return {asset.labels.filter_by_scheme(self.distinguishing_asset_label_scheme).value: asset for asset in assets}

    @abstractmethod
    def fetch_active_assets(self) -> Generator[AssetNew, None, None]:
        """
        Public entrypoint for fetching active assets.

        Must return a generator of assets deemed 'active'/'current' from each provider.

        Typically, this method calls private, provider specific, methods to fetch raw asset information, then marshall
        it into standardised AssetNew instances in this method.
        """
        pass

    @abstractmethod
    def fetch_latest_positions(self, assets: list[Asset]) -> Generator[PositionNew, None, None]:
        """
        Public entrypoint for fetching latest positions of assets.

        Must return a generator of PositionNew instances for a given list of assets.

        Typically, this method calls private, provider specific, methods to fetch raw position information, then
        marshall it into standardised PositionNew instances in this method.
        """
        pass
