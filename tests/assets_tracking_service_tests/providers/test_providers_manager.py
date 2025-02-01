import logging
from datetime import UTC, datetime
from typing import Self
from unittest.mock import PropertyMock

import pytest
from freezegun.api import FrozenDateTimeFactory
from psycopg.sql import SQL
from pytest_mock import MockerFixture

from assets_tracking_service.config import Config
from assets_tracking_service.db import DatabaseClient
from assets_tracking_service.models.asset import AssetNew
from assets_tracking_service.providers.providers_manager import ProvidersManager
from tests.examples.example_provider import ExampleProvider

creation_time = datetime(2012, 6, 10, 14, 30, 20, tzinfo=UTC)


class TestProvidersManager:
    """Providers manager tests."""

    def test_init(
        self: Self,
        mocker: MockerFixture,
        fx_config: Config,
        fx_db_client_tmp_db_mig: DatabaseClient,
        fx_logger: logging.Logger,
    ):
        """Initialises."""
        mock_geotab_client = mocker.MagicMock(auto_spec=True)
        mock_geotab_client.authenticate.return_value = []
        mocker.patch("assets_tracking_service.providers.geotab.Geotab", return_value=mock_geotab_client)

        manager = ProvidersManager(config=fx_config, db=fx_db_client_tmp_db_mig, logger=fx_logger)

        assert len(manager._providers) > 0

    def test_init_no_providers(
        self: Self, mocker: MockerFixture, fx_db_client_tmp_db_mig: DatabaseClient, fx_logger: logging.Logger
    ):
        """Initialises with no providers."""
        mock_config = mocker.Mock()
        type(mock_config).ENABLED_PROVIDERS = PropertyMock(return_value=[])
        manager = ProvidersManager(config=mock_config, db=fx_db_client_tmp_db_mig, logger=fx_logger)

        assert len(manager._providers) == 0

    @pytest.mark.parametrize("enabled_providers", [["geotab"], ["aircraft_tracking"]])
    def test_make_each_provider(
        self: Self,
        mocker: MockerFixture,
        fx_db_client_tmp_db_mig: DatabaseClient,
        fx_logger: logging.Logger,
        enabled_providers: list[str],
    ):
        """Makes each provider."""
        mock_geotab_client = mocker.MagicMock(auto_spec=True)
        mock_geotab_client.authenticate.return_value = []
        mocker.patch("assets_tracking_service.providers.geotab.Geotab", return_value=mock_geotab_client)

        mock_config = mocker.Mock()
        type(mock_config).ENABLED_PROVIDERS = PropertyMock(return_value=enabled_providers)

        manager = ProvidersManager(config=mock_config, db=fx_db_client_tmp_db_mig, logger=fx_logger)

        assert len(manager._providers) == 1

    @pytest.mark.parametrize("enabled_providers", [["geotab"], ["aircraft_tracking"]])
    def test_make_providers_error(
        self: Self,
        caplog: pytest.LogCaptureFixture,
        mocker: MockerFixture,
        fx_db_client_tmp_db_mig: DatabaseClient,
        fx_logger: logging.Logger,
        enabled_providers: list[str],
    ):
        """Skips providers that error during creation."""
        provider_title = " ".join(word.capitalize() for word in enabled_providers[0].split("_"))

        mock_config = mocker.Mock()
        type(mock_config).ENABLED_PROVIDERS = PropertyMock(return_value=enabled_providers)

        mocker.patch("assets_tracking_service.providers.geotab.GeotabProvider.__init__", side_effect=RuntimeError)
        mocker.patch(
            "assets_tracking_service.providers.aircraft_tracking.AircraftTrackingProvider.__init__",
            side_effect=RuntimeError,
        )

        manager = ProvidersManager(config=mock_config, db=fx_db_client_tmp_db_mig, logger=fx_logger)

        assert len(manager._providers) == 0
        assert f"{provider_title} provider will be skipped." in caplog.text

    def test_filter_entities(self: Self, fx_providers_manager_no_providers: ProvidersManager, fx_asset_new: AssetNew):
        """Filters entities."""
        db_rows = [{"dist_label_value": "1"}, {"dist_label_value": "2"}]
        fetched_entities = {"2": fx_asset_new, "3": fx_asset_new}
        expected_new_entities = [fx_asset_new]

        assert (
            fx_providers_manager_no_providers._filter_entities(
                db_values=db_rows, indexed_fetched_entities=fetched_entities
            )
            == expected_new_entities
        )

    def test_fetch_active_assets(
        self: Self,
        freezer: FrozenDateTimeFactory,
        caplog: pytest.LogCaptureFixture,
        fx_providers_manager_no_providers: ProvidersManager,
        fx_provider_example: ExampleProvider,
    ):
        """Fetches active assets."""
        freezer.move_to(creation_time)

        fx_providers_manager_no_providers._providers = [fx_provider_example]

        fx_providers_manager_no_providers.fetch_active_assets()

        assets = fx_providers_manager_no_providers._assets.list()
        assert len(assets) == 3
        assert "Persisting 3 new assets from 'example' provider." in caplog.text

        # verify ats:last_fetched label value is set
        assert assets[0].labels.filter_by_scheme("ats:last_fetched").value == 1339338620

    def test_fetch_latest_positions(
        self: Self,
        caplog: pytest.LogCaptureFixture,
        fx_providers_manager_eg_provider: ProvidersManager,
    ):
        """Fetches latest positions."""
        fx_providers_manager_eg_provider.fetch_active_assets()  # to have assets to fetch positions for

        fx_providers_manager_eg_provider.fetch_latest_positions()

        result = fx_providers_manager_eg_provider._db.get_query_result(SQL("""SELECT * FROM public.position;"""))
        assert len(result) == 3
        assert "Persisting 3 new positions from 'example' provider." in caplog.text
