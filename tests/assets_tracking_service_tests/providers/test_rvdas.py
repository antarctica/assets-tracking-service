import logging
from datetime import UTC, datetime

import pytest
from freezegun.api import FrozenDateTimeFactory
from pytest_mock import MockerFixture
from shapely.geometry.point import Point
from ulid import new as new_ulid

from assets_tracking_service.config import Config
from assets_tracking_service.models.asset import Asset, AssetNew
from assets_tracking_service.models.label import Label, LabelRelation, Labels
from assets_tracking_service.models.position import PositionNew
from assets_tracking_service.providers.rvdas import RvdasProvider

creation_time = datetime(2012, 6, 10, 14, 30, 20, tzinfo=UTC)


class TestRvdasProvider:
    """RVDAS provider tests."""

    def test_init(self, caplog: pytest.LogCaptureFixture, fx_config: Config, fx_logger: logging.Logger):
        """Can initialise provider."""
        RvdasProvider(config=fx_config, logger=fx_logger)

        assert "Setting RVDAS configuration.." in caplog.text
        assert "RVDAS configuration ok." in caplog.text

    def test_fetch_vessels(self, fx_config: Config, fx_logger: logging.Logger):
        """Can fetch vessels."""
        provider = RvdasProvider(config=fx_config, logger=fx_logger)

        assert provider._fetch_vessels()[0] == {
            "_fake_vessel_id": "1",
            "name": "SIR DAVID ATTENBOROUGH",
            "imo": "9798222",
        }

    @pytest.mark.vcr()
    def test_fetch_data(self, fx_config: Config, fx_logger: logging.Logger):
        """Can fetch raw data from provider."""
        provider = RvdasProvider(config=fx_config, logger=fx_logger)
        data = provider._fetch_data()
        assert isinstance(data, dict)

    @pytest.mark.vcr()
    def test_fetch_data_invalid(self, fx_config: Config, fx_logger: logging.Logger):
        """Cannot fetch raw data if HTTP response is not valid JSON."""
        provider = RvdasProvider(config=fx_config, logger=fx_logger)

        with pytest.raises(RuntimeError, match="Failed to parse HTTP response as JSON."):
            provider._fetch_data()

    @pytest.mark.vcr()
    def test_fetch_data_error(self, mocker: MockerFixture, fx_config: Config, fx_logger: logging.Logger):
        """Cannot fetch raw data if an HTTP errors occurs."""
        provider = RvdasProvider(config=fx_config, logger=fx_logger)

        with pytest.raises(RuntimeError, match="Failed to fetch HTTP response."):
            provider._fetch_data()

    def test_fetch_latest_vessel_positions(self, mocker: MockerFixture, fx_config: Config, fx_logger: logging.Logger):
        """Can fetch latest vessel positions."""
        payload = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [-45.579345917, -60.701441817]},
                    "properties": {
                        "depth_from_transducer": 1189.5,
                        "depth_time": "2025-04-1002:59:42.098+00",
                        "gps_time": "2025-04-12 12:09:34.729+00",
                        "heading_time": "2025-04-12 12:09:34.715+00",
                        "headingtrue": 299.55,
                        "lat": -60.70144181666667,
                        "lon": -45.57934591666666,
                        "now_time": "2025-04-12 12:09:35.127674+00",
                        "speed_time": "2025-04-12 12:09:34.729+00",
                        "speedknots": 0.1,
                    },
                }
            ],
            "numberReturned": 1,
            "timeStamp": "2025-04-12T12:09:35Z",
            "links": [
                {
                    "href": "https://example.com/items.json",
                    "rel": "self",
                    "type": "application/json",
                    "title": "This document as JSON",
                },
                {
                    "href": "https://example.com/items.html",
                    "rel": "alternate",
                    "type": "text/html",
                    "title": "This document as HTML",
                },
            ],
        }
        provider = RvdasProvider(config=fx_config, logger=fx_logger)
        mocker.patch.object(provider, "_fetch_data", return_value=payload)

        assert provider._fetch_latest_positions()[0] == {
            "longitude": -45.579345917,
            "latitude": -60.701441817,
            "speedknots": 0.1,
            "headingtrue": 299.55,
            "gps_time": "2025-04-12 12:09:34.729+00",
            "_fake_vessel_id": "1",
            "_fake_position_id": "606689e87a8b33fcf8170d51cd4e956b",
        }

    @pytest.mark.parametrize(
        ("data", "msg"),
        [
            ({"x": "x"}, "Failed to parse feature collection."),
            ({"type": "FeatureCollection"}, "Failed to parse feature collection."),
            (
                {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "geometry": {},
                        }
                    ],
                },
                "Failed to parse feature collection.",
            ),
            (
                {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "geometry": {"type": "x"},
                        }
                    ],
                },
                "Expected feature to use a Point geometry.",
            ),
            (
                {
                    "type": "FeatureCollection",
                    "features": [],
                },
                "Expected exactly 1 feature in feature collection, found 0.",
            ),
            (
                {
                    "type": "FeatureCollection",
                    "features": [{"x": "x"}, {"x": "x"}],
                },
                "Expected exactly 1 feature in feature collection, found 2.",
            ),
        ],
    )
    def test_fetch_latest_vessel_positions_invalid(
        self, mocker: MockerFixture, fx_config: Config, fx_logger: logging.Logger, data: dict, msg: str
    ):
        """Cannot fetch latest vessel positions when invalid GeoJSON is returned."""
        provider = RvdasProvider(config=fx_config, logger=fx_logger)
        mocker.patch.object(provider, "_fetch_data", return_value=data)

        with pytest.raises(RuntimeError, match=msg):
            provider._fetch_latest_positions()

    @pytest.mark.parametrize("key", ["speedknots", "headingtrue", "gps_time"])
    def test_fetch_latest_vessel_positions_incomplete(
        self, mocker: MockerFixture, fx_config: Config, fx_logger: logging.Logger, key: str
    ):
        """Cannot fetch a vessel position when its missing required feature properties."""
        payload = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [-45.579345917, -60.701441817]},
                    "properties": {
                        "depth_from_transducer": 1189.5,
                        "depth_time": "2025-04-1002:59:42.098+00",
                        "gps_time": "2025-04-12 12:09:34.729+00",
                        "heading_time": "2025-04-12 12:09:34.715+00",
                        "headingtrue": 299.55,
                        "lat": -60.70144181666667,
                        "lon": -45.57934591666666,
                        "now_time": "2025-04-12 12:09:35.127674+00",
                        "speed_time": "2025-04-12 12:09:34.729+00",
                        "speedknots": 0.1,
                    },
                }
            ],
            "numberReturned": 1,
            "timeStamp": "2025-04-12T12:09:35Z",
            "links": [
                {
                    "href": "https://example.com/items.json",
                    "rel": "self",
                    "type": "application/json",
                    "title": "This document as JSON",
                },
                {
                    "href": "https://example.com/items.html",
                    "rel": "alternate",
                    "type": "text/html",
                    "title": "This document as HTML",
                },
            ],
        }
        del payload["features"][0]["properties"][key]
        provider = RvdasProvider(config=fx_config, logger=fx_logger)
        mocker.patch.object(provider, "_fetch_data", return_value=payload)

        assert len(provider._fetch_latest_positions()) == 0

    def test_fetch_active_assets(self, freezer: FrozenDateTimeFactory, fx_provider_rvdas: RvdasProvider):
        """Fetches active assets."""
        freezer.move_to(creation_time)

        expected_asset = AssetNew(
            labels=Labels(
                [
                    Label(rel=LabelRelation.SELF, scheme="rvdas:_fake_vessel_id", value="1"),
                    Label(rel=LabelRelation.SELF, scheme="skos:prefLabel", value="SIR DAVID ATTENBOROUGH"),
                    Label(
                        rel=LabelRelation.SELF,
                        scheme="nvs:L06",
                        scheme_uri="http://vocab.nerc.ac.uk/collection/L06/current",
                        value="31",
                        value_uri="http://vocab.nerc.ac.uk/collection/L06/current/31",
                    ),
                    Label(rel=LabelRelation.SELF, scheme="rvdas:name", value="SIR DAVID ATTENBOROUGH"),
                    Label(rel=LabelRelation.SELF, scheme="rvdas:imo", value="9798222"),
                    Label(rel=LabelRelation.PROVIDER, scheme="ats:provider_id", value="rvdas"),
                    Label(rel=LabelRelation.PROVIDER, scheme="ats:provider_version", value="2025-04-12"),
                ]
            )
        )

        assert list(iter(fx_provider_rvdas.fetch_active_assets()))[0] == expected_asset  # noqa: RUF015

    def test_fetch_active_assets_error(self, mocker: MockerFixture, fx_provider_rvdas: RvdasProvider):
        """Raises error if fetching active assets fails."""
        mocker.patch.object(fx_provider_rvdas, "_fetch_vessels", side_effect=RuntimeError)

        with pytest.raises(RuntimeError, match="Failed to fetch vessels from provider."):
            next(fx_provider_rvdas.fetch_active_assets())

    def test_fetch_latest_positions(self, freezer: FrozenDateTimeFactory, fx_provider_rvdas: RvdasProvider):
        """Fetches latest positions."""
        freezer.move_to(creation_time)

        asset = Asset(
            id=new_ulid(),
            labels=Labels(
                [
                    Label(rel=LabelRelation.SELF, scheme="rvdas:_fake_vessel_id", value="1"),
                    Label(rel=LabelRelation.SELF, scheme="skos:prefLabel", value="SIR DAVID ATTENBOROUGH"),
                    Label(
                        rel=LabelRelation.SELF,
                        scheme="nvs:L06",
                        scheme_uri="http://vocab.nerc.ac.uk/collection/L06/current",
                        value="31",
                        value_uri="http://vocab.nerc.ac.uk/collection/L06/current/31",
                    ),
                    Label(rel=LabelRelation.SELF, scheme="rvdas:name", value="SIR DAVID ATTENBOROUGH"),
                    Label(rel=LabelRelation.SELF, scheme="rvdas:imo", value="9798222"),
                    Label(rel=LabelRelation.PROVIDER, scheme="ats:provider_id", value="rvdas"),
                    Label(rel=LabelRelation.PROVIDER, scheme="ats:provider_version", value="2025-04-12"),
                ]
            ),
        )

        expected_position = PositionNew(
            asset_id=asset.id,
            time=datetime(2025, 4, 12, 12, 9, 34, tzinfo=UTC),
            geom=Point(-45.579346, -60.701442),
            velocity=0.05144444444444445,
            heading=299.55,
            labels=Labels(
                [
                    Label(
                        rel=LabelRelation.SELF,
                        scheme="rvdas:_fake_position_id",
                        value="c28c61d85e803b933c722bef9307cf76",
                    ),
                    Label(rel=LabelRelation.SELF, scheme="rvdas:_fake_vessel_id", value="1"),
                    Label(rel=LabelRelation.SELF, scheme="rvdas:speedknots", value=0.1),
                    Label(rel=LabelRelation.SELF, scheme="rvdas:headingtrue", value=299.55),
                    Label(rel=LabelRelation.SELF, scheme="rvdas:gps_time", value="2025-04-12 12:09:34.729+00"),
                    Label(rel=LabelRelation.SELF, scheme="rvdas:longitude", value=-45.579346),
                    Label(rel=LabelRelation.SELF, scheme="rvdas:latitude", value=-60.701442),
                    Label(rel=LabelRelation.PROVIDER, scheme="ats:provider_id", value="rvdas"),
                    Label(rel=LabelRelation.PROVIDER, scheme="ats:provider_version", value="2025-04-12"),
                ]
            ),
        )

        position = next(fx_provider_rvdas.fetch_latest_positions(assets=[asset]))

        assert position == expected_position

    def test_fetch_latest_positions_error(self, mocker: MockerFixture, fx_provider_rvdas: RvdasProvider):
        """Raises error if fetching latest positions fails."""
        mocker.patch.object(fx_provider_rvdas, "_fetch_latest_positions", side_effect=RuntimeError)

        with pytest.raises(RuntimeError, match="Failed to fetch vessel positions from provider."):
            next(fx_provider_rvdas.fetch_latest_positions(assets=[]))

    def test_fetch_latest_positions_error_no_asset(
        self,
        caplog: pytest.LogCaptureFixture,
        fx_provider_rvdas: RvdasProvider,
    ):
        """Skips positions for assets not available."""
        assert len(list(fx_provider_rvdas.fetch_latest_positions(assets=[]))) == 0
        assert "Skipping position for vessel ID: '1' as asset not available." in caplog.text
