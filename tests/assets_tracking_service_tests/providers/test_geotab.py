import datetime
import logging
from typing import Self

import pytest
from freezegun.api import FrozenDateTimeFactory
from mygeotab import MyGeotabException, TimeoutException
from pytest_mock import MockerFixture
from shapely import Point
from ulid import new as new_ulid

from assets_tracking_service.models.asset import Asset, AssetNew
from assets_tracking_service.models.label import Label, LabelRelation, Labels
from assets_tracking_service.models.position import PositionNew
from assets_tracking_service.providers.geotab import GeotabConfig, GeotabProvider

creation_time = datetime.datetime(2012, 6, 10, 14, 30, 20, tzinfo=datetime.UTC)


class TestGeotabProvider:
    """Geotab provider tests."""

    def test_init(
        self: Self,
        caplog: pytest.LogCaptureFixture,
        mocker: MockerFixture,
        fx_logger: logging.Logger,
        fx_provider_geotab_config: GeotabConfig,
    ):
        """Initialises."""
        mocker.patch("assets_tracking_service.providers.geotab.Geotab", return_value=mocker.MagicMock())

        GeotabProvider(config=fx_provider_geotab_config, logger=fx_logger)

        assert "Creating Geotab SDK client..." in caplog.text

    @pytest.mark.parametrize(
        "config",
        [
            {"password": "x", "database": "x", "nvs_l06_group_mappings": {}},
            {"username": "x", "database": "x", "nvs_l06_group_mappings": {}},
            {"username": "x", "password": "x", "nvs_l06_group_mappings": {}},
            {"username": "x", "password": "x", "database": "x"},
        ],
    )
    def test_init_error_config(self: Self, config: GeotabConfig):
        """Errors if config is invalid."""
        with pytest.raises(RuntimeError, match="Missing required config key"):
            GeotabProvider(config=config, logger=logging.getLogger())

    def test_init_error_geotab(
        self: Self, mocker: MockerFixture, fx_provider_geotab_config: GeotabConfig, fx_logger: logging.Logger
    ):
        """Errors if initialising Geotab fails."""
        mock_geotab_client = mocker.MagicMock(auto_spec=True)
        mock_geotab_client.authenticate.side_effect = MyGeotabException(
            full_error={"errors": [{"name": "Fake Error", "message": "Fake Error."}]}
        )
        mocker.patch("assets_tracking_service.providers.geotab.Geotab", return_value=mock_geotab_client)

        with pytest.raises(RuntimeError, match="Failed to initialise Geotab Provider."):
            GeotabProvider(config=fx_provider_geotab_config, logger=fx_logger)

        mock_geotab_client = mocker.MagicMock(auto_spec=True)
        mock_geotab_client.authenticate.side_effect = TimeoutException(server="Fake Server")
        mocker.patch("assets_tracking_service.providers.geotab.Geotab", return_value=mock_geotab_client)

        with pytest.raises(RuntimeError, match="Failed to initialise Geotab Provider."):
            GeotabProvider(config=fx_provider_geotab_config, logger=fx_logger)

    @pytest.mark.vcr()
    def test_fetch_devices(self: Self, fx_provider_geotab: GeotabProvider):
        """Fetches devices."""
        assert list(fx_provider_geotab._fetch_devices())[0] == {  # noqa: RUF015
            "device_id": "b8",
            "device_serial_number": "000-000-0000",
            "device_name": "GR9 Beta test in Skidoo",
            "device_comment": "GR9 Beta test in Skidoo",
            "device_group_ids": "GroupVehicleId",
        }

    def test_fetch_devices_error(
        self: Self,
        fx_provider_geotab_mocked_error_mygeotab: GeotabProvider,
        fx_provider_geotab_mocked_error_timeout: GeotabProvider,
    ):
        """Errors if fetching devices fails."""
        with pytest.raises(RuntimeError, match="Failed to fetch devices."):
            fx_provider_geotab_mocked_error_mygeotab._fetch_devices()

        with pytest.raises(RuntimeError, match="Failed to fetch devices."):
            fx_provider_geotab_mocked_error_timeout._fetch_devices()

    @pytest.mark.cov()
    def test_fetch_devices_error_keys(
        self: Self,
        caplog: pytest.LogCaptureFixture,
        mocker: MockerFixture,
        fx_provider_geotab_config: GeotabConfig,
        fx_logger: logging.Logger,
    ):
        """Errors if fetching devices fails due to missing keys."""
        mock_geotab_client = mocker.MagicMock(auto_spec=True)
        mock_geotab_client.get.return_value = [
            {},  # invalid
            {"id": "xx", "serialNumber": "000-000-0000"},
            {"id": "xx", "serialNumber": "000-000-0000", "name": "x", "comment": "x", "groups": [{"id": "x"}]},
        ]
        mocker.patch("assets_tracking_service.providers.geotab.Geotab", return_value=mock_geotab_client)

        client = GeotabProvider(config=fx_provider_geotab_config, logger=fx_logger)
        results = client._fetch_devices()

        # the first item is incomplete, and so should be skipped
        assert "Skipping device: 'unknown' due to missing required fields." in caplog.text
        assert len(results) == 2

    @pytest.mark.vcr()
    def test_fetch_device_statuses(self: Self, fx_provider_geotab: GeotabProvider):
        """Fetches device statuses."""
        assert list(fx_provider_geotab._fetch_device_statuses())[0] == {  # noqa: RUF015
            "bearing_degrees": 132.0,
            "date": datetime.datetime(2024, 7, 6, 13, 49, 47, tzinfo=datetime.UTC),
            "device_id": "b7",
            "latitude": 56.0257034,
            "longitude": -3.44706559,
            "speed_km_h": 0.0,
        }

    def test_fetch_device_statuses_error(
        self: Self,
        fx_provider_geotab_mocked_error_mygeotab: GeotabProvider,
        fx_provider_geotab_mocked_error_timeout: GeotabProvider,
    ):
        """Errors if fetching device statuses fails."""
        with pytest.raises(RuntimeError, match="Failed to fetch device statues."):
            fx_provider_geotab_mocked_error_mygeotab._fetch_device_statuses()

        with pytest.raises(RuntimeError, match="Failed to fetch device statues."):
            fx_provider_geotab_mocked_error_timeout._fetch_device_statuses()

    @pytest.mark.cov()
    def test_fetch_devices_statues_error_keys(
        self: Self,
        caplog: pytest.LogCaptureFixture,
        mocker: MockerFixture,
        fx_provider_geotab_config: GeotabConfig,
        fx_logger: logging.Logger,
    ):
        """Errors if fetching device statuses fails due to missing keys."""
        mock_geotab_client = mocker.MagicMock(auto_spec=True)
        mock_geotab_client.get.return_value = [
            {},  # invalid
            {
                "latitude": 1,
                "longitude": 0,
                "dateTime": datetime.datetime.now(tz=datetime.UTC),
                "device": {},
            },  # invalid
            {
                "latitude": 1,
                "longitude": 0,
                "dateTime": datetime.datetime.now(tz=datetime.UTC),
                "device": {"id": "xx"},
            },
            {
                "bearing_degrees": 0,
                "latitude": 1,
                "longitude": 0,
                "speed": 0,
                "dateTime": datetime.datetime.now(tz=datetime.UTC),
                "device": {"id": "xx"},
            },
        ]
        mocker.patch("assets_tracking_service.providers.geotab.Geotab", return_value=mock_geotab_client)

        client = GeotabProvider(config=fx_provider_geotab_config, logger=fx_logger)
        results = client._fetch_device_statuses()

        # the first item is incomplete, and so should be skipped
        assert "Skipping status for device ID: 'null' due to missing required fields." in caplog.text
        assert "Skipping status for device ID: 'unknown' due to missing required fields." in caplog.text
        assert len(results) == 2

    @pytest.mark.vcr()
    def test_fetch_log_record(self: Self, fx_provider_geotab: GeotabProvider):
        """Fetches log record."""
        assert fx_provider_geotab._fetch_log_record(
            device_id="b7", time=datetime.datetime(2024, 7, 6, 13, 49, 47, tzinfo=datetime.UTC)
        ) == {
            "dateTime": datetime.datetime(2024, 7, 6, 13, 49, 47, tzinfo=datetime.UTC),
            "device": {"id": "b7"},
            "id": "b114521",
            "latitude": 56.0257034,
            "longitude": -3.44706559,
            "speed": 0,
        }

    def test_fetch_log_record_error(
        self: Self,
        fx_provider_geotab_mocked_error_mygeotab: GeotabProvider,
        fx_provider_geotab_mocked_error_timeout: GeotabProvider,
    ):
        """Errors if fetching log record fails."""
        device_id = "b7"
        time = datetime.datetime(2024, 7, 6, 13, 49, 47, tzinfo=datetime.UTC)

        with pytest.raises(RuntimeError, match="Failed to fetch LogRecord."):
            fx_provider_geotab_mocked_error_mygeotab._fetch_log_record(device_id=device_id, time=time)

        with pytest.raises(RuntimeError, match="Failed to fetch LogRecord."):
            fx_provider_geotab_mocked_error_timeout._fetch_log_record(device_id=device_id, time=time)

    @pytest.mark.cov()
    def test_fetch_log_record_none(
        self: Self, mocker: MockerFixture, fx_provider_geotab_config: GeotabConfig, fx_logger: logging.Logger
    ):
        """Errors if no log record is found."""
        mock_geotab_client = mocker.MagicMock(auto_spec=True)
        mock_geotab_client.get.return_value = []
        mocker.patch("assets_tracking_service.providers.geotab.Geotab", return_value=mock_geotab_client)

        client = GeotabProvider(config=fx_provider_geotab_config, logger=fx_logger)

        with pytest.raises(IndexError, match="No log record found"):
            client._fetch_log_record(device_id="x", time=datetime.datetime.now(tz=datetime.UTC))

    @pytest.mark.cov()
    def test_fetch_log_record_multiple(
        self: Self, mocker: MockerFixture, fx_provider_geotab_config: GeotabConfig, fx_logger: logging.Logger
    ):
        """Errors if multiple log records are found."""
        mock_geotab_client = mocker.MagicMock(auto_spec=True)
        mock_geotab_client.get.return_value = [1, 2]
        mocker.patch("assets_tracking_service.providers.geotab.Geotab", return_value=mock_geotab_client)

        client = GeotabProvider(config=fx_provider_geotab_config, logger=fx_logger)

        with pytest.raises(IndexError, match="Multiple log records found"):
            client._fetch_log_record(device_id="x", time=datetime.datetime.now(tz=datetime.UTC))

    @pytest.mark.cov()
    def test_index_assets(self: Self, fx_provider_geotab_mocked: GeotabProvider):
        """Indexes assets."""
        key = "y"
        assets = [
            Asset(
                id=new_ulid(),
                labels=Labels(
                    [
                        Label(rel=LabelRelation.SELF, scheme="skos:prefLabel", value="x"),
                        Label(rel=LabelRelation.SELF, scheme="geotab:device_id", value=key),
                    ]
                ),
            )
        ]

        assert fx_provider_geotab_mocked._index_assets(assets=assets) == {key: assets[0]}

    @pytest.mark.vcr()
    def test_fetch_active_assets(self: Self, freezer: FrozenDateTimeFactory, fx_provider_geotab: GeotabProvider):
        """Fetches active assets."""
        freezer.move_to(creation_time)

        expected_asset = AssetNew(
            labels=Labels(
                [
                    Label(rel=LabelRelation.SELF, scheme="skos:prefLabel", value="GR9 Beta test in Skidoo"),
                    Label(
                        rel=LabelRelation.SELF,
                        scheme="nvs:L06",
                        scheme_uri="http://vocab.nerc.ac.uk/collection/L06/current",
                        value="0",
                        value_uri="http://vocab.nerc.ac.uk/collection/L06/current/0",
                    ),
                    Label(rel=LabelRelation.SELF, scheme="geotab:device_id", value="b8"),
                    Label(rel=LabelRelation.SELF, scheme="geotab:device_serial_number", value="000-000-0000"),
                    Label(rel=LabelRelation.SELF, scheme="geotab:device_name", value="GR9 Beta test in Skidoo"),
                    Label(rel=LabelRelation.SELF, scheme="geotab:device_comment", value="GR9 Beta test in Skidoo"),
                    Label(rel=LabelRelation.SELF, scheme="geotab:device_group_ids", value="GroupVehicleId"),
                    Label(rel=LabelRelation.PROVIDER, scheme="ats:provider_id", value="geotab"),
                    Label(rel=LabelRelation.PROVIDER, scheme="ats:provider_version", value="2024-07-02"),
                ]
            )
        )

        # can't use next() here as at least one call to each generator method must get all items to avoid pytest-cov
        # flagging the generator loop has not completed
        assert list(fx_provider_geotab.fetch_active_assets())[0] == expected_asset  # noqa: RUF015

    def test_fetch_active_assets_error(
        self: Self, caplog: pytest.LogCaptureFixture, mocker: MockerFixture, fx_provider_geotab_mocked: GeotabProvider
    ):
        """Errors if fetching active assets fails."""
        mocker.patch.object(fx_provider_geotab_mocked, "_fetch_devices", side_effect=RuntimeError)

        with pytest.raises(RuntimeError):
            next(fx_provider_geotab_mocked.fetch_active_assets())

        assert "Failed to fetch devices from Geotab." in caplog.text

    # noinspection DuplicatedCode
    @pytest.mark.vcr()
    def test_fetch_latest_positions(self: Self, freezer: FrozenDateTimeFactory, fx_provider_geotab: GeotabProvider):
        """Fetches latest positions."""
        freezer.move_to(creation_time)

        asset = Asset(
            id=new_ulid(),
            labels=Labels(
                [
                    Label(rel=LabelRelation.SELF, scheme="skos:prefLabel", value="G20 - RRS Sir David Attenborough"),
                    Label(
                        rel=LabelRelation.SELF,
                        scheme="nvs:L06",
                        scheme_uri="http://vocab.nerc.ac.uk/collection/L06/current",
                        value="31",
                        value_uri="http://vocab.nerc.ac.uk/collection/L06/current/31",
                    ),
                    Label(rel=LabelRelation.SELF, scheme="geotab:device_id", value="b7"),
                    Label(rel=LabelRelation.SELF, scheme="geotab:device_serial_number", value="G907211BC9F4"),
                    Label(
                        rel=LabelRelation.SELF, scheme="geotab:device_name", value="G20 - RRS Sir David Attenborough"
                    ),
                    Label(
                        rel=LabelRelation.SELF, scheme="geotab:device_comment", value="G20 - RRS Sir David Attenborough"
                    ),
                    Label(rel=LabelRelation.SELF, scheme="geotab:device_group_ids", value="GroupVehicleId,b2794"),
                    Label(rel=LabelRelation.PROVIDER, scheme="ats:provider_id", value="geotab"),
                    Label(rel=LabelRelation.PROVIDER, scheme="ats:provider_version", value="2024-07-02"),
                ]
            ),
        )
        expected_position = PositionNew(
            asset_id=asset.id,
            time=datetime.datetime(2024, 7, 6, 18, 12, 58, tzinfo=datetime.UTC),
            geom=Point(-3.44706559, 56.0256767),
            velocity=0.0,
            heading=0.0,
            labels=Labels(
                [
                    Label(rel=LabelRelation.SELF, scheme="geotab:log_record_id", value="b1145C6"),
                    Label(rel=LabelRelation.SELF, scheme="geotab:bearing_degrees", value=0.0),
                    Label(rel=LabelRelation.SELF, scheme="geotab:latitude", value=56.0256767),
                    Label(rel=LabelRelation.SELF, scheme="geotab:longitude", value=-3.44706559),
                    Label(rel=LabelRelation.SELF, scheme="geotab:speed_km_h", value=0.0),
                    Label(rel=LabelRelation.SELF, scheme="geotab:date", value="2024-07-06T18:12:58+00:00"),
                    Label(rel=LabelRelation.SELF, scheme="geotab:device_id", value="b7"),
                    Label(rel=LabelRelation.PROVIDER, scheme="ats:provider_id", value="geotab"),
                    Label(rel=LabelRelation.PROVIDER, scheme="ats:provider_version", value="2024-07-02"),
                ]
            ),
        )

        assert next(fx_provider_geotab.fetch_latest_positions(assets=[asset])) == expected_position

    def test_fetch_latest_positions_error(
        self: Self, caplog: pytest.LogCaptureFixture, mocker: MockerFixture, fx_provider_geotab_mocked: GeotabProvider
    ):
        """Errors if fetching latest positions fails."""
        mocker.patch.object(fx_provider_geotab_mocked, "_fetch_device_statuses", side_effect=RuntimeError)

        with pytest.raises(RuntimeError):
            next(fx_provider_geotab_mocked.fetch_latest_positions(assets=[]))

        assert "Failed to fetch device statuses from Geotab." in caplog.text

    # noinspection DuplicatedCode
    def test_fetch_latest_positions_error_no_asset(
        self: Self, caplog: pytest.LogCaptureFixture, mocker: MockerFixture, fx_provider_geotab_mocked: GeotabProvider
    ):
        """Errors if fetching latest positions fails due to missing asset."""
        mock_device_statuses = [
            {
                "bearing_degrees": -1,
                "date": datetime.datetime(2024, 7, 6, 13, 49, 47, tzinfo=datetime.UTC),
                "device_id": "xx",
                "latitude": 56.0257034,
                "longitude": -3.44706559,
                "speed_km_h": 0.0,
            },  # unknown asset
            {
                "bearing_degrees": -1,
                "date": datetime.datetime(2024, 7, 6, 13, 49, 47, tzinfo=datetime.UTC),
                "device_id": "b7",
                "latitude": 56.0257034,
                "longitude": -3.44706559,
                "speed_km_h": 0.0,
            },
        ]
        mocker.patch.object(
            fx_provider_geotab_mocked, "_fetch_device_statuses", return_value=iter(mock_device_statuses)
        )

        mock_log_record = {
            "dateTime": datetime.datetime(2024, 7, 6, 13, 49, 47, tzinfo=datetime.UTC),
            "device": {"id": "b7"},
            "id": "b114521",
            "latitude": 56.0257034,
            "longitude": -3.44706559,
            "speed": 0,
        }
        mocker.patch.object(fx_provider_geotab_mocked, "_fetch_log_record", return_value=mock_log_record)

        asset = Asset(
            id=new_ulid(),
            labels=Labels(
                [
                    Label(rel=LabelRelation.SELF, scheme="skos:prefLabel", value="G20 - RRS Sir David Attenborough"),
                    Label(
                        rel=LabelRelation.SELF,
                        scheme="nvs:L06",
                        scheme_uri="http://vocab.nerc.ac.uk/collection/L06/current",
                        value="31",
                        value_uri="http://vocab.nerc.ac.uk/collection/L06/current/31",
                    ),
                    Label(rel=LabelRelation.SELF, scheme="geotab:device_id", value="b7"),
                    Label(rel=LabelRelation.SELF, scheme="geotab:device_serial_number", value="G907211BC9F4"),
                    Label(
                        rel=LabelRelation.SELF, scheme="geotab:device_name", value="G20 - RRS Sir David Attenborough"
                    ),
                    Label(
                        rel=LabelRelation.SELF, scheme="geotab:device_comment", value="G20 - RRS Sir David Attenborough"
                    ),
                    Label(rel=LabelRelation.SELF, scheme="geotab:device_group_ids", value="GroupVehicleId,b2794"),
                    Label(rel=LabelRelation.PROVIDER, scheme="ats:provider_id", value="geotab"),
                    Label(rel=LabelRelation.PROVIDER, scheme="ats:provider_version", value="2024-07-02"),
                ]
            ),
        )
        expected_position = PositionNew(
            asset_id=asset.id,
            time=datetime.datetime(2024, 7, 6, 13, 49, 47, tzinfo=datetime.UTC),
            geom=Point(-3.44706559, 56.0257034),
            velocity=0.0,
            heading=None,
            labels=Labels(
                [
                    Label(rel=LabelRelation.SELF, scheme="geotab:log_record_id", value="b114521"),
                    Label(rel=LabelRelation.SELF, scheme="geotab:bearing_degrees", value=-1),
                    Label(rel=LabelRelation.SELF, scheme="geotab:bearing_unknown", value=True),
                    Label(rel=LabelRelation.SELF, scheme="geotab:latitude", value=56.0257034),
                    Label(rel=LabelRelation.SELF, scheme="geotab:longitude", value=-3.44706559),
                    Label(rel=LabelRelation.SELF, scheme="geotab:speed_km_h", value=0.0),
                    Label(rel=LabelRelation.SELF, scheme="geotab:date", value="2024-07-06T13:49:47+00:00"),
                    Label(rel=LabelRelation.SELF, scheme="geotab:device_id", value="b7"),
                    Label(rel=LabelRelation.PROVIDER, scheme="ats:provider_id", value="geotab"),
                    Label(rel=LabelRelation.PROVIDER, scheme="ats:provider_version", value="2024-07-02"),
                ]
            ),
        )

        assert next(fx_provider_geotab_mocked.fetch_latest_positions(assets=[asset])) == expected_position
        assert "Skipping status for device ID: 'xx' as asset not available." in caplog.text

    # noinspection DuplicatedCode
    def test_fetch_latest_positions_error_no_log_record(
        self: Self, caplog: pytest.LogCaptureFixture, mocker: MockerFixture, fx_provider_geotab_mocked: GeotabProvider
    ):
        """Errors if fetching latest positions fails due to missing log record."""
        mock_device_statuses = [
            {
                "bearing_degrees": -1,
                "date": datetime.datetime(2024, 7, 6, 13, 49, 47, tzinfo=datetime.UTC),
                "device_id": "b7",
                "latitude": 56.0257034,
                "longitude": -3.44706559,
                "speed_km_h": 0.0,
            }
        ]
        mocker.patch.object(
            fx_provider_geotab_mocked, "_fetch_device_statuses", return_value=iter(mock_device_statuses)
        )

        mocker.patch.object(fx_provider_geotab_mocked, "_fetch_log_record", side_effect=IndexError)

        asset = Asset(
            id=new_ulid(),
            labels=Labels(
                [
                    Label(rel=LabelRelation.SELF, scheme="skos:prefLabel", value="G20 - RRS Sir David Attenborough"),
                    Label(
                        rel=LabelRelation.SELF,
                        scheme="nvs:L06",
                        scheme_uri="http://vocab.nerc.ac.uk/collection/L06/current",
                        value="31",
                        value_uri="http://vocab.nerc.ac.uk/collection/L06/current/31",
                    ),
                    Label(rel=LabelRelation.SELF, scheme="geotab:device_id", value="b7"),
                    Label(rel=LabelRelation.SELF, scheme="geotab:device_serial_number", value="G907211BC9F4"),
                    Label(
                        rel=LabelRelation.SELF, scheme="geotab:device_name", value="G20 - RRS Sir David Attenborough"
                    ),
                    Label(
                        rel=LabelRelation.SELF, scheme="geotab:device_comment", value="G20 - RRS Sir David Attenborough"
                    ),
                    Label(rel=LabelRelation.SELF, scheme="geotab:device_group_ids", value="GroupVehicleId,b2794"),
                    Label(rel=LabelRelation.PROVIDER, scheme="ats:provider_id", value="geotab"),
                    Label(rel=LabelRelation.PROVIDER, scheme="ats:provider_version", value="2024-07-02"),
                ]
            ),
        )

        assert len(list(fx_provider_geotab_mocked.fetch_latest_positions(assets=[asset]))) == 0
        assert "Skipping status for device ID: 'b7' as LogRecord not available." in caplog.text

    # noinspection DuplicatedCode
    def test_fetch_latest_positions_unknown_heading(
        self: Self, freezer: FrozenDateTimeFactory, mocker: MockerFixture, fx_provider_geotab_mocked: GeotabProvider
    ):
        """Handles fetching latest position with unknown heading."""
        freezer.move_to(creation_time)

        mock_device_statuses = [
            {
                "bearing_degrees": -1,
                "date": datetime.datetime(2024, 7, 6, 13, 49, 47, tzinfo=datetime.UTC),
                "device_id": "b7",
                "latitude": 56.0257034,
                "longitude": -3.44706559,
                "speed_km_h": 0.0,
            }
        ]
        mock_log_record = {
            "dateTime": datetime.datetime(2024, 7, 6, 13, 49, 47, tzinfo=datetime.UTC),
            "device": {"id": "b7"},
            "id": "b114521",
            "latitude": 56.0257034,
            "longitude": -3.44706559,
            "speed": 0,
        }

        asset = Asset(
            id=new_ulid(),
            labels=Labels(
                [
                    Label(rel=LabelRelation.SELF, scheme="skos:prefLabel", value="G20 - RRS Sir David Attenborough"),
                    Label(
                        rel=LabelRelation.SELF,
                        scheme="nvs:L06",
                        scheme_uri="http://vocab.nerc.ac.uk/collection/L06/current",
                        value="31",
                        value_uri="http://vocab.nerc.ac.uk/collection/L06/current/31",
                    ),
                    Label(rel=LabelRelation.SELF, scheme="geotab:device_id", value="b7"),
                    Label(rel=LabelRelation.SELF, scheme="geotab:device_serial_number", value="G907211BC9F4"),
                    Label(
                        rel=LabelRelation.SELF, scheme="geotab:device_name", value="G20 - RRS Sir David Attenborough"
                    ),
                    Label(
                        rel=LabelRelation.SELF, scheme="geotab:device_comment", value="G20 - RRS Sir David Attenborough"
                    ),
                    Label(rel=LabelRelation.SELF, scheme="geotab:device_group_ids", value="GroupVehicleId,b2794"),
                    Label(rel=LabelRelation.PROVIDER, scheme="ats:provider_id", value="geotab"),
                    Label(rel=LabelRelation.PROVIDER, scheme="ats:provider_version", value="2024-07-02"),
                ]
            ),
        )
        expected_position = PositionNew(
            asset_id=asset.id,
            time=datetime.datetime(2024, 7, 6, 13, 49, 47, tzinfo=datetime.UTC),
            geom=Point(-3.44706559, 56.0257034),
            velocity=0.0,
            heading=None,
            labels=Labels(
                [
                    Label(rel=LabelRelation.SELF, scheme="geotab:log_record_id", value="b114521"),
                    Label(rel=LabelRelation.SELF, scheme="geotab:bearing_degrees", value=-1),
                    Label(rel=LabelRelation.SELF, scheme="geotab:bearing_unknown", value=True),
                    Label(rel=LabelRelation.SELF, scheme="geotab:latitude", value=56.0257034),
                    Label(rel=LabelRelation.SELF, scheme="geotab:longitude", value=-3.44706559),
                    Label(rel=LabelRelation.SELF, scheme="geotab:speed_km_h", value=0.0),
                    Label(rel=LabelRelation.SELF, scheme="geotab:date", value="2024-07-06T13:49:47+00:00"),
                    Label(rel=LabelRelation.SELF, scheme="geotab:device_id", value="b7"),
                    Label(rel=LabelRelation.PROVIDER, scheme="ats:provider_id", value="geotab"),
                    Label(rel=LabelRelation.PROVIDER, scheme="ats:provider_version", value="2024-07-02"),
                ]
            ),
        )

        mocker.patch.object(
            fx_provider_geotab_mocked, "_fetch_device_statuses", return_value=iter(mock_device_statuses)
        )
        mocker.patch.object(fx_provider_geotab_mocked, "_fetch_log_record", return_value=mock_log_record)

        # can't use next() here as at least one call to each generator method must get all items to avoid pytest-cov
        # flagging the generator loop has not completed
        position = list(fx_provider_geotab_mocked.fetch_latest_positions(assets=[asset]))[0]  # noqa: RUF015
        assert position == expected_position
