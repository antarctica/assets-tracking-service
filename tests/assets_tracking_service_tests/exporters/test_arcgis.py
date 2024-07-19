import logging
from pathlib import Path

import pytest
from geojson import FeatureCollection, load as geojson_load
from pytest_mock import MockerFixture

from assets_tracking_service.config import Config
from assets_tracking_service.db import DatabaseClient
from assets_tracking_service.exporters.arcgis import ArcGISExporter, ArcGISAuthenticationError


class TestExporterArcGIS:
    def test_init(self, mocker: MockerFixture, fx_config: Config, fx_db_client_tmp_db_mig: DatabaseClient, fx_logger: logging.Logger):
        mocker.patch("assets_tracking_service.exporters.arcgis.GIS", return_value=mocker.MagicMock(auto_spec=True))

        ArcGISExporter(config=fx_config, db=fx_db_client_tmp_db_mig, logger=fx_logger)

    def test_init_auth_error(self, mocker: MockerFixture, fx_config: Config, fx_db_client_tmp_db_mig: DatabaseClient, fx_logger: logging.Logger):
        mocker.patch("assets_tracking_service.exporters.arcgis.GIS", side_effect=Exception("Invalid username or password"))

        with pytest.raises(ArcGISAuthenticationError):
            ArcGISExporter(config=fx_config, db=fx_db_client_tmp_db_mig, logger=fx_logger)

    def test_get_data_with_name(self, fx_exporter_arcgis: ArcGISExporter):
        expected = "foo.geojson"
        result = fx_exporter_arcgis._get_data_with_name(name=Path(expected))

        assert result.exists()
        assert result.name == expected

        # verify file is valid GeoJSON
        with result.open("r") as f:
            fc: FeatureCollection = geojson_load(f)
            assert isinstance(fc, FeatureCollection)
            assert fc.is_valid
            assert len(fc["features"]) > 0

        # cleanup temporary directory
        fx_exporter_arcgis._output_path.cleanup()
        if fx_exporter_arcgis._output_path:
            assert not Path(fx_exporter_arcgis._output_path.name).exists()

    def test_overwrite_fs_data(self, fx_exporter_arcgis: ArcGISExporter):
        fx_exporter_arcgis._overwrite_fs_data()

    def test_export(self, fx_exporter_arcgis: ArcGISExporter):
        fx_exporter_arcgis.export()
