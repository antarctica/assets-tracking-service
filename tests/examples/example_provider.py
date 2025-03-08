import logging
from collections.abc import Generator
from datetime import UTC, datetime

from shapely import Point

from assets_tracking_service.config import Config
from assets_tracking_service.models.asset import Asset, AssetNew
from assets_tracking_service.models.label import Label, LabelRelation, Labels
from assets_tracking_service.models.position import PositionNew
from assets_tracking_service.providers.base_provider import Provider


class ExampleProvider(Provider):
    """Example Provider for testing."""

    name = "example"
    prefix = name
    version = "2024-07-06"
    distinguishing_asset_label_scheme = f"{prefix}:asset_id"
    distinguishing_position_label_scheme = f"{prefix}:position_id"

    def __init__(self, config: Config, logger: logging.Logger) -> None:
        self._logger = logger

        self._logger.debug("Setting Example Provider configuration...")
        self._config = config
        self._logger.debug("Example Provider configuration ok.")

    def fetch_active_assets(self) -> Generator[AssetNew, None, None]:
        """Fetch active assets."""
        for i in range(3):
            value = f"example-asset-{i}"
            labels = Labels(
                [
                    Label(rel=LabelRelation.SELF, scheme="skos:prefLabel", value=value),
                    Label(rel=LabelRelation.SELF, scheme=self.distinguishing_asset_label_scheme, value=value),
                    Label(
                        rel=LabelRelation.SELF,
                        scheme="nvs:L06",
                        scheme_uri="http://vocab.nerc.ac.uk/collection/L06/current",
                        value="0",
                        value_uri="http://vocab.nerc.ac.uk/collection/L06/current/0",
                    ),
                    *self.provider_labels,
                ]
            )

            yield AssetNew(labels=labels)

    def fetch_latest_positions(self, assets: list[Asset]) -> Generator[PositionNew, None, None]:
        """Fetch latest positions for assets."""
        asset = assets[0]

        for i in range(3):
            value = f"example-position-{i}"

            yield PositionNew(
                asset_id=asset.id,
                time=datetime.now(tz=UTC),
                geom=Point(0, 0, 0),
                labels=Labels(
                    [
                        Label(rel=LabelRelation.SELF, scheme=self.distinguishing_position_label_scheme, value=value),
                        *self.provider_labels,
                    ]
                ),
            )
