from datetime import UTC, datetime
from re import escape
from zoneinfo import ZoneInfo

import pytest
from lantern.lib.metadata_library.models.record.elements.identification import Extent
from lantern.lib.metadata_library.models.record.presets.extents import make_bbox_extent, make_temporal_extent
from pytest_mock import MockerFixture

from assets_tracking_service.models.layer import Layer, LayerNew, LayersClient


class TestLayerNew:
    """Test data class in initial state."""

    def test_init(self, fx_record_layer_slug: str):
        """Creates a LayerNew."""
        layer = LayerNew(slug=fx_record_layer_slug, source_view="x")

        assert isinstance(layer, LayerNew)

    @pytest.mark.parametrize("slug", ["", "UPPER", "mixedCase", "with spaces", "with-hyphens", "with.dots"])
    def test_slug_invalid(self, slug: str):
        """Invalid slug triggers error."""
        with pytest.raises(
            ValueError, match=escape(f"Invalid slug: [{slug}]. It must be lowercase a-z, 0-9, and underscores only.")
        ):
            # noinspection PyTypeChecker
            LayerNew(slug=slug, source_view="x")

    def test_to_db_dict(self, fx_layer_pre_init: LayerNew):
        """Converts Layer to a database dict."""
        data = fx_layer_pre_init.to_db_dict()
        assert data == {"slug": fx_layer_pre_init.slug, "source_view": fx_layer_pre_init.source_view}


class TestLayer:
    """Test data class in existing state."""

    def test_init(self, fx_record_layer_slug: str):
        """Creates a minimal Layer."""
        dt = datetime.now(tz=UTC)
        layer = Layer(slug=fx_record_layer_slug, source_view="x", created_at=dt)

        assert isinstance(layer, Layer)
        assert layer.created_at == dt
        assert layer.agol_id_geojson is None
        assert layer.agol_id_feature is None
        assert layer.agol_id_feature_ogc is None
        assert layer.data_last_refreshed is None
        assert layer.metadata_last_refreshed is None

    def test_updated(self, fx_record_layer_slug: str):
        """Creates a complete Layer."""
        dt = datetime.now(tz=UTC)
        layer = Layer(
            slug=fx_record_layer_slug,
            source_view="x",
            created_at=dt,
            agol_id_geojson="x",
            agol_id_feature="x",
            agol_id_feature_ogc="x",
            data_last_refreshed=dt,
            metadata_last_refreshed=dt,
        )

        assert isinstance(layer, Layer)
        assert layer.agol_id_geojson == "x"
        assert layer.agol_id_feature == "x"
        assert layer.agol_id_feature_ogc == "x"
        assert layer.data_last_refreshed == dt
        assert layer.metadata_last_refreshed == dt

    def test_repr(self, fx_layer_init: Layer, fx_layer_updated: Layer):
        """String representation."""
        assert repr(fx_layer_init) == f"Layer(slug='{fx_layer_init.slug}')"
        assert (
            repr(fx_layer_updated)
            == f"Layer(slug={fx_layer_updated.slug!r}, feature_layer={fx_layer_updated.agol_id_feature!r})"
        )

    def test_from_db_dict(self, fx_layer_updated: Layer):
        """Makes Layer from a database dict."""
        data = {
            "slug": str(fx_layer_updated.slug),
            "source_view": fx_layer_updated.source_view,
            "created_at": fx_layer_updated.created_at,
            "agol_id_geojson": fx_layer_updated.agol_id_geojson,
            "agol_id_feature": fx_layer_updated.agol_id_feature,
            "agol_id_feature_ogc": fx_layer_updated.agol_id_feature_ogc,
            "data_last_refreshed": fx_layer_updated.data_last_refreshed,
            "metadata_last_refreshed": fx_layer_updated.metadata_last_refreshed,
        }

        layer = Layer.from_db_dict(data)

        assert layer == fx_layer_updated


class TestLayersClient:
    """Integration tests for a data/resource client."""

    def test_list_slugs(self, fx_layers_client_one: LayersClient, fx_layer_updated: Layer):
        """Can list Layer slugs."""
        layers = fx_layers_client_one.list_slugs()
        assert layers == [fx_layer_updated.slug]

    def test_get_by_slug(self, fx_layers_client_one: LayersClient, fx_layer_updated: Layer):
        """Can get Layer by slug that exists."""
        layer = fx_layers_client_one.get_by_slug(fx_layer_updated.slug)
        assert layer == fx_layer_updated

    def test_get_by_slug_unknown(self, fx_layers_client_one: LayersClient):
        """Cannot get Layer for slug that does not exist."""
        result = fx_layers_client_one.get_by_slug("unknown")
        assert result is None

    def test_get_extent_by_slug(self, fx_layers_client_one: LayersClient, fx_layer_updated: Layer):
        """Can get record extent for Layer data by slug."""
        extent = fx_layers_client_one.get_extent_by_slug(fx_layer_updated.slug)
        assert isinstance(extent, Extent)

    @staticmethod
    def _get_layer_extent(slug: str) -> Extent:
        extent_a = Extent(
            identifier="bounding",
            geographic=make_bbox_extent(
                min_x=1,
                max_x=3,
                min_y=10,
                max_y=30,
            ),
            temporal=make_temporal_extent(
                start=datetime(2021, 1, 1, tzinfo=UTC),
                end=datetime(2021, 3, 3, tzinfo=UTC),
            ),
        )
        extent_b = Extent(
            identifier="bounding",
            geographic=make_bbox_extent(
                min_x=2,
                max_x=4,
                min_y=20,
                max_y=40,
            ),
            temporal=make_temporal_extent(
                start=datetime(2021, 2, 2, tzinfo=UTC),
                end=datetime(2021, 4, 4, tzinfo=UTC),
            ),
        )

        if slug == "a":
            return extent_a
        return extent_b

    def test_get_bounding_extent(self, mocker: MockerFixture, fx_layers_client_one: LayersClient):
        """Can get bounding extent across all Layer extents."""
        mocker.patch.object(fx_layers_client_one, "list_slugs", return_value=["a", "b"])
        mocker.patch.object(fx_layers_client_one, "get_extent_by_slug", side_effect=self._get_layer_extent)
        expected = Extent(
            identifier="bounding",
            geographic=make_bbox_extent(min_x=1, max_x=4, min_y=10, max_y=40),
            temporal=make_temporal_extent(start=datetime(2021, 1, 1, tzinfo=UTC), end=datetime(2021, 4, 4, tzinfo=UTC)),
        )

        bounding_extent = fx_layers_client_one.get_bounding_extent()

        assert isinstance(bounding_extent, Extent)
        assert bounding_extent == expected

    def test_get_latest_data_refresh(self, fx_layers_client_one: LayersClient, fx_layer_updated: Layer):
        """Can get latest data refresh time across all Layers."""
        result = fx_layers_client_one.get_latest_data_refresh()
        assert result == fx_layer_updated.data_last_refreshed

    @pytest.mark.parametrize(
        "ids",
        [
            {"geojson_id": "x"},
            {"feature_id": "x"},
            {"feature_ogc_id": "x"},
            {"geojson_id": "x", "feature_id": "x", "feature_ogc_id": "x"},
        ],
    )
    def test_set_item_id(self, fx_layers_client_one: LayersClient, fx_record_layer_slug: str, ids: dict):
        """Can set AGOL item IDs."""
        original = fx_layers_client_one.get_by_slug(fx_record_layer_slug)

        fx_layers_client_one.set_item_id(slug=fx_record_layer_slug, **ids)

        result = fx_layers_client_one.get_by_slug(fx_record_layer_slug)
        if "geojson_id" in ids:
            assert result.agol_id_geojson == ids["geojson_id"]
            assert original.agol_id_geojson != result.agol_id_geojson
        else:
            assert original.agol_id_geojson == result.agol_id_geojson
        if "feature_id" in ids:
            assert result.agol_id_feature == ids["feature_id"]
            assert original.agol_id_feature != result.agol_id_feature
        else:
            assert original.agol_id_feature == result.agol_id_feature
        if "feature_ogc_id" in ids:
            assert result.agol_id_feature_ogc == ids["feature_ogc_id"]
            assert original.agol_id_feature_ogc != result.agol_id_feature_ogc
        else:
            assert original.agol_id_feature_ogc == result.agol_id_feature_ogc

    dt_x = datetime(2020, 3, 3, 3, 3, 3, tzinfo=UTC)

    @pytest.mark.parametrize(
        "dates",
        [{"data_refreshed": dt_x}, {"metadata_refreshed": dt_x}, {"data_refreshed": dt_x, "metadata_refreshed": dt_x}],
    )
    def test_set_last_refreshed(self, fx_layers_client_one: LayersClient, fx_record_layer_slug: str, dates: dict):
        """Can set data/metadata last refreshed times."""
        original = fx_layers_client_one.get_by_slug(fx_record_layer_slug)

        fx_layers_client_one.set_last_refreshed(slug=fx_record_layer_slug, **dates)

        result = fx_layers_client_one.get_by_slug(fx_record_layer_slug)
        if "data_refreshed" in dates:
            assert result.data_last_refreshed == dates["data_refreshed"]
            assert original.data_last_refreshed != result.data_last_refreshed
        else:
            assert original.data_last_refreshed == result.data_last_refreshed
        if "metadata_refreshed" in dates:
            assert result.metadata_last_refreshed == dates["metadata_refreshed"]
            assert original.metadata_last_refreshed != result.metadata_last_refreshed
        else:
            assert original.metadata_last_refreshed == result.metadata_last_refreshed

    dt_invalid = datetime.now(tz=ZoneInfo("America/Lima"))

    @pytest.mark.parametrize("dates", [{"data_refreshed": dt_invalid}, {"metadata_refreshed": dt_invalid}])
    def test_set_last_refreshed_invalid(
        self, fx_layers_client_one: LayersClient, fx_record_layer_slug: str, dates: dict
    ):
        """Cannot set data/metadata last refreshed times with invalid values."""
        with pytest.raises(ValueError, match="It must be UTC."):
            fx_layers_client_one.set_last_refreshed(slug=fx_record_layer_slug, **dates)
