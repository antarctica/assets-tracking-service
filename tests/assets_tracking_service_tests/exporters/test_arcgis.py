import logging
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from _pytest.logging import LogCaptureFixture
from arcgis.gis import Group, ItemTypeEnum, SharingLevel
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
from tests.conftest import _create_fake_arcgis_item


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
        """Can initialise."""
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
        """Can get layer as catalogue ArcGIS GeoJSON item."""
        item = fx_exporter_arcgis_layer_updated._catalogue_item_arc_geojson

        assert item is not None
        assert item.item_id is not None
        assert item.item_type == ItemTypeEnum.GEOJSON

        # check access level override
        assert item.sharing_level == SharingLevel.PRIVATE

    def test_catalogue_item_arc_feature(self, fx_exporter_arcgis_layer_updated: ArcGisExporterLayer):
        """Can get layer as catalogue ArcGIS feature item."""
        item = fx_exporter_arcgis_layer_updated._catalogue_item_arc_feature

        assert item is not None
        assert item.item_id is not None
        assert item.item_type == ItemTypeEnum.FEATURE_SERVICE

    def test_catalogue_item_arc_ogc_feature(self, fx_exporter_arcgis_layer_updated: ArcGisExporterLayer):
        """Can get layer as catalogue ArcGIS OGC feature item."""
        item = fx_exporter_arcgis_layer_updated._catalogue_item_arc_ogc_feature

        assert item is not None
        assert item.item_id is not None
        assert item.item_type == ItemTypeEnum.OGCFEATURESERVER

    def test_get_layer(self, fx_exporter_arcgis_layer: ArcGisExporterLayer, fx_layer_init: Layer):
        """Can get Layer."""
        layer = fx_exporter_arcgis_layer._get_layer()

        assert layer == fx_layer_init

    def test_get_data(self, fx_exporter_arcgis_layer: ArcGisExporterLayer):
        """Can get geojson feature collection from source view/table."""
        data = fx_exporter_arcgis_layer._get_data()

        assert isinstance(data, FeatureCollection)

    def test_get_data_empty(self, mocker: MockerFixture, fx_exporter_arcgis_layer: ArcGisExporterLayer):
        """Can make geojson feature collection from empty source view/table."""
        q = (('{"type" : "FeatureCollection", "features" : null}',),)
        mocker.patch.object(fx_exporter_arcgis_layer._db, "get_query_result", return_value=q)

        data = fx_exporter_arcgis_layer._get_data()

        assert isinstance(data, FeatureCollection)

    @staticmethod
    def _get_group_create_group(
        title: str,
        snippet: str | None = None,
        description: str | None = None,
        thumbnail_path: Path | None = None,
        sharing_level: SharingLevel = SharingLevel.PRIVATE,
    ) -> Group:
        """Check group is passed correct values."""
        mock_gis = MagicMock(auto_spec=True)
        return Group(
            gis=mock_gis,
            groupid="x",
            groupdict={
                "title": title,
                "snippet": snippet,
                "description": description,
                "thumbnail": thumbnail_path,
                "access": sharing_level,
            },
        )

    def test_get_group(self, mocker: MockerFixture, fx_exporter_arcgis_layer: ArcGisExporterLayer):
        """Get ArcGIS group for project."""
        mocker.patch.object(
            fx_exporter_arcgis_layer._arcgis_client, "create_group", side_effect=self._get_group_create_group
        )
        group_info = fx_exporter_arcgis_layer._config.EXPORTER_ARCGIS_GROUP_INFO

        group = fx_exporter_arcgis_layer._get_group()
        assert group.groupid == "x"
        assert group.title == group_info["name"]
        assert group.snippet == group_info["summary"]
        assert ".." in group.description  # updating when group description is set properly
        assert group.access == SharingLevel.EVERYONE
        # can't test thumbnail

    def test_get_portrayal(self, fx_exporter_arcgis_layer: ArcGisExporterLayer):
        """Can get portrayal information from resource file."""
        portrayal = fx_exporter_arcgis_layer._get_portrayal()
        assert portrayal is not None

    @pytest.mark.cov()
    @pytest.mark.parametrize("set_dates", [True, False])
    def test_log_last_refreshed(
        self, caplog: LogCaptureFixture, fx_exporter_arcgis_layer: ArcGisExporterLayer, set_dates: bool
    ):
        """Can log last refreshed time."""
        data_ = None
        metadata_ = None
        if set_dates:
            dt = datetime.now(tz=UTC)
            fx_exporter_arcgis_layer._layer.data_last_refreshed = dt
            fx_exporter_arcgis_layer._layer.metadata_last_refreshed = dt
            data_ = dt.isoformat()
            metadata_ = dt.isoformat()

        fx_exporter_arcgis_layer._log_last_refreshed()

        assert f"Layer.data_last_refreshed now '{data_}'." in caplog.messages
        assert f"Layer.metadata_last_refreshed now '{metadata_}'." in caplog.messages

    @pytest.mark.cov()
    def test_set_refreshed_at_layers(self, mocker: MockerFixture, fx_exporter_arcgis_layer: ArcGisExporterLayer):
        """Can set dates based on layer in ArcGIS item."""
        ts = datetime.now(tz=UTC).timestamp() * 1000
        item = _create_fake_arcgis_item(item_id="x", item_type=ItemTypeEnum.FEATURE_SERVICE)
        item.updated = ts
        layer = mocker.MagicMock(auto_spec=True)
        layer.properties.editingInfo.dataLastEditDate = ts
        layers = [layer]
        item.layers = layers
        item["layers"] = layers

        fx_exporter_arcgis_layer._set_refreshed_at(item)

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
