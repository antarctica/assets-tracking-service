import logging
from datetime import UTC, datetime
from typing import Self

import pytest
from freezegun.api import FrozenDateTimeFactory
from pytest_mock import MockerFixture
from requests import HTTPError
from shapely import Point
from ulid import new as new_ulid

from assets_tracking_service.config import Config
from assets_tracking_service.models.asset import Asset, AssetNew
from assets_tracking_service.models.label import Label, LabelRelation, Labels
from assets_tracking_service.models.position import PositionNew
from assets_tracking_service.providers.aircraft_tracking import AircraftTrackingProvider

creation_time = datetime(2012, 6, 10, 14, 30, 20, tzinfo=UTC)


class TestAircraftTrackingProvider:
    """Aircraft Tracking provider tests."""

    def test_init(self: Self, caplog: pytest.LogCaptureFixture, fx_config: Config, fx_logger: logging.Logger):
        """Initialises."""
        AircraftTrackingProvider(config=fx_config, logger=fx_logger)

        assert "Creating Aircraft Tracking SDK client..." in caplog.text
        assert "Aircraft Tracking SDK client created." in caplog.text

    def test_fetch_aircraft(self: Self, mocker: MockerFixture, fx_config: Config, fx_logger: logging.Logger):
        """Fetches aircraft."""
        mock_aircraft_tracker_client = mocker.MagicMock(auto_spec=True)
        mock_aircraft_tracker_client.get_active_aircraft.return_value = [
            {
                "oak": 4658,
                "elm": "70002330",
                "yew": "881651431217",
                "ash": "VP-FAZ",
                "teak": "VP-FAZ",
            }
        ]
        mocker.patch(
            "assets_tracking_service.providers.aircraft_tracking.AircraftTrackerClient",
            return_value=mock_aircraft_tracker_client,
        )

        provider = AircraftTrackingProvider(config=fx_config, logger=fx_logger)

        assert provider._fetch_aircraft()[0] == {
            "aircraft_id": "4658",
            "esn": "70002330",
            "msisdn": "881651431217",
            "name": "VP-FAZ",
            "registration": "VP-FAZ",
        }

    def test_fetch_aircraft_error(self: Self, mocker: MockerFixture, fx_config: Config, fx_logger: logging.Logger):
        """Raises error if fetching aircraft fails."""
        mock_aircraft_tracker_client = mocker.MagicMock(auto_spec=True)
        mock_aircraft_tracker_client.get_active_aircraft.side_effect = HTTPError
        mocker.patch(
            "assets_tracking_service.providers.aircraft_tracking.AircraftTrackerClient",
            return_value=mock_aircraft_tracker_client,
        )

        provider = AircraftTrackingProvider(config=fx_config, logger=fx_logger)

        with pytest.raises(RuntimeError):
            provider._fetch_aircraft()

    def test_fetch_aircraft_error_keys(
        self: Self,
        caplog: pytest.LogCaptureFixture,
        mocker: MockerFixture,
        fx_config: Config,
        fx_logger: logging.Logger,
    ):
        """Raises error if fetched aircraft missing required properties."""
        mock_aircraft_tracker_client = mocker.MagicMock(auto_spec=True)
        mock_aircraft_tracker_client.get_active_aircraft.return_value = [
            {},  # invalid
            {
                "oak": 4658,
                "elm": "70002330",
                "yew": "881651431217",
                "ash": "VP-FAZ",
                "teak": "VP-FAZ",
            },
        ]
        mocker.patch(
            "assets_tracking_service.providers.aircraft_tracking.AircraftTrackerClient",
            return_value=mock_aircraft_tracker_client,
        )

        provider = AircraftTrackingProvider(config=fx_config, logger=fx_logger)

        assert len(provider._fetch_aircraft()) == 1
        assert "Skipping aircraft: 'unknown' due to missing required fields." in caplog.text

    def test_fetch_latest_aircraft_positions(
        self: Self,
        mocker: MockerFixture,
        fx_config: Config,
        fx_logger: logging.Logger,
    ):
        """Fetches latest aircraft positions."""
        mock_aircraft_tracker_client = mocker.MagicMock(auto_spec=True)
        mock_aircraft_tracker_client.get_last_aircraft_positions.return_value = [
            {
                "battenberg": 88803930,
                "carrot": 1,
                "sponge": 1719660930000,
                "christmas": 0,
                "fruit": 0,
                "lemon_drizzle": 0,
                "victoria": 1719660925000,
                "banana": 4658,
                "cheesecake": 0,
                "fudge": 0,
            }
        ]
        mocker.patch(
            "assets_tracking_service.providers.aircraft_tracking.AircraftTrackerClient",
            return_value=mock_aircraft_tracker_client,
        )

        provider = AircraftTrackingProvider(config=fx_config, logger=fx_logger)

        assert provider._fetch_latest_positions()[0] == {
            "position_id": "88803930",
            "speed_knots": 0.0,
            "altitude_feet": 0.0,
            "heading_degrees": 0.0,
            "utc_milliseconds": 1719660925000,
            "aircraft_id": "4658",
            "longitude": 0.0,
            "latitude": 0.0,
        }

    def test_fetch_latest_aircraft_positions_error(
        self: Self,
        mocker: MockerFixture,
        fx_config: Config,
        fx_logger: logging.Logger,
    ):
        """Raises error if fetching aircraft positions fails."""
        mock_aircraft_tracker_client = mocker.MagicMock(auto_spec=True)
        mock_aircraft_tracker_client.get_last_aircraft_positions.side_effect = HTTPError
        mocker.patch(
            "assets_tracking_service.providers.aircraft_tracking.AircraftTrackerClient",
            return_value=mock_aircraft_tracker_client,
        )

        provider = AircraftTrackingProvider(config=fx_config, logger=fx_logger)

        with pytest.raises(RuntimeError):
            provider._fetch_latest_positions()

    def test_fetch_latest_aircraft_positions_error_keys(
        self: Self,
        caplog: pytest.LogCaptureFixture,
        mocker: MockerFixture,
        fx_config: Config,
        fx_logger: logging.Logger,
    ):
        """Raises error if fetched aircraft positions missing required properties."""
        mock_aircraft_tracker_client = mocker.MagicMock(auto_spec=True)
        mock_aircraft_tracker_client.get_last_aircraft_positions.return_value = [
            {},  # invalid
            {
                "battenberg": 88803930,
                "carrot": 1,
                "sponge": 1719660930000,
                "christmas": 0,
                "fruit": 0,
                "lemon_drizzle": 0,
                "victoria": 1719660925000,
                "banana": 4658,
                "cheesecake": 0,
                "fudge": 0,
            },
        ]
        mocker.patch(
            "assets_tracking_service.providers.aircraft_tracking.AircraftTrackerClient",
            return_value=mock_aircraft_tracker_client,
        )

        provider = AircraftTrackingProvider(config=fx_config, logger=fx_logger)

        assert len(provider._fetch_latest_positions()) == 1
        assert (
            "Skipping position ID 'unknown' for aircraft ID: 'unknown' due to missing required fields." in caplog.text
        )

    def test_fetch_active_assets(
        self: Self,
        freezer: FrozenDateTimeFactory,
        mocker: MockerFixture,
        fx_provider_aircraft_tracking: AircraftTrackingProvider,
    ):
        """Fetches active assets."""
        freezer.move_to(creation_time)

        expected_asset = AssetNew(
            labels=Labels(
                [
                    Label(rel=LabelRelation.SELF, scheme="aircraft_tracking:aircraft_id", value="4658"),
                    Label(rel=LabelRelation.SELF, scheme="skos:prefLabel", value="VP-FAZ"),
                    Label(
                        rel=LabelRelation.SELF,
                        scheme="nvs:L06",
                        scheme_uri="http://vocab.nerc.ac.uk/collection/L06/current",
                        value="62",
                        value_uri="http://vocab.nerc.ac.uk/collection/L06/current/62",
                    ),
                    Label(rel=LabelRelation.SELF, scheme="aircraft_tracking:aircraft_id", value="4658"),
                    Label(rel=LabelRelation.SELF, scheme="aircraft_tracking:esn", value="70002330"),
                    Label(rel=LabelRelation.SELF, scheme="aircraft_tracking:msisdn", value="881651431217"),
                    Label(rel=LabelRelation.SELF, scheme="aircraft_tracking:name", value="VP-FAZ"),
                    Label(rel=LabelRelation.SELF, scheme="aircraft_tracking:registration", value="VP-FAZ"),
                    Label(rel=LabelRelation.PROVIDER, scheme="ats:provider_id", value="aircraft_tracking"),
                    Label(rel=LabelRelation.PROVIDER, scheme="ats:provider_version", value="2024-07-05"),
                ]
            )
        )

        aircraft = [
            {
                "aircraft_id": "4658",
                "esn": "70002330",
                "msisdn": "881651431217",
                "name": "VP-FAZ",
                "registration": "VP-FAZ",
            }
        ]
        mocker.patch.object(fx_provider_aircraft_tracking, "_fetch_aircraft", return_value=aircraft)

        assert list(fx_provider_aircraft_tracking.fetch_active_assets())[0] == expected_asset  # noqa: RUF015

    def test_fetch_active_assets_error(
        self: Self, mocker: MockerFixture, fx_provider_aircraft_tracking: AircraftTrackingProvider
    ):
        """Raises error if fetching active assets fails."""
        mocker.patch.object(fx_provider_aircraft_tracking, "_fetch_aircraft", side_effect=RuntimeError)

        with pytest.raises(RuntimeError, match="Failed to fetch aircraft from provider."):
            next(fx_provider_aircraft_tracking.fetch_active_assets())

    def test_fetch_latest_positions(
        self: Self,
        freezer: FrozenDateTimeFactory,
        mocker: MockerFixture,
        fx_provider_aircraft_tracking: AircraftTrackingProvider,
    ):
        """Fetches latest positions."""
        freezer.move_to(creation_time)

        asset = Asset(
            id=new_ulid(),
            labels=Labels(
                [
                    Label(rel=LabelRelation.SELF, scheme="aircraft_tracking:aircraft_id", value="4658"),
                    Label(rel=LabelRelation.SELF, scheme="skos:prefLabel", value="VP-FAZ"),
                    Label(
                        rel=LabelRelation.SELF,
                        scheme="nvs:L06",
                        scheme_uri="http://vocab.nerc.ac.uk/collection/L06/current",
                        value="62",
                        value_uri="http://vocab.nerc.ac.uk/collection/L06/current/62",
                    ),
                    Label(rel=LabelRelation.SELF, scheme="aircraft_tracking:aircraft_id", value="4658"),
                    Label(rel=LabelRelation.SELF, scheme="aircraft_tracking:esn", value="70002330"),
                    Label(rel=LabelRelation.SELF, scheme="aircraft_tracking:msisdn", value="881651431217"),
                    Label(rel=LabelRelation.SELF, scheme="aircraft_tracking:name", value="VP-FAZ"),
                    Label(rel=LabelRelation.SELF, scheme="aircraft_tracking:registration", value="VP-FAZ"),
                    Label(rel=LabelRelation.PROVIDER, scheme="ats:provider_id", value="aircraft_tracking"),
                    Label(rel=LabelRelation.PROVIDER, scheme="ats:provider_version", value="2024-07-05"),
                ]
            ),
        )
        expected_position = PositionNew(
            asset_id=asset.id,
            time=datetime(2024, 6, 29, 11, 35, 25, tzinfo=UTC),
            geom=Point(1.0, 2.0, 9143.999999999998),
            velocity=6.173333333333334,
            heading=67.2,
            labels=Labels(
                [
                    Label(rel=LabelRelation.SELF, scheme="aircraft_tracking:position_id", value="88803930"),
                    Label(rel=LabelRelation.SELF, scheme="aircraft_tracking:position_id", value="88803930"),
                    Label(rel=LabelRelation.SELF, scheme="aircraft_tracking:speed_knots", value=12),
                    Label(rel=LabelRelation.SELF, scheme="aircraft_tracking:altitude_feet", value=30000),
                    Label(rel=LabelRelation.SELF, scheme="aircraft_tracking:heading_degrees", value=67.2),
                    Label(rel=LabelRelation.SELF, scheme="aircraft_tracking:utc_milliseconds", value=1719660925000),
                    Label(rel=LabelRelation.SELF, scheme="aircraft_tracking:aircraft_id", value="4658"),
                    Label(rel=LabelRelation.SELF, scheme="aircraft_tracking:longitude", value=1.0),
                    Label(rel=LabelRelation.SELF, scheme="aircraft_tracking:latitude", value=2.0),
                    Label(rel=LabelRelation.PROVIDER, scheme="ats:provider_id", value="aircraft_tracking"),
                    Label(rel=LabelRelation.PROVIDER, scheme="ats:provider_version", value="2024-07-05"),
                ]
            ),
        )

        positions = [
            {
                "position_id": "88803930",
                "speed_knots": 12,
                "altitude_feet": 30_000,
                "heading_degrees": 67.2,
                "utc_milliseconds": 1719660925000,
                "aircraft_id": "4658",
                "longitude": 1.0,
                "latitude": 2.0,
            }
        ]
        mocker.patch.object(fx_provider_aircraft_tracking, "_fetch_latest_positions", return_value=positions)

        position = next(fx_provider_aircraft_tracking.fetch_latest_positions(assets=[asset]))

        assert position == expected_position

    def test_fetch_latest_positions_error(
        self: Self, mocker: MockerFixture, fx_provider_aircraft_tracking: AircraftTrackingProvider
    ):
        """Raises error if fetching latest positions fails."""
        mocker.patch.object(fx_provider_aircraft_tracking, "_fetch_latest_positions", side_effect=RuntimeError)

        with pytest.raises(RuntimeError, match="Failed to fetch aircraft positions from provider."):
            next(fx_provider_aircraft_tracking.fetch_latest_positions(assets=[]))

    def test_fetch_latest_positions_error_no_asset(
        self: Self,
        caplog: pytest.LogCaptureFixture,
        mocker: MockerFixture,
        fx_provider_aircraft_tracking: AircraftTrackingProvider,
    ):
        """Skips positions for assets not available."""
        positions = [
            {
                "position_id": "88803930",
                "speed_knots": 0.0,
                "altitude_feet": 0.0,
                "heading_degrees": 0.0,
                "utc_milliseconds": 1719660925000,
                "aircraft_id": "4658",
                "longitude": 0.0,
                "latitude": 0.0,
            }
        ]
        mocker.patch.object(fx_provider_aircraft_tracking, "_fetch_latest_positions", return_value=positions)

        assert len(list(fx_provider_aircraft_tracking.fetch_latest_positions(assets=[]))) == 0
        assert "Skipping position for aircraft ID: '4658' as asset not available." in caplog.text
