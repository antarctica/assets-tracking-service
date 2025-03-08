import contextlib
from typing import Any

from arcgis.gis import ItemProperties, ItemTypeEnum, SharingLevel
from jinja2 import Environment, PackageLoader, select_autoescape
from lxml.etree import Element, SubElement
from lxml.etree import tostring as etree_tostring

from assets_tracking_service.lib.bas_data_catalogue.models.item import (
    AccessType,
    GraphicLabelNotFoundError,
    IdentifierNamespaceNotFoundError,
)
from assets_tracking_service.lib.bas_data_catalogue.models.item import ItemBase as ItemBase
from assets_tracking_service.lib.bas_data_catalogue.models.record import Record

TERMS_OF_USE_MAPPING = {
    "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/": "licenses/ogl-3-0.j2"
}


class ArcGisItemLicenceHrefUnsupportedError(Exception):
    """Raised when the licence href value is not mapped to a licence template."""

    pass


class Item(ItemBase):
    """
    ArcGIS representation of a resource within the BAS Data Catalogue / Metadata ecosystem.

    Typically, there is a one-to-many relationship between 'BAS' and ArcGIS resources, represented by their respective
    item classes (e.g. a vector dataset resource may have feature and tile layers within ArcGIS).

    Note: The terms 'item' and 'resource' are used in both the BAS Data Catalogue / Metadata ecosystem and ArcGIS.
    When importing classes from both platforms, it is recommended to alias this class as `ItemArcGIS` or similar and
    the equivalent ArcGIS item class as `ArcGisItem`.

    Maps a 'BAS' resource to the information model used by ArcGIS items [1] (e.g. summary -> snippet). Some properties
    that are not present as distinct elements in the ArcGIS the BAS/ISO-19115 model are combined via Jinja templates
    (e.g. abstract, lineage, citation are mapped to the description). Some properties are not supported, or cannot be
    known, in the BAS/ISO model and use either fixed values or are set by the caller (e.g. the ArcGIS item ID specific
    to each representation of a 'BAS' resource).

    In general, the same information is used across all representations of a resource. However, where a GeoJSON item
    is used as the source of a feature service/layer, the sharing level (access type) can be overwritten to hide the
    source item.

    [1] https://developers.arcgis.com/documentation/glossary/item/
    """

    def __init__(
        self,
        record: Record,
        arcgis_item_type: ItemTypeEnum,
        arcgis_item_name: str,
        arcgis_item_id: str | None = None,
        access_type: AccessType | None = None,
    ) -> None:
        super().__init__(record)
        self._id = arcgis_item_id
        self._name = arcgis_item_name
        self._type = arcgis_item_type
        self._access_type = access_type  # allow access type to be overridden (for sources of services)

        _loader = PackageLoader("assets_tracking_service.lib.bas_esri_utils", "resources/templates")
        self._jinja = Environment(loader=_loader, autoescape=select_autoescape(), trim_blocks=True, lstrip_blocks=True)

    @staticmethod
    def _render_arcgis_metadata(md_file_id: str) -> str:
        """
        Generate minimal metadata using the ArcGIS metadata storage format.

        See https://doc.arcgis.com/en/arcgis-online/manage-data/metadata.htm#ESRI_SECTION1_A1309B89E2FA42A89DE1ADA1249CA6D8
        for general information about this format.

        This is used to store the ISO file identifier only, to allow ArcGIS items to be unambiguously related to an ISO
        resource.

        The wider ISO record is not included to avoid:
        - information getting out of sync
        - encoding differences between the BAS Metadata Library and ArcGIS (e.g. using gmx:Anchor elements)

        Though the ArcGIS metadata format is used, this minimal use is not considered valid by ArcGIS, and so cannot
        (and must not) be edited through AGOL or ArcPro to avoid losing the ArcGIS - ISO association.
        """
        root = Element("metadata")
        md_file_id_e = SubElement(root, "mdFileID")
        md_file_id_e.text = md_file_id
        return etree_tostring(root, encoding="unicode")

    def _render_template(self, template_path: str, **kwargs: Any) -> str:  # noqa: ANN401
        """Render Jinja template to a string."""
        template = self._jinja.get_template(template_path)
        return template.render(**kwargs)

    @property
    def _title(self) -> str:
        """
        Item title.

        Mapped from: base item title (without formatting)
        Mapped to: title (from [1])
        [1] https://developers.arcgis.com/rest/users-groups-and-items/common-parameters/#item-parameters
        """
        return self.title_plain

    @property
    def _snippet(self) -> str | None:
        """
        Item snippet (summary).

        Mapped from: base item summary (without formatting)
        Mapped to: snippet (from [1])
        [1] https://developers.arcgis.com/rest/users-groups-and-items/common-parameters/#item-parameters
        """
        return self.summary_plain

    @property
    def _description(self) -> str:
        """
        Item description rendered from a template.

        Mapped from:
            - base item abstract (with HTML encoding)
            - base item lineage (with HTML encoding) if present
            - base item citation (with HTML encoding) if present
            - base item data catalogue identifier if present
            - base item access type enum name

        Mapped to: description (from [1])
        [1] https://developers.arcgis.com/rest/users-groups-and-items/common-parameters/#item-parameters
        """
        kwargs = {"template_path": "description.j2", "abstract": self.abstract_html}

        if self.lineage_html is not None:
            kwargs["lineage"] = self.lineage_html
        if self.citation_html is not None:
            kwargs["citation"] = self.citation_html
        with contextlib.suppress(IdentifierNamespaceNotFoundError):
            kwargs["catalogue_href"] = self.get_identifier(namespace="data.bas.ac.uk").href

        return self._render_template(**kwargs)

    @property
    def _attribution(self) -> str:
        """
        Item attribution (credit).

        Always "BAS".

        Mapped to: accessInformation (from [1])
        [1] https://developers.arcgis.com/rest/users-groups-and-items/common-parameters/#item-parameters
        """
        return "BAS"

    @property
    def _terms_of_use(self) -> str | None:
        """
        Item terms of use rendered from a template.

        Mapped from: base item licence if present
        Mapped to: licenseInfo (from [1])
        [1] https://developers.arcgis.com/rest/users-groups-and-items/common-parameters/#item-parameters
        """
        if self.licence is None:
            return None
        try:
            template_name = TERMS_OF_USE_MAPPING[self.licence.href]
            return self._render_template(template_path=template_name)
        except KeyError as e:
            msg = f"Unknown licence href: '{self.licence.href}'."
            raise ArcGisItemLicenceHrefUnsupportedError(msg) from e

    @property
    def _metadata_editable(self) -> bool:
        """
        Item metadata editing control.

        Always false to prevent breaking link between ArcGIS and Catalogue items.

        Mapped to: metadataEditable (from [1])
        [1] https://developers.arcgis.com/rest/users-groups-and-items/common-parameters/#item-parameters
        """
        return False

    @property
    def item_id(self) -> str | None:
        """
        Item ID assigned by ArcGIS.

        Can uniquely identify an item within the ArcGIS platform, and distinguish representations of a resource.

        Value not held in the base item and must be set by the caller.

        Mapped to: id (from [1])
        [1] https://developers.arcgis.com/documentation/glossary/item-id/
        """
        return self._id

    @property
    def item_type(self) -> ItemTypeEnum:
        """
        Item type/resource within ArcGIS.

        Can typically distinguish different representations of a resource within the ArcGIS platform.

        E.g.:
        - a vector dataset may be represented as a GeoJSON, feature layer and vector tile layer item.
        - a product may be represented as a PDF, JPEG and web map item.

        Valid values defined by [1] and `arcgis.gis.ItemTypeEnum` enum.

        Value not held in the base item and must be set by the caller.

        Mapped to: type (from [2])

        [1] https://developers.arcgis.com/rest/users-groups-and-items/items-and-item-types/
        [2] https://developers.arcgis.com/rest/users-groups-and-items/common-parameters/#item-parameters
        """
        return self._type

    @property
    def item_name(self) -> str:
        """
        Item service name within ArcGIS.

        As per ArcGIS REST Services Directory [1]

        Value not held in the base item and must be set by the caller.

        [1] https://developers.arcgis.com/rest/services-reference/enterprise/get-started-with-the-services-directory/
        """
        return self._name

    @property
    def item_properties(self) -> ItemProperties:
        """
        Combined ArcGIS item properties.

        `item_name` used over `_title` for `title` property due to https://gitlab.data.bas.ac.uk/MAGIC/esri/-/issues/122
        """
        props = ItemProperties(
            title=self.item_name,
            item_type=self.item_type,
            description=self._description,
            access_information=self._attribution,
            license_info=self._terms_of_use,
            metadata_editable=self._metadata_editable,
        )
        if self._snippet is not None:
            props.snippet = self._snippet
        return props

    @property
    def sharing_level(self) -> SharingLevel:
        """ArcGIS sharing level based on item access type."""
        access_type = self._access_type if self._access_type is not None else super().access

        if access_type == AccessType.PUBLIC:
            return SharingLevel.EVERYONE
        if access_type == AccessType.BAS_ALL:
            return SharingLevel.ORG

        # fail-safe
        return SharingLevel.PRIVATE

    @property
    def metadata(self) -> str:
        """
        ArcGIS item metadata.

        Encoded using the ArcGIS metadata storage format.
        """
        return self._render_arcgis_metadata(self.resource_id)

    @property
    def thumbnail_href(self) -> str | None:
        """
        URL to optional item thumbnail.

        Uses 'overview-agol' graphic label if available. This graphic must be hosted somewhere accessible to the
        ArcGIS instance (Online or Enterprise). It should be sized as per Esri's recommendations.
        """
        try:
            return self.get_graphic_overview("overview-agol").src
        except GraphicLabelNotFoundError:
            return None
