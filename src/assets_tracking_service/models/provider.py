from abc import ABC, abstractmethod
from typing import Generator

from assets_tracking_service.models.asset import AssetNew, Asset
from assets_tracking_service.models.label import Labels, Label, LabelRelation
from assets_tracking_service.models.position import PositionNew


class Provider(ABC):
    name: str = ""
    prefix: str = ""
    version: str = "YYYY-MM-DD"
    distinguishing_asset_label_scheme: str = f"{prefix}:"
    distinguishing_position_label_scheme: str = f"{prefix}:"

    @property
    def _provider_labels(self) -> Labels:
        return Labels(
            [
                Label(rel=LabelRelation.PROVIDER, scheme="ats:provider_id", value=self.name),
                Label(rel=LabelRelation.PROVIDER, scheme="ats:provider_version", value=self.version),
            ]
        )

    def _index_assets(self, assets: list[Asset]) -> dict[str, Asset]:
        return {asset.labels.filter_by_scheme(self.distinguishing_asset_label_scheme).value: asset for asset in assets}

    @abstractmethod
    def _check_config(self, config: dict) -> None:
        # make sure to call from __init__
        pass

    @abstractmethod
    def fetch_active_assets(self) -> Generator[AssetNew, None, None]:
        pass

    @abstractmethod
    def fetch_latest_positions(self, assets: list[Asset]) -> Generator[PositionNew, None, None]:
        pass
