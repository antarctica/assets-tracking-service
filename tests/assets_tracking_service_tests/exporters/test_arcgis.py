import logging

import pytest
from arcgis.gis import ItemTypeEnum, SharingLevel
from geojson import FeatureCollection
from pytest_mock import MockerFixture

from assets_tracking_service.config import Config
from assets_tracking_service.db import DatabaseClient
from assets_tracking_service.exporters.arcgis import (
    ArcGISAuthenticationError,
    ArcGisExporter,
    ArcGisExporterLayer,
)
from assets_tracking_service.models.layer import Layer, LayersClient


class TestArcGisExporterLayer:
    """ArcGIS exporter layer tests."""

    def test_init(
        self,
        mocker: MockerFixture,
        fx_config: Config,
        fx_db_client_tmp_db_mig: DatabaseClient,
        fx_logger: logging.Logger,
        fx_record_layer_slug: str,
    ):
        """Initialises."""
        layers_client = LayersClient(db_client=fx_db_client_tmp_db_mig, logger=fx_logger)

        mock_gis = mocker.MagicMock(auto_spec=True)
        mocker.patch("assets_tracking_service.exporters.arcgis.GIS", return_value=mock_gis)
        mocker.patch(
            "assets_tracking_service.exporters.arcgis.ArcGisClient", return_value=mocker.MagicMock(auto_spec=True)
        )

        ArcGisExporterLayer(
            config=fx_config,
            db=fx_db_client_tmp_db_mig,
            logger=fx_logger,
            arcgis=mock_gis,
            layers=layers_client,
            layer_slug=fx_record_layer_slug,
        )

    def test_catalogue_item_arc_geojson(self, fx_exporter_arcgis_layer_updated: ArcGisExporterLayer):
        """Get layer as catalogue ArcGIS GeoJSON item."""
        item = fx_exporter_arcgis_layer_updated._catalogue_item_arc_geojson

        assert item is not None
        assert item.item_id is not None
        assert item.item_type == ItemTypeEnum.GEOJSON

        # check access level override
        assert item.sharing_level == SharingLevel.PRIVATE

    def test_catalogue_item_arc_feature(self, fx_exporter_arcgis_layer_updated: ArcGisExporterLayer):
        """Get layer as catalogue ArcGIS feature item."""
        item = fx_exporter_arcgis_layer_updated._catalogue_item_arc_feature

        assert item is not None
        assert item.item_id is not None
        assert item.item_type == ItemTypeEnum.FEATURE_SERVICE

    def test_catalogue_item_arc_ogc_feature(self, fx_exporter_arcgis_layer_updated: ArcGisExporterLayer):
        """Get layer as catalogue ArcGIS OGC feature item."""
        item = fx_exporter_arcgis_layer_updated._catalogue_item_arc_ogc_feature

        assert item is not None
        assert item.item_id is not None
        assert item.item_type == ItemTypeEnum.OGCFEATURESERVER

    def test_get_layer(self, fx_exporter_arcgis_layer: ArcGisExporterLayer, fx_layer_init: Layer):
        """Get Layer."""
        layer = fx_exporter_arcgis_layer._get_layer()

        assert layer == fx_layer_init

    def test_get_data(self, fx_exporter_arcgis_layer: ArcGisExporterLayer):
        """Get data."""
        data = fx_exporter_arcgis_layer._get_data()

        assert isinstance(data, FeatureCollection)

    def test_setup(self, fx_exporter_arcgis_layer: ArcGisExporterLayer):
        """Creates items for layer."""
        fx_exporter_arcgis_layer.setup()

        # Very updated layer
        layer = fx_exporter_arcgis_layer._layers.get_by_slug(fx_exporter_arcgis_layer._slug)
        assert layer.metadata_last_refreshed is not None
        assert layer.agol_id_geojson is not None
        assert layer.agol_id_feature is not None
        assert layer.agol_id_feature_ogc is not None

    def test_setup_skipped(self, fx_exporter_arcgis_layer: ArcGisExporterLayer):
        """Skips creating items for layer when already setup."""
        fx_exporter_arcgis_layer.setup()
        layer_setup_first = fx_exporter_arcgis_layer._layers.get_by_slug(fx_exporter_arcgis_layer._slug)

        fx_exporter_arcgis_layer.setup()
        layer_setup_second = fx_exporter_arcgis_layer._layers.get_by_slug(fx_exporter_arcgis_layer._slug)

        # Verify layer has not changed
        assert layer_setup_first.metadata_last_refreshed == layer_setup_second.metadata_last_refreshed

    def test_update(self, fx_exporter_arcgis_layer: ArcGisExporterLayer):
        """Updates items for layer."""
        fx_exporter_arcgis_layer.setup()
        layer_setup = fx_exporter_arcgis_layer._layers.get_by_slug(fx_exporter_arcgis_layer._slug)
        # simulate creating a new exporter layer class instance
        fx_exporter_arcgis_layer._layer = layer_setup

        fx_exporter_arcgis_layer.update()
        layer_updated = fx_exporter_arcgis_layer._layers.get_by_slug(fx_exporter_arcgis_layer._slug)

        # Verify updated layer recorded
        assert layer_setup.metadata_last_refreshed < layer_updated.metadata_last_refreshed

    @pytest.mark.cov()
    def test_update_no_items(self, fx_exporter_arcgis_layer: ArcGisExporterLayer):
        """Does not update items that are not configured for layer."""
        fx_exporter_arcgis_layer.update()

        layer_not_updated = fx_exporter_arcgis_layer._layers.get_by_slug(fx_exporter_arcgis_layer._slug)
        assert layer_not_updated.metadata_last_refreshed is None


class TestExporterArcGIS:
    """ArcGIS exporter tests."""

    def test_init(
        self,
        mocker: MockerFixture,
        fx_config: Config,
        fx_db_client_tmp_db_mig: DatabaseClient,
        fx_logger: logging.Logger,
    ):
        """Initialises."""
        mocker.patch("assets_tracking_service.exporters.arcgis.GIS", return_value=mocker.MagicMock(auto_spec=True))

        ArcGisExporter(config=fx_config, db=fx_db_client_tmp_db_mig, logger=fx_logger)

    def test_init_auth_error(
        self,
        mocker: MockerFixture,
        fx_config: Config,
        fx_db_client_tmp_db_mig: DatabaseClient,
        fx_logger: logging.Logger,
    ):
        """Errors on invalid authentication."""
        mocker.patch(
            "assets_tracking_service.exporters.arcgis.GIS", side_effect=Exception("Invalid username or password")
        )

        with pytest.raises(ArcGISAuthenticationError):
            ArcGisExporter(config=fx_config, db=fx_db_client_tmp_db_mig, logger=fx_logger)

    def test_get_layers(self, fx_exporter_arcgis: ArcGisExporter):
        """Generates layers."""
        result = fx_exporter_arcgis._get_layers()

        assert isinstance(result, list)
        assert all(isinstance(layer, ArcGisExporterLayer) for layer in result)

    def test_export(self, mocker: MockerFixture, fx_exporter_arcgis: ArcGisExporter):
        """Exports layers."""
        mocker.patch(
            "assets_tracking_service.exporters.arcgis.ArcGisExporterLayer",
            return_value=mocker.MagicMock(auto_spec=True),
        )

        fx_exporter_arcgis.export()
