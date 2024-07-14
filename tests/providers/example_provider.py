import logging
from datetime import datetime, timezone
from typing import TypedDict, Generator

from shapely import Point

from assets_tracking_service.models.asset import AssetNew, Asset
from assets_tracking_service.models.label import Labels, Label, LabelRelation
from assets_tracking_service.models.position import PositionNew
from assets_tracking_service.models.provider import Provider


class ExampleProviderConfig(TypedDict):
    username: str
    password: str


class ExampleProvider(Provider):
    name = "example"
    prefix = name
    version = "2024-07-06"
    distinguishing_asset_label_scheme = f"{prefix}:asset_id"
    distinguishing_position_label_scheme = f"{prefix}:position_id"

    def __init__(self, config: ExampleProviderConfig, logger: logging.Logger):
        self._logger = logger

        self._logger.debug("Setting Example Provider configuration...")
        self._check_config(config)
        self._config = config
        self._logger.debug("Example Provider configuration ok.")

    def _check_config(self, config: ExampleProviderConfig) -> None:
        for key in ["username", "password"]:
            if key not in config:
                msg = f"Missing required config key: '{key}'"
                self._logger.error(msg)
                raise RuntimeError(msg)

    def fetch_active_assets(self) -> Generator[AssetNew, None, None]:
        for i in range(3):
            value = f"example-asset-{i}"
            labels = Labels(
                [
                    Label(rel=LabelRelation.SELF, scheme="skos:prefLabel", value=value),
                    Label(rel=LabelRelation.SELF, scheme=self.distinguishing_asset_label_scheme, value=value),
                    *self._provider_labels,
                ]
            )

            yield AssetNew(labels=labels)

    def fetch_latest_positions(self, assets: list[Asset]) -> Generator[PositionNew, None, None]:
        asset = assets[0]

        for i in range(3):
            value = f"example-position-{i}"

            yield PositionNew(
                asset_id=asset.id,
                time=datetime.now(tz=timezone.utc),
                geom=Point(0, 0, 0),
                labels=Labels(
                    [
                        Label(rel=LabelRelation.SELF, scheme=self.distinguishing_position_label_scheme, value=value),
                        *self._provider_labels,
                    ]
                ),
            )
