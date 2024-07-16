import logging
from unittest.mock import PropertyMock

import pytest
from pytest_mock import MockerFixture

from assets_tracking_service.config import Config
from assets_tracking_service.db import DatabaseClient
from assets_tracking_service.exporters.exporters_manager import ExportersManager
from tests.examples.example_exporter import ExampleExporter


class TestExportersManager:
    def test_init(
        self,
        fx_config: Config,
        fx_db_client_tmp_db_mig: DatabaseClient,
        fx_logger: logging.Logger,
    ):
        manager = ExportersManager(config=fx_config, db=fx_db_client_tmp_db_mig, logger=fx_logger)

        assert len(manager._exporters) > 0

    def test_init_no_providers(
        self, mocker: MockerFixture, fx_db_client_tmp_db_mig: DatabaseClient, fx_logger: logging.Logger
    ):
        mock_config = mocker.Mock()
        type(mock_config).enabled_exporters = PropertyMock(return_value=[])
        manager = ExportersManager(config=mock_config, db=fx_db_client_tmp_db_mig, logger=fx_logger)

        assert len(manager._exporters) == 0

    @pytest.mark.parametrize("enabled_exporters", [["geojson"]])
    def test_make_each_exporter(
        self,
        mocker: MockerFixture,
        fx_db_client_tmp_db_pop: DatabaseClient,
        fx_logger: logging.Logger,
        enabled_exporters: list[str],
    ):
        mock_config = mocker.Mock()
        type(mock_config).enabled_exporters = PropertyMock(return_value=enabled_exporters)

        manager = ExportersManager(config=mock_config, db=fx_db_client_tmp_db_pop, logger=fx_logger)

        assert len(manager._exporters) == 1

    def test_fetch_active_assets(
        self,
        mocker: MockerFixture,
        caplog: pytest.LogCaptureFixture,
        fx_exporters_manager_no_exporters: ExportersManager,
        fx_exporter_example: ExampleExporter,
    ):
        mock_geojson_exporter = mocker.MagicMock(auto_spec=True)
        mocker.patch(
            "assets_tracking_service.exporters.exporters_manager.GeoJsonExporter", return_value=mock_geojson_exporter
        )

        fx_exporters_manager_no_exporters._exporters = [fx_exporter_example]

        fx_exporters_manager_no_exporters.export()
