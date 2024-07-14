import logging
from datetime import datetime, timezone

import pytest
from freezegun.api import FrozenDateTimeFactory
from ulid import parse as ulid_parse

from assets_tracking_service.models.asset import Asset
from assets_tracking_service.models.label import Labels, Label, LabelRelation
from tests.providers.example_provider import ExampleProviderConfig, ExampleProvider

creation_time = datetime(2012, 6, 10, 14, 30, 20, tzinfo=timezone.utc)


class TestModelProvider:
    """
    Test abstract Provider class.

    Because Provider is an abstract class, we use a local concrete subclass (ExampleProvider) to test it.
    """

    def test_name(self, fx_provider_example: ExampleProvider):
        """Name class property."""
        assert fx_provider_example.name == "example"

    def test_prefix(self, fx_provider_example: ExampleProvider):
        """Prefix class property."""
        assert fx_provider_example.prefix == "example"

    def test_distinguishing_asset_label_scheme(self, fx_provider_example: ExampleProvider):
        """Distinguishing asset label scheme class property."""
        assert fx_provider_example.distinguishing_asset_label_scheme == "example:asset_id"

    def test_distinguishing_position_label_scheme(self, fx_provider_example: ExampleProvider):
        """Distinguishing position label scheme class property."""
        assert fx_provider_example.distinguishing_position_label_scheme == "example:position_id"

    @pytest.mark.parametrize("config", [{"password": "x"}, {"username": "x"}])
    def test_init_error(self, fx_logger: logging.Logger, config: ExampleProviderConfig):
        with pytest.raises(RuntimeError, match="Missing required config key"):
            ExampleProvider(config=config, logger=fx_logger)

    def test_provider_labels(self, freezer: FrozenDateTimeFactory, fx_provider_example: ExampleProvider):
        """Makes provider labels."""
        freezer.move_to(creation_time)

        expected_labels = Labels(
            [
                Label(rel=LabelRelation.PROVIDER, scheme="ats:provider_id", value="example"),
                Label(rel=LabelRelation.PROVIDER, scheme="ats:provider_version", value="2024-07-06"),
            ]
        )

        assert fx_provider_example._provider_labels == expected_labels

    @pytest.mark.cov
    def test_index_assets(self, fx_provider_example: ExampleProvider):
        """Indexes assets by distinguishing asset label scheme."""
        asset_new = next(fx_provider_example.fetch_active_assets())
        asset = Asset(id=ulid_parse("01J2S3YST6RM9Y2JDYR4RXTJE0"), labels=asset_new.labels)

        indexed_assets = fx_provider_example._index_assets(assets=[asset])
        assert indexed_assets == {"example-asset-0": asset}

    def test_fetch_active_assets(self, fx_provider_example: ExampleProvider):
        """Fetch active assets abstract method."""
        assets = list(fx_provider_example.fetch_active_assets())
        assert len(assets) == 3

    def test_fetch_latest_positions(self, fx_provider_example: ExampleProvider, fx_asset: Asset):
        """Fetch latest positions abstract method."""
        positions = list(fx_provider_example.fetch_latest_positions(assets=[fx_asset]))
        assert len(positions) == 3
