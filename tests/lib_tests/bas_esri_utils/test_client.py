from logging import Logger
from pathlib import Path
from tempfile import TemporaryDirectory

import geojson
import pytest
from arcgis.gis import Group, Item, ItemTypeEnum, SharingLevel
from arcgis.gis._impl._content_manager import Folder
from geojson import Feature, FeatureCollection, Point
from pytest_mock import MockerFixture

from assets_tracking_service.config import Config
from assets_tracking_service.lib.bas_esri_utils.client import (
    ArcGisClient,
    ArcGISGroupAmbiguityError,
    ArcGISInternalServerError,
    ArcGisInvalidPublishTargetError,
    ArcGISItemDataEmptyError,
    ArcGisItemNotFoundError,
    ArcGisItemNotSpecifiedError,
    ArcGisUnsupportedPublishItemTypeError,
    GroupSharingLevel,
)
from assets_tracking_service.lib.bas_esri_utils.models.item import Item as ItemArc
from tests.conftest import _create_fake_arcgis_item


class TestGroupSharingLevel:
    """
    Tests for group sharing level enum.

    These test use extensive mocking to avoid calling the actual ArcGIS API. Given this class relies heavily on that,
    these tests are not as useful as they could be.
    """

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (SharingLevel.PRIVATE, GroupSharingLevel.PRIVATE),
            (SharingLevel.ORG, GroupSharingLevel.ORG),
            (SharingLevel.EVERYONE, GroupSharingLevel.PUBLIC),
        ],
    )
    def test_from_sharing_level(self, value: SharingLevel, expected: GroupSharingLevel):
        """Can map ArcGIS sharing level to a group sharing level."""
        assert GroupSharingLevel.from_sharing_level(value) == expected


class TestArcGisClient:
    """Tests for BAS ArcGIS client."""

    def test_init(self, mocker: MockerFixture, fx_config: Config, fx_logger: Logger):
        """Can initialise."""
        client = ArcGisClient(arcgis=mocker.MagicMock(auto_spec=True), logger=fx_logger)
        assert client is not None

    def test_dump_metadata(self, fx_lib_arcgis_client: ArcGisClient, fx_lib_catalogue_arcgis_item: ItemArc):
        """Can write ArcGIS metadata to file."""
        with TemporaryDirectory() as tmp_path:
            base_path = Path(tmp_path)
            expected_path = base_path / "metadata.xml"

            fx_lib_arcgis_client._dump_metadata(base_path=base_path, cat_item_arc=fx_lib_catalogue_arcgis_item)

            assert expected_path.exists()
            with expected_path.open() as expected_file:
                assert expected_file.read() == fx_lib_catalogue_arcgis_item.metadata

    def test_dump_data(self, fx_lib_arcgis_client: ArcGisClient):
        """Can write ArcGIS data to file."""
        data = FeatureCollection(features=[])
        filename = "x.geojson"

        with TemporaryDirectory() as tmp_path:
            base_path = Path(tmp_path)
            expected_path = base_path / filename

            fx_lib_arcgis_client._dump_data(base_path=base_path, data=data, file_name=filename)

            assert expected_path.exists()
            with expected_path.open() as expected_file:
                assert geojson.load(expected_file) == data

    def test_get_create_folder(self, mocker: MockerFixture, fx_lib_arcgis_client: ArcGisClient):
        """Can create then get a folder if it doesn't exist."""
        name = "x"
        expected = Folder(gis=fx_lib_arcgis_client._client, folder=name)
        mocker.patch.object(fx_lib_arcgis_client._client.content.folders, "get", return_value=None)
        mocker.patch.object(fx_lib_arcgis_client._client.content.folders, "create", return_value=expected)

        folder = fx_lib_arcgis_client._get_create_folder(name=name)
        assert folder == expected

    def test_get_create_folder_exists(self, mocker: MockerFixture, fx_lib_arcgis_client: ArcGisClient):
        """Can get a folder if it exists."""
        name = "x"
        expected = Folder(gis=fx_lib_arcgis_client._client, folder=name)
        mocker.patch.object(fx_lib_arcgis_client._client.content.folders, "get", return_value=expected)

        folder = fx_lib_arcgis_client._get_create_folder(name=name)
        assert folder == expected

    def test_get_group(self, mocker: MockerFixture, fx_lib_arcgis_client: ArcGisClient):
        """Can get a group that exists."""
        expected = Group(gis=fx_lib_arcgis_client._client, groupid="x", groupdict={"id": "x", "title": "x"})
        mocker.patch.object(fx_lib_arcgis_client._client.groups, "search", return_value=[expected])

        group = fx_lib_arcgis_client.get_group(title=expected.title)
        assert group == expected

    def test_get_group_unknown(self, mocker: MockerFixture, fx_lib_arcgis_client: ArcGisClient):
        """Cannot get a group that doesn't exist."""
        mocker.patch.object(fx_lib_arcgis_client._client.groups, "search", return_value=[])

        group = fx_lib_arcgis_client.get_group(title="invalid")
        assert group is None

    def test_get_group_ambiguous(self, mocker: MockerFixture, fx_lib_arcgis_client: ArcGisClient):
        """Cannot get a group where multiple are matched."""
        group_ = Group(gis=fx_lib_arcgis_client._client, groupid="x", groupdict={"id": "x", "title": "x"})
        mocker.patch.object(fx_lib_arcgis_client._client.groups, "search", return_value=[group_, group_])

        with pytest.raises(ArcGISGroupAmbiguityError):
            fx_lib_arcgis_client.get_group(title=group_.title)

    def test_create_group(self, mocker: MockerFixture, fx_lib_arcgis_client: ArcGisClient):
        """Can create a group."""
        expected = Group(gis=fx_lib_arcgis_client._client, groupid="x", groupdict={"id": "x", "title": "x"})
        mocker.patch.object(fx_lib_arcgis_client._client.groups, "search", return_value=[])
        mocker.patch.object(fx_lib_arcgis_client._client.groups, "create", return_value=expected)

        group = fx_lib_arcgis_client.create_group(title=expected.title)
        assert group == expected

    def test_create_group_exists(self, mocker: MockerFixture, fx_lib_arcgis_client: ArcGisClient):
        """Returns existing group if one already exists."""
        expected = Group(gis=fx_lib_arcgis_client._client, groupid="x", groupdict={"id": "x", "title": "x"})
        mocker.patch.object(fx_lib_arcgis_client._client.groups, "search", return_value=[expected])

        group = fx_lib_arcgis_client.create_group(title=expected.title)
        assert group == expected

    def test_get_item(self, mocker: MockerFixture, fx_lib_arcgis_client: ArcGisClient):
        """Can get a group that exists."""
        expected = _create_fake_arcgis_item(item_id="x")
        mocker.patch.object(fx_lib_arcgis_client._client.content, "get", return_value=expected)

        item = fx_lib_arcgis_client.get_item(item_id=expected.id)
        assert item == expected

    def test_get_item_unknown(self, mocker: MockerFixture, fx_lib_arcgis_client: ArcGisClient):
        """Cannot get a group that doesn't exist."""
        mocker.patch.object(fx_lib_arcgis_client._client.content, "get", return_value=None)

        with pytest.raises(ArcGisItemNotFoundError):
            fx_lib_arcgis_client.get_item(item_id="x")

    def test_create_item(
        self, mocker: MockerFixture, fx_lib_arcgis_client: ArcGisClient, fx_lib_catalogue_arcgis_item: ItemArc
    ):
        """Can create an item."""
        expected = _create_fake_arcgis_item(item_id="x")
        folder = Folder(gis=fx_lib_arcgis_client._client, folder="x")
        data = FeatureCollection(features=[Feature(geometry=Point(coordinates=(0, 0)), properties={"id": "x"})])

        # mock getting folder
        mocker.patch.object(fx_lib_arcgis_client, "_get_create_folder", return_value=folder)
        # mock creating item
        result = mocker.MagicMock(auto_spec=True)
        result.result.return_value = expected
        mocker.patch.object(folder, "add", return_value=result)
        # mock updating item sharing
        item_sharing = mocker.MagicMock(auto_spec=True)
        item_sharing.sharing_level.return_value = fx_lib_catalogue_arcgis_item.sharing_level
        mocker.patch("arcgis.gis.Item.sharing", autospec=True, return_value=item_sharing)
        # mock updating item (as this is tested separately)
        mocker.patch.object(expected, "update", return_value=expected)

        item = fx_lib_arcgis_client.create_item(
            folder_name=folder.name, cat_item_arc=fx_lib_catalogue_arcgis_item, data=data
        )

        assert item == expected

    def test_create_item_empty_data(self, fx_lib_arcgis_client: ArcGisClient, fx_lib_catalogue_arcgis_item: ItemArc):
        """Cannot create an item if associated data is empty."""
        data = FeatureCollection(features=[])

        with pytest.raises(ArcGISItemDataEmptyError):
            fx_lib_arcgis_client.create_item(folder_name="x", cat_item_arc=fx_lib_catalogue_arcgis_item, data=data)

    @pytest.mark.parametrize(
        "item_type",
        [
            (ItemTypeEnum.GEOJSON, ItemTypeEnum.FEATURE_SERVICE),
            (ItemTypeEnum.FEATURE_SERVICE, ItemTypeEnum.OGCFEATURESERVER),
        ],
    )
    def test_publish_item(
        self,
        mocker: MockerFixture,
        fx_lib_arcgis_client: ArcGisClient,
        fx_lib_catalogue_arcgis_item: ItemArc,
        item_type: tuple[ItemTypeEnum],
    ):
        """Can publish an item from an existing item."""
        src_item = _create_fake_arcgis_item(item_id="x")
        expected = _create_fake_arcgis_item(item_id="y")
        src_cat_item = ItemArc(
            record=fx_lib_catalogue_arcgis_item._record,
            arcgis_item_type=item_type[0],
            arcgis_item_id="x",
            arcgis_item_name="x",
        )
        dest_cat_item = ItemArc(
            record=fx_lib_catalogue_arcgis_item._record,
            arcgis_item_type=item_type[1],
            arcgis_item_id="y",
            arcgis_item_name="y",
        )

        # mock publishing item
        mocker.patch("arcgis.gis.Item.publish", autospec=True, return_value=expected)
        # mock getting source item (as this is tested separately)
        mocker.patch.object(fx_lib_arcgis_client, "get_item", return_value=src_item)
        # mock updating item (as this is tested separately)
        mocker.patch.object(fx_lib_arcgis_client, "update_item", return_value=expected)

        item = fx_lib_arcgis_client.publish_item(src_cat_item=src_cat_item, dest_cat_item=dest_cat_item)

        assert item == expected

    def test_publish_item_undefined(self, fx_lib_arcgis_client: ArcGisClient, fx_lib_catalogue_arcgis_item: ItemArc):
        """Cannot publish an item without an ArcGIS item ID."""
        with pytest.raises(ArcGisItemNotSpecifiedError):
            fx_lib_arcgis_client.publish_item(
                src_cat_item=fx_lib_catalogue_arcgis_item, dest_cat_item=fx_lib_catalogue_arcgis_item
            )

    def test_publish_item_self(self, fx_lib_arcgis_client: ArcGisClient, fx_lib_catalogue_arcgis_item: ItemArc):
        """
        Cannot publish an item to itself.

        I.e. source and destination catalogue arc records match.
        """
        cat_item = ItemArc(
            record=fx_lib_catalogue_arcgis_item._record,
            arcgis_item_type=ItemTypeEnum.GEOJSON,
            arcgis_item_id="x",
            arcgis_item_name="x",
        )

        with pytest.raises(ArcGisInvalidPublishTargetError):
            fx_lib_arcgis_client.publish_item(src_cat_item=cat_item, dest_cat_item=cat_item)

    def test_publish_item_unsupported(self, fx_lib_arcgis_client: ArcGisClient, fx_lib_catalogue_arcgis_item: ItemArc):
        """Cannot publish an unsupported item type."""
        src_cat_item = ItemArc(
            record=fx_lib_catalogue_arcgis_item._record,
            arcgis_item_type=ItemTypeEnum.GEOJSON,
            arcgis_item_id="x",
            arcgis_item_name="x",
        )
        dest_cat_item = ItemArc(
            record=fx_lib_catalogue_arcgis_item._record,
            arcgis_item_type=ItemTypeEnum.GEOJSON,
            arcgis_item_id="y",
            arcgis_item_name="y",
        )

        with pytest.raises(ArcGisUnsupportedPublishItemTypeError):
            fx_lib_arcgis_client.publish_item(src_cat_item=src_cat_item, dest_cat_item=dest_cat_item)

    def test_update_item(
        self, mocker: MockerFixture, fx_lib_arcgis_client: ArcGisClient, fx_lib_catalogue_arcgis_item: ItemArc
    ):
        """Can update existing item with item ID from cat item."""
        cat_item = ItemArc(
            record=fx_lib_catalogue_arcgis_item._record,
            arcgis_item_type=ItemTypeEnum.GEOJSON,
            arcgis_item_id="x",
            arcgis_item_name="x",
        )
        expected = _create_fake_arcgis_item(item_id="x")

        # mock getting item (as this is tested separately)
        mocker.patch.object(fx_lib_arcgis_client, "get_item", return_value=expected)
        # mock updating item
        mocker.patch("arcgis.gis.Item.update", autospec=True, return_value=expected)
        # mock updating item sharing
        item_sharing = mocker.MagicMock(auto_spec=True)
        item_sharing.sharing_level.return_value = fx_lib_catalogue_arcgis_item.sharing_level
        mocker.patch("arcgis.gis.Item.sharing", autospec=True, return_value=item_sharing)

        item = fx_lib_arcgis_client.update_item(cat_item_arc=cat_item)
        assert item == expected

    def test_update_item_id(
        self, mocker: MockerFixture, fx_lib_arcgis_client: ArcGisClient, fx_lib_catalogue_arcgis_item: ItemArc
    ):
        """Can update existing item with item ID set explicitly."""
        cat_item = ItemArc(
            record=fx_lib_catalogue_arcgis_item._record,
            arcgis_item_type=ItemTypeEnum.GEOJSON,
            arcgis_item_id="x",
            arcgis_item_name="x",
        )
        expected = _create_fake_arcgis_item(item_id="x")

        # mock getting item (as this is tested separately)
        mocker.patch.object(fx_lib_arcgis_client, "get_item", return_value=expected)
        # mock updating item
        mocker.patch("arcgis.gis.Item.update", autospec=True, return_value=expected)
        # mock updating item sharing
        item_sharing = mocker.MagicMock(auto_spec=True)
        item_sharing.sharing_level.return_value = fx_lib_catalogue_arcgis_item.sharing_level
        mocker.patch("arcgis.gis.Item.sharing", autospec=True, return_value=item_sharing)

        item = fx_lib_arcgis_client.update_item(cat_item_arc=cat_item, item_id="y")
        assert item == expected

    def test_update_item_portrayal(
        self, mocker: MockerFixture, fx_lib_arcgis_client: ArcGisClient, fx_lib_catalogue_arcgis_item: ItemArc
    ):
        """Can update existing item with portrayal information."""
        cat_item = ItemArc(
            record=fx_lib_catalogue_arcgis_item._record,
            arcgis_item_type=ItemTypeEnum.GEOJSON,
            arcgis_item_id="x",
            arcgis_item_name="x",
        )
        expected = _create_fake_arcgis_item(item_id="x")

        # mock getting item (as this is tested separately)
        mocker.patch.object(fx_lib_arcgis_client, "get_item", return_value=expected)
        # mock updating item
        mocker.patch("arcgis.gis.Item.update", autospec=True, return_value=expected)
        # mock updating item sharing
        item_sharing = mocker.MagicMock(auto_spec=True)
        item_sharing.sharing_level.return_value = fx_lib_catalogue_arcgis_item.sharing_level
        mocker.patch("arcgis.gis.Item.sharing", autospec=True, return_value=item_sharing)

        item = fx_lib_arcgis_client.update_item(cat_item_arc=cat_item, item_portrayal={})
        assert item == expected

    def test_add_item_to_group(self, mocker: MockerFixture, fx_lib_arcgis_client: ArcGisClient):
        """
        Can add item to a group.

        This really only tests mocks are set up correctly.
        """
        item = _create_fake_arcgis_item(item_id="x")
        group = Group(gis=fx_lib_arcgis_client._client, groupid="x", groupdict={"id": "x", "title": "x"})

        item_sharing = mocker.MagicMock(auto_spec=True)
        mocker.patch("arcgis.gis.Item.sharing", autospec=True, return_value=item_sharing)

        fx_lib_arcgis_client.add_item_to_group(item=item, group=group)
        assert True

    @staticmethod
    def _get_item_override_feat(item_id: str) -> Item:
        return _create_fake_arcgis_item(item_id=item_id)

    def test_overwrite_service_features(self, mocker: MockerFixture, fx_lib_arcgis_client: ArcGisClient):
        """Can overwrite features in feature service."""
        data = FeatureCollection(features=[Feature(geometry=Point(coordinates=(0, 0)), properties={"id": "x"})])
        mocker.patch.object(fx_lib_arcgis_client, "get_item", side_effect=self._get_item_override_feat)
        mocker.patch("assets_tracking_service.lib.bas_esri_utils.client.FeatureLayerCollection", autospec=True)

        fx_lib_arcgis_client.overwrite_service_features(features_id="x", geojson_id="y", data=data)

    def test_overwrite_service_features_failed(self, mocker: MockerFixture, fx_lib_arcgis_client: ArcGisClient):
        """Cannot overwrite features in feature service but handles error if a 500 error occurs."""
        data = FeatureCollection(features=[Feature(geometry=Point(coordinates=(0, 0)), properties={"id": "x"})])
        mocker.patch.object(fx_lib_arcgis_client, "get_item", side_effect=self._get_item_override_feat)

        feat_collection = mocker.MagicMock(auto_spec=True)
        mocker.patch(
            "assets_tracking_service.lib.bas_esri_utils.client.FeatureLayerCollection.fromitem",
            return_value=feat_collection,
        )
        feat_collection.manager.overwrite.side_effect = Exception("Internal Server Error")

        with pytest.raises(ArcGISInternalServerError):
            fx_lib_arcgis_client.overwrite_service_features(features_id="x", geojson_id="y", data=data)

    def test_overwrite_service_features_error(self, mocker: MockerFixture, fx_lib_arcgis_client: ArcGisClient):
        """Cannot overwrite features in feature service and raises exception."""
        data = FeatureCollection(features=[Feature(geometry=Point(coordinates=(0, 0)), properties={"id": "x"})])
        mocker.patch.object(fx_lib_arcgis_client, "get_item", side_effect=self._get_item_override_feat)

        feat_collection = mocker.MagicMock(auto_spec=True)
        mocker.patch(
            "assets_tracking_service.lib.bas_esri_utils.client.FeatureLayerCollection.fromitem",
            return_value=feat_collection,
        )
        feat_collection.manager.overwrite.side_effect = Exception("x")

        with pytest.raises(Exception):  # noqa: B017, PT011
            fx_lib_arcgis_client.overwrite_service_features(features_id="x", geojson_id="y", data=data)
