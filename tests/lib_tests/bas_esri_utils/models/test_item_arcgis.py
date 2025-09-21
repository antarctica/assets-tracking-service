from re import escape

import pytest
from arcgis.gis import ItemTypeEnum, SharingLevel
from lantern.lib.metadata_library.models.record.elements.common import Identifier, Identifiers
from lantern.lib.metadata_library.models.record.elements.data_quality import DataQuality, Lineage
from lantern.lib.metadata_library.models.record.elements.identification import (
    Constraint,
    Constraints,
    GraphicOverview,
    GraphicOverviews,
)
from lantern.lib.metadata_library.models.record.enums import (
    ConstraintRestrictionCode,
    ConstraintTypeCode,
)
from lantern.lib.metadata_library.models.record.record import Record
from lantern.models.item.base.enums import AccessLevel

from assets_tracking_service.lib.bas_esri_utils.models.item import ArcGisItemLicenceHrefUnsupportedError, Item


class TestItemArcGIS:
    """Test ArcGIS item representation."""

    def test_init(self, fx_lib_record_minimal_item: Record):
        """Creates an ItemArcGIS."""
        item = Item(fx_lib_record_minimal_item, arcgis_item_type=ItemTypeEnum.GEOJSON, arcgis_item_name="x")

        assert item._record == fx_lib_record_minimal_item

    def test_validate_snippet(self, fx_lib_record_minimal_item: Record):
        """Cannot use a record where snippet/purpose is too long."""
        fx_lib_record_minimal_item.identification.purpose = "x" * 251

        with pytest.raises(ValueError, match=escape("ArcGIS snippet (summary/purpose) limited to 250 characters.")):
            Item(fx_lib_record_minimal_item, arcgis_item_type=ItemTypeEnum.GEOJSON, arcgis_item_name="x")

    def test_item_id(self, fx_lib_record_minimal_item: Record):
        """Can get Item ID assigned by ArcGIS (and set by caller)."""
        expected = "x"
        item = Item(
            fx_lib_record_minimal_item,
            arcgis_item_type=ItemTypeEnum.GEOJSON,
            arcgis_item_name="x",
            arcgis_item_id=expected,
        )

        assert item.item_id == expected

    def test_item_type(self, fx_lib_record_minimal_item: Record):
        """Can get the ArcGIS Item type/resource."""
        expected = ItemTypeEnum.GEOJSON
        item = Item(fx_lib_record_minimal_item, arcgis_item_type=expected, arcgis_item_name="x")

        assert item.item_type == expected

    def test_item_name(self, fx_lib_record_minimal_item: Record):
        """Can get the ArcGIS Item service name."""
        expected = "x"
        item = Item(fx_lib_record_minimal_item, arcgis_item_type=ItemTypeEnum.GEOJSON, arcgis_item_name=expected)

        assert item.item_name == expected

    @pytest.mark.cov()
    def test_title(self, fx_lib_record_minimal_item: Record):
        """Can format title without Markdown."""
        fx_lib_record_minimal_item.identification.title = "_x_"
        item = Item(fx_lib_record_minimal_item, arcgis_item_type=ItemTypeEnum.GEOJSON, arcgis_item_name="...")

        assert item.title_plain == "x"

    @pytest.mark.parametrize(("lineage", "citation", "href"), [(None, None, None), ("-y-", "-z-", "-l-")])
    def test_description(
        self, fx_lib_record_minimal_item: Record, lineage: str | None, citation: str | None, href: str | None
    ):
        """Can render description from template."""
        abstract = "-x-"

        fx_lib_record_minimal_item.identification.abstract = abstract
        if citation is not None:
            fx_lib_record_minimal_item.identification.other_citation_details = citation
        if href is not None:
            fx_lib_record_minimal_item.identification.identifiers = Identifiers(
                [Identifier(identifier="x", href=href, namespace="data.bas.ac.uk")]
            )
        if lineage is not None:
            fx_lib_record_minimal_item.data_quality = DataQuality(lineage=Lineage(statement=lineage))

        item = Item(fx_lib_record_minimal_item, arcgis_item_type=ItemTypeEnum.GEOJSON, arcgis_item_name="...")
        result = item._description

        assert abstract in result

        if lineage is not None:
            assert lineage in result
        else:
            assert "<h5>Lineage</h5>" not in result

        if citation is not None:
            assert citation in result
        else:
            assert "<h5>Citation</h5>" not in result

        if href is not None:
            assert href in result
        else:
            assert "<h5>Further Information</h5>" not in result

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (
                "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
                "Open Government Licence (OGL 3.0)",
            ),
            (None, None),
        ],
    )
    def test_terms_of_use(self, fx_lib_record_minimal_item: Record, value: str | None, expected: str | None):
        """Can render terms of use from a template."""
        if value is not None:
            fx_lib_record_minimal_item.identification.constraints = Constraints(
                [
                    Constraint(
                        type=ConstraintTypeCode.USAGE, restriction_code=ConstraintRestrictionCode.LICENSE, href=value
                    )
                ]
            )
        item = Item(fx_lib_record_minimal_item, arcgis_item_type=ItemTypeEnum.GEOJSON, arcgis_item_name="...")

        result = item._terms_of_use
        if expected is not None:
            assert expected in result
        else:
            assert result is None

    def test_terms_of_use_unknown(self, fx_lib_record_minimal_item: Record):
        """Can't render terms of use from an unknown licence."""
        fx_lib_record_minimal_item.identification.constraints = Constraints(
            [
                Constraint(
                    type=ConstraintTypeCode.USAGE, restriction_code=ConstraintRestrictionCode.LICENSE, href="invalid"
                )
            ]
        )
        item = Item(fx_lib_record_minimal_item, arcgis_item_type=ItemTypeEnum.GEOJSON, arcgis_item_name="...")

        with pytest.raises(ArcGisItemLicenceHrefUnsupportedError):
            _ = item._terms_of_use

    @pytest.mark.parametrize(
        ("purpose", "identifiers", "constraints", "lineage"),
        [
            (
                "x",
                Identifiers([Identifier(identifier="x", href="x", namespace="data.bas.ac.uk")]),
                Constraints(
                    [
                        Constraint(
                            type=ConstraintTypeCode.USAGE,
                            restriction_code=ConstraintRestrictionCode.LICENSE,
                            href="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
                        )
                    ]
                ),
                "x",
            ),
            (None, None, None, None),
        ],
    )
    def test_item_properties(
        self,
        fx_lib_record_minimal_item: Record,
        purpose: str | None,
        identifiers: Identifiers | None,
        constraints: Constraints | None,
        lineage: str | None,
    ):
        """Can get combined ArcGIS item properties."""
        expected = "x"
        item_type = ItemTypeEnum.GEOJSON
        fx_lib_record_minimal_item.identification.title = expected
        fx_lib_record_minimal_item.identification.abstract = expected
        if purpose is not None:
            fx_lib_record_minimal_item.identification.purpose = purpose
        if identifiers is not None:
            fx_lib_record_minimal_item.identification.identifiers = identifiers
        if constraints is not None:
            fx_lib_record_minimal_item.identification.constraints = constraints
        if lineage is not None:
            fx_lib_record_minimal_item.data_quality = DataQuality(lineage=Lineage(statement=lineage))
        item = Item(fx_lib_record_minimal_item, arcgis_item_type=item_type, arcgis_item_name=expected)

        result = item.item_properties
        assert result.title == expected  # matches `arcgis_item_name` until MAGIC/esri#122 resolved
        assert result.item_type == item_type
        assert expected in result.description
        assert result.access_information == "BAS"
        if (
            constraints is not None
            and constraints[0].href == "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
        ):
            assert "Open Government Licence (OGL 3.0)" in result.license_info
        assert result.metadata_editable is False

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (Constraint(type=ConstraintTypeCode.ACCESS), SharingLevel.PRIVATE),
            (
                Constraint(type=ConstraintTypeCode.ACCESS, restriction_code=ConstraintRestrictionCode.UNRESTRICTED),
                SharingLevel.EVERYONE,
            ),
            (
                Constraint(
                    type=ConstraintTypeCode.ACCESS,
                    restriction_code=ConstraintRestrictionCode.RESTRICTED,
                    href='%5B{"scheme"%3A"ms_graph"%2C"schemeVersion"%3A"1"%2C"directoryId"%3A"b311db95-32ad-438f-a101-7ba061712a4e"%2C"objectId"%3A"6fa3b48c-393c-455f-b787-c006f839b51f"}%5D',
                ),
                SharingLevel.ORG,
            ),
            (None, SharingLevel.PRIVATE),
        ],
    )
    def test_sharing_level(self, fx_lib_record_minimal_item: Record, value: Constraint | None, expected: SharingLevel):
        """Can get the ArcGIS sharing level."""
        if value is not None:
            fx_lib_record_minimal_item.identification.constraints = Constraints([value])
        item = Item(fx_lib_record_minimal_item, arcgis_item_type=ItemTypeEnum.GEOJSON, arcgis_item_name="...")

        assert item.sharing_level == expected

    def test_sharing_level_override(self, fx_lib_record_minimal_item: Record):
        """Can override the ArcGIS sharing level."""
        value = AccessLevel.BAS_ALL
        expected = SharingLevel.ORG
        item = Item(
            fx_lib_record_minimal_item, arcgis_item_type=ItemTypeEnum.GEOJSON, arcgis_item_name="...", access_type=value
        )

        assert item.sharing_level == expected

    def test_metadata(self, fx_lib_record_minimal_item: Record):
        """Can get ArcGIS item metadata."""
        fx_lib_record_minimal_item.file_identifier = "x"
        expected = f"<mdFileID>{fx_lib_record_minimal_item.file_identifier}</mdFileID>"
        item = Item(fx_lib_record_minimal_item, arcgis_item_type=ItemTypeEnum.GEOJSON, arcgis_item_name="...")

        assert expected in item.metadata

    @pytest.mark.parametrize(
        "value", [GraphicOverviews([GraphicOverview(identifier="overview-agol", href="x", mime_type="x")]), None]
    )
    def test_thumbnail_href(self, fx_lib_record_minimal_item: Record, value: GraphicOverviews | None):
        """Can get URL to optional item thumbnail."""
        expected = None
        if value is not None:
            fx_lib_record_minimal_item.identification.graphic_overviews = value
            expected = value[0].href
        item = Item(fx_lib_record_minimal_item, arcgis_item_type=ItemTypeEnum.GEOJSON, arcgis_item_name="...")

        if value is not None:
            assert item.thumbnail_href == expected
        else:
            assert item.thumbnail_href is None
