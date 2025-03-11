import json
import logging
from enum import Enum
from pathlib import Path
from tempfile import TemporaryDirectory

from arcgis import GIS
from arcgis.features import FeatureLayerCollection
from arcgis.gis import Group, Item, ItemTypeEnum, SharingLevel
from arcgis.gis._impl._content_manager import Folder
from geojson import FeatureCollection
from geojson import dump as geojson_dump

from assets_tracking_service.lib.bas_esri_utils.models.item import Item as CatalogueItemArcGis


class ArcGISInternalServerError(Exception):
    """Raised when an internal server error occurs within an ArcGIS service."""

    pass


class ArcGISGroupAmbiguityError(Exception):
    """Raised when an ArcGIS group search returns multiple results."""

    pass


class ArcGISItemDataEmptyError(Exception):
    """Raised when trying to create an ArcGIS item with an empty feature collection."""

    pass


class ArcGisItemNotSpecifiedError(Exception):
    """Raised when an ArcGIS item is not specified but is required."""

    pass


class ArcGisUnsupportedPublishItemTypeError(Exception):
    """Raised when trying to publish an item as an unsupported type."""

    pass


class ArcGisInvalidPublishTargetError(Exception):
    """Raised when publishing a catalogue item that is the same as its intended destination."""

    pass


class ArcGisItemNotFoundError(Exception):
    """Raised when an ArcGIS item cannot be found."""

    pass


class GroupSharingLevel(Enum):
    """
    ArcGIS group sharing level.

    I.e. Who can access content within a group.
    """

    ORG = "org"
    PRIVATE = "private"
    PUBLIC = "public"

    @classmethod
    def from_sharing_level(cls, sharing_level: SharingLevel) -> "GroupSharingLevel":
        """Map ArcGIS item sharing level to group sharing level."""
        if sharing_level == SharingLevel.EVERYONE:
            return GroupSharingLevel.PUBLIC
        # noinspection PyTypeChecker
        return GroupSharingLevel[sharing_level.name]


class GroupMembershipAccess(Enum):
    """
    ArcGIS group membership access level.

    I.e. Who can join a group.
    """

    ORG = "org"
    COLLABORATION = "collaboration"
    NONE = "none"


class ArcGisClient:
    """
    A high-level client for the ArcGIS platform.

    Built upon the ArcGIS API for Python, https://developers.arcgis.com/python/latest/. Opinionated to workflows used
    by the British Antarctic Survey to manage and publish data, with item metadata linked to BAS Data Catalogue records.

    Note: This class, and its behaviours, are not yet stable and subject to change as we better understand our needs.
    """

    def __init__(self, arcgis: GIS, logger: logging.Logger | None = None) -> None:
        self._logger = logger
        self._client = arcgis

    def _dump_metadata(self, base_path: Path, cat_item_arc: CatalogueItemArcGis) -> Path:
        """Write ArcGIS metadata to file."""
        metadata_path = base_path / "metadata.xml"
        self._logger.debug("Generating ArcGIS metadata ...")
        self._logger.debug("ArcGIS metadata:")
        self._logger.debug(cat_item_arc.metadata)
        self._logger.debug("Metadata path: %s", metadata_path.resolve())
        metadata_path.write_text(cat_item_arc.metadata)
        return metadata_path

    def _dump_data(self, base_path: Path, data: FeatureCollection, file_name: str) -> Path:
        data_path = base_path / file_name
        self._logger.debug("Writing item source data to: %s", data_path.resolve())
        self._logger.debug("Data:")
        self._logger.debug(data)
        with data_path.open(mode="w") as f:
            geojson_dump(data, f)
        return data_path

    def _get_create_folder(self, name: str) -> Folder:
        """
        Return a folder within the user account of the current user.

        If missing it will be created.
        """
        self._logger.debug("Getting folder '%s' ...", name)
        folder = self._client.content.folders.get(name)
        if folder is not None:
            return folder
        self._logger.debug("Folder '%s' not found, creating ...", name)
        return self._client.content.folders.create(name)

    def get_group(self, title: str) -> Group | None:
        """Get a ArcGIS group by title."""
        self._logger.debug("Searching for group '%s'", title)
        results = self._client.groups.search(filter=f'title:"{title}"')
        self._logger.debug("Results: %s", [f"[{g.id}] '{g.title}', " for g in results])

        if len(results) == 0:
            return None
        if len(results) > 1:
            raise ArcGISGroupAmbiguityError() from None
        return results[0]

    def create_group(
        self,
        title: str,
        tags: list[str] | None = None,
        snippet: str | None = None,
        description: str | None = None,
        thumbnail_path: Path | None = None,
        sharing_level: SharingLevel = SharingLevel.PRIVATE,
        membership_level: GroupMembershipAccess = GroupMembershipAccess.ORG,
        can_request_membership: bool = False,
        shared_update: bool = False,
        members_hidden: bool = True,
    ) -> Group:
        """Create ArcGIS group."""
        self._logger.debug("Checking if ArcGIS group '%s' exists ...", title)
        group = self.get_group(title)
        if group is not None:
            self._logger.debug("Returning existing ArcGIS group [%s] '%s'", group.id, group.title)
            return group

        self._logger.debug("Creating ArcGIS group '%s' ...", title)
        return self._client.groups.create(
            title=title,
            tags=[] if tags is None else tags,
            snippet=snippet,
            description=description,
            thumbnail=str(thumbnail_path),
            access=GroupSharingLevel.from_sharing_level(sharing_level).value,
            is_invitation_only=not can_request_membership,
            membership_access=membership_level.value,
            users_update_items=shared_update,
            hidden_members=members_hidden,
        )

    def get_item(self, item_id: str) -> Item:
        """Get ArcGIS item."""
        item = self._client.content.get(item_id)

        if item is None:
            msg = f"Item [{item_id}] not found"
            raise ArcGisItemNotFoundError(msg) from None

        self._logger.debug("Item [%s] '%s'", item.id, item.title)
        return item

    def create_item(self, folder_name: str, cat_item_arc: CatalogueItemArcGis, data: FeatureCollection) -> Item:
        """Create ArcGIS item."""
        self._logger.debug("Creating ArcGIS item '%s' ...", cat_item_arc.title_plain)

        if len(data["features"]) == 0:
            self._logger.exception(msg="Feature collection is empty, cannot derive schema for item.")
            raise ArcGISItemDataEmptyError() from None

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            metadata_path = self._dump_metadata(temp_path, cat_item_arc)
            data_path = self._dump_data(temp_path, data, "features.geojson")

            folder = self._get_create_folder(folder_name)
            self._logger.debug("Adding item to folder '%s' ...", folder.name)
            self._logger.debug("Item properties:")
            self._logger.debug(cat_item_arc.item_properties)
            result = folder.add(item_properties=cat_item_arc.item_properties, file=str(data_path))
            new_item = result.result()
            self._logger.debug("New item created [%s] '%s'", new_item.id, new_item.title)

            self._logger.debug("Setting item sharing level to: '%s' ...", cat_item_arc.sharing_level)
            new_item.sharing.sharing_level = cat_item_arc.sharing_level
            # `Folder.add` method doesn't support setting ArcGIS item metadata and thumbnail so update these separately
            self._logger.debug("Setting item thumbnail to: '%s' ...", cat_item_arc.thumbnail_href)
            new_item.update(
                thumbnail=cat_item_arc.thumbnail_href,
                metadata=str(metadata_path),
            )

            return new_item

    def publish_item(self, src_cat_item: CatalogueItemArcGis, dest_cat_item: CatalogueItemArcGis) -> Item:
        """Publish ArcGIS item as a service."""
        self._logger.debug("Publishing ArcGIS item '%s' as a %s ...", src_cat_item.item_id, dest_cat_item.item_type)

        if src_cat_item.item_id is None:
            self._logger.exception("Cannot publish item without an ArcGIS item ID.")
            raise ArcGisItemNotSpecifiedError() from None

        if src_cat_item == dest_cat_item:
            self._logger.exception("Cannot publish item where its destination is the same as its source.")
            raise ArcGisInvalidPublishTargetError() from None

        supported_types = [ItemTypeEnum.FEATURE_SERVICE, ItemTypeEnum.OGCFEATURESERVER]
        if dest_cat_item.item_type not in supported_types:
            self._logger.exception("Cannot publish item of type '%s'", src_cat_item.item_type)
            raise ArcGisUnsupportedPublishItemTypeError() from None

        params = {"publish_parameters": {"name": dest_cat_item.item_name}}
        if src_cat_item.item_type == ItemTypeEnum.FEATURE_SERVICE:
            params["file_type"] = "featureService"
        if dest_cat_item.item_type == ItemTypeEnum.OGCFEATURESERVER:
            params["output_type"] = "OGCFeatureService"
        self._logger.debug("Publishing parameters:")
        self._logger.debug(params)

        src_item = self.get_item(src_cat_item.item_id)
        new_item = src_item.publish(**params)
        # Set metadata link for new item
        with TemporaryDirectory() as temp_dir:
            metadata_path = self._dump_metadata(Path(temp_dir), dest_cat_item)
            new_item.update(metadata=str(metadata_path))

        self._logger.debug("Item [%s] published as a %s [%s]", src_item.id, dest_cat_item.item_type, new_item.id)
        # Apply metadata to new item
        return self.update_item(dest_cat_item, new_item.id)

    def update_item(
        self, cat_item_arc: CatalogueItemArcGis, item_id: str | None = None, item_portrayal: dict | None = None
    ) -> Item:
        """
        Update ArcGIS item details.

        Items are updated from a combination of:
        - an associated BAS Data Catalogue item (based on an ISO 19115 record)
        - optional ArcGIS portrayal information (e.g. symbology, fields configuration and popups)

        ArcGIS portrayal information is typically generated interactively and can then be saved as a resource file in
        this project for reproducibility and versioning. Data can be accessed for an item via tools such as
        https://ago-assistant.esri.com (view item JSON -> Data (not description)), or directly via
        https://www.arcgis.com/sharing/rest/content/items/{item-id}/data (requires token if item is not public).

        **Note:** The ArcGIS API refers to this information as 'text' and is accessed via `item.get_data()` - both of
        which are confusingly / non-obviously named as they don't relate the item description or actual data in a layer.

        The ArcGIS item to update (`item_id`) can usually be taken from the ArcGIS Data Catalogue item (a Data
        Catalogue item with ArcGIS specific details, including item type and ID (if yet known)), and so not set
        explicitly. However, if publishing an item as another type (e.g. a feature service as an OGC feature service),
        `item_id` needs to be explicitly set to the new (ArcGIS) item, as the ArcGIS Data Catalogue item will refer to
        the original.
        """
        item_id = item_id or cat_item_arc.item_id
        self._logger.debug("Updating ArcGIS item '%s'...", item_id)

        item = self.get_item(item_id)
        properties = cat_item_arc.item_properties
        if item_portrayal is not None:
            properties.text = json.dumps(item_portrayal)
        item.update(item_properties=properties, thumbnail=cat_item_arc.thumbnail_href)
        item.sharing.sharing_level = cat_item_arc.sharing_level

        return self.get_item(item_id)

    def add_item_to_group(self, item: Item, group: Group) -> None:
        """Add an ArcGIS item to a group."""
        self._logger.debug("Adding item [%s] '%s' to group [%s] '%s' ...", item.id, item.title, group.id, group.title)
        item.sharing.groups.add(group=group)

    def overwrite_service_features(self, features_id: str, geojson_id: str, data: FeatureCollection) -> None:
        """Overwrite features in an ArcGIS feature layer."""
        self._logger.debug("Overwriting features in ArcGIS item '%s' via source item '%s'...", features_id, geojson_id)
        feature_item = self.get_item(features_id)
        collection = FeatureLayerCollection.fromitem(feature_item)

        geojson_item = self.get_item(geojson_id)
        with TemporaryDirectory() as temp_dir:
            self._logger.debug("Writing out layer data to temporary file for upload...")
            data_path = self._dump_data(Path(temp_dir), data, geojson_item.name)

            try:
                result = collection.manager.overwrite(str(data_path))
                self._logger.debug("Overwrite result: %s", result)
            except Exception as e:
                if "Internal Server Error" in str(e):
                    self._logger.exception("Overwrite failed", exc_info=e)
                    raise ArcGISInternalServerError() from e

                self._logger.exception("Overwrite failed", exc_info=e)
                raise e from e
