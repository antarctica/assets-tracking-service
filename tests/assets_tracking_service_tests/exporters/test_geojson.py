import logging

import pytest
from geojson import FeatureCollection, load as geojson_load

from assets_tracking_service.config import Config
from assets_tracking_service.db import DatabaseClient
from assets_tracking_service.exporters.geojson import GeoJsonExporter


class TestExporterGeoJson:
    def test_init(self, fx_config: Config, fx_db_client_tmp_db_mig: DatabaseClient, fx_logger: logging.Logger):
        GeoJsonExporter(config=fx_config, db=fx_db_client_tmp_db_mig, logger=fx_logger)

    def test_data(self, fx_exporter_geojson: GeoJsonExporter):
        result = fx_exporter_geojson.data

        assert isinstance(result, FeatureCollection)
        assert result.is_valid
        assert len(result["features"]) > 0

    def test_data_keys_order(self, fx_exporter_geojson: GeoJsonExporter):
        """Feature property keys are in expected order (sanity check)."""
        expected_order = [
            "asset_id",
            "position_id",
            "name",
            "type_code",
            "type_label",
            "time_utc",
            "last_fetched_utc",
            "lat_dd",
            "lon_dd",
            "lat_dms",
            "lon_dms",
            "elv_m",
            "elv_ft",
            "speed_ms",
            "speed_kmh",
            "speed_kn",
            "heading_d",
        ]
        result = fx_exporter_geojson.data
        feature_props = result["features"][0]["properties"]

        assert list(feature_props.keys()) == expected_order

    @pytest.mark.cov
    def test_data_empty(self, fx_config: Config, fx_db_client_tmp_db_mig: DatabaseClient, fx_logger: logging.Logger):
        """Handles empty features list."""
        exporter = GeoJsonExporter(config=fx_config, db=fx_db_client_tmp_db_mig, logger=fx_logger)

        result = exporter.data

        assert isinstance(result, FeatureCollection)
        assert result.is_valid
        assert len(result["features"]) == 0

    def test_export(self, fx_exporter_geojson: GeoJsonExporter):
        """Handles empty features list."""
        expected_path = fx_exporter_geojson._config.EXPORTER_GEOJSON_OUTPUT_PATH

        fx_exporter_geojson.export()

        assert expected_path.exists()

        # verify file is valid GeoJSON
        with expected_path.open("r") as f:
            fc: FeatureCollection = geojson_load(f)
            assert fc.is_valid