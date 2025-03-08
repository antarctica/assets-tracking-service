import pytest
from psycopg.sql import SQL
from psycopg.types.json import Jsonb
from ulid import ULID

from assets_tracking_service.models.asset import Asset, AssetNew, AssetsClient
from assets_tracking_service.models.label import Label, LabelRelation, Labels
from tests.conftest import LabelsPlain


class TestAssetNew:
    """Test data class in initial state."""

    def test_init(self, fx_labels_one: Labels):
        """Creates an AssetNew."""
        asset = AssetNew(labels=fx_labels_one)

        assert asset.labels == fx_labels_one

    def test_empty_labels(self):
        """Empty labels triggers error."""
        with pytest.raises(ValueError, match="Invalid labels: It must not be empty."):
            AssetNew(labels=Labels([]))

    def test_not_labels_object(self, fx_label_minimal: Label):
        """Non-Labels object triggers error."""
        with pytest.raises(TypeError, match="Invalid labels: It must be a Labels object."):
            # noinspection PyTypeChecker
            AssetNew(labels=[fx_label_minimal])

    def test_not_one_pref_label(self, fx_label_minimal: Label):
        """No skos:prefLabel triggers error."""
        with pytest.raises(
            ValueError, match="Invalid labels: It must include at least and at most one skos:prefLabel item."
        ):
            AssetNew(labels=Labels([Label(rel=LabelRelation.SELF, scheme="foo", value="bar")]))

        with pytest.raises(
            ValueError, match="Invalid labels: It must include at least and at most one skos:prefLabel item."
        ):
            AssetNew(labels=Labels([fx_label_minimal, fx_label_minimal]))

    def test_to_db_dict(self, fx_asset_new: AssetNew):
        """Converts Asset to a database dict."""
        data = fx_asset_new.to_db_dict()
        assert isinstance(data["labels"], Jsonb)
        assert data["labels"].obj == fx_asset_new.labels.unstructure()

    def test_eq(self, fx_labels_one: Labels, fx_label_minimal: Label, fx_label_expired: Label):
        """Equality check."""
        assert AssetNew(labels=fx_labels_one) == AssetNew(labels=fx_labels_one)
        assert AssetNew(labels=Labels([fx_label_minimal, fx_label_expired])) == AssetNew(
            labels=Labels([fx_label_expired, fx_label_minimal])
        )


class TestAsset:
    """Test data class in existing state."""

    def test_init(self, fx_asset_id: ULID, fx_labels_one: Labels):
        """Creates an Asset."""
        asset = Asset(id=fx_asset_id, labels=fx_labels_one)

        assert asset.id == fx_asset_id
        assert asset.labels == fx_labels_one

    def test_to_db_dict(self, fx_asset: Asset):
        """
        Converts Asset to a database dict.

        Check DB assigned `id` property is not included. Overload method.
        """
        assert "id" not in fx_asset.to_db_dict()

    def test_from_db_dict(self, fx_asset: Asset, fx_label_full_plain: LabelsPlain):
        """Makes Asset from a database dict."""
        data = {
            "id": str(fx_asset.id),
            "labels": fx_label_full_plain,
        }

        asset = Asset.from_db_dict(data)

        assert asset == fx_asset

    def test_pref_label(self, fx_asset: Asset):
        """Gets the preferred label."""
        assert fx_asset.pref_label_value == fx_asset.labels[0].value


class TestAssetsClient:
    """Integration tests for a data/resource client."""

    def test_assets_client_add(self, fx_assets_client_empty: AssetsClient, fx_asset_new: AssetNew):
        """Add an Asset."""
        fx_assets_client_empty.add(asset=fx_asset_new)

        # verify table isn't empty
        result = fx_assets_client_empty._db.get_query_result(SQL("""SELECT * FROM public.asset;"""))
        assert len(result) > 0

    def test_assets_client_list(self, fx_assets_client_one: AssetsClient, fx_asset: Asset):
        """List all Assets."""
        assets = fx_assets_client_one.list()
        assert assets == [fx_asset]

    def test_assets_client_list_filtered_by_label_complete(self, fx_assets_client_many: AssetsClient, fx_asset: Asset):
        """List Assets filtered by a label."""
        assert len(fx_assets_client_many.list()) > 1

        assets = fx_assets_client_many.list_filtered_by_label(label=fx_asset.labels[0])

        assert assets == [fx_asset]

    def test_assets_client_list_filtered_by_label_minimal(
        self, fx_assets_client_many: AssetsClient, fx_label_minimal: Label, fx_asset: Asset
    ):
        """List Assets filtered by a label with URIs."""
        assert len(fx_assets_client_many.list()) > 1

        assets = fx_assets_client_many.list_filtered_by_label(label=fx_label_minimal)

        assert assets == [fx_asset]
