import json
from datetime import UTC, datetime

import pytest

from assets_tracking_service.lib.bas_data_catalogue.models.item.base import (
    ItemBase,
    ItemSummaryBase,
    md_as_html,
    md_as_plain,
)
from assets_tracking_service.lib.bas_data_catalogue.models.item.base.elements import (
    Contact,
    Contacts,
    Extent,
    Extents,
)
from assets_tracking_service.lib.bas_data_catalogue.models.item.base.enums import AccessType
from assets_tracking_service.lib.bas_data_catalogue.models.record import DataQuality, Record, RecordSummary
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.common import Contact as RecordContact
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.common import (
    ContactIdentity,
    Date,
    Identifier,
    Identifiers,
    OnlineResource,
)
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.common import Contacts as RecordContacts
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.data_quality import Lineage
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.distribution import (
    Distribution,
    TransferOption,
)
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.identification import (
    Aggregation,
    Aggregations,
    BoundingBox,
    Constraint,
    Constraints,
    ExtentGeographic,
    GraphicOverview,
    GraphicOverviews,
)
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.identification import (
    Extent as RecordExtent,
)
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.identification import (
    Extents as RecordExtents,
)
from assets_tracking_service.lib.bas_data_catalogue.models.record.enums import (
    AggregationAssociationCode,
    AggregationInitiativeCode,
    ConstraintRestrictionCode,
    ConstraintTypeCode,
    ContactRoleCode,
    HierarchyLevelCode,
    OnlineResourceFunctionCode,
)


class TestMdAsHtml:
    """Test _md_as_html util function."""

    def test_md_as_html(self):
        """Can convert Markdown to HTML."""
        assert md_as_html("_x_") == "<p><em>x</em></p>"


class TestMdAsPlain:
    """Test _md_as_plain util function."""

    def test_md_as_plain(self):
        """Can convert Markdown to plain text."""
        assert md_as_plain("_x_") == "x"


class TestItemBase:
    """Test base item."""

    def test_init(self, fx_lib_record_minimal_item: Record):
        """Can create an ItemBase from a Record."""
        item = ItemBase(fx_lib_record_minimal_item)
        assert item._record == fx_lib_record_minimal_item

    def test_init_invalid(self, fx_lib_record_minimal_iso: Record):
        """Cannot create an ItemBase with an invalid record."""
        with pytest.raises(ValueError, match="Items require a file_identifier."):
            ItemBase(fx_lib_record_minimal_iso)

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("", []),
            ("invalid", []),
            (
                f"#{json.dumps([{'scheme': 'x', 'schemeVersion': 'x'}])}",
                [],
            ),
            (
                f"#{json.dumps([{'scheme': 'ms_graph', 'schemeVersion': '1', 'directoryId': 'x', 'objectId': 'x'}])}",
                [],
            ),
            (
                f"#{json.dumps([{'scheme': 'ms_graph', 'schemeVersion': '1', 'directoryId': 'b311db95-32ad-438f-a101-7ba061712a4e', 'objectId': '6fa3b48c-393c-455f-b787-c006f839b51f'}])}",
                [AccessType.BAS_ALL],
            ),
        ],
    )
    def test_parse_permissions(self, fx_lib_record_minimal_item: Record, value: str, expected: list[AccessType]):
        """Can parse permissions string."""
        item = ItemBase(fx_lib_record_minimal_item)
        result = item._parse_permissions(value)
        assert result == expected

    def test_abstract_raw(self, fx_lib_record_minimal_item: Record):
        """Can get aw Abstract."""
        expected = "x"
        fx_lib_record_minimal_item.identification.abstract = expected
        item = ItemBase(fx_lib_record_minimal_item)

        assert item.abstract_raw == expected

    def test_abstract_md(self, fx_lib_record_minimal_item: Record):
        """Can get abstract with Markdown formatting if present."""
        expected = "x"
        fx_lib_record_minimal_item.identification.abstract = expected
        item = ItemBase(fx_lib_record_minimal_item)

        assert item.abstract_md == expected

    def test_abstract_html(self, fx_lib_record_minimal_item: Record):
        """Can get abstract with Markdown formatting, if present, encoded as HTML."""
        value = "_x_"
        expected = "<p><em>x</em></p>"
        fx_lib_record_minimal_item.identification.abstract = value
        item = ItemBase(fx_lib_record_minimal_item)

        assert item.abstract_html == expected

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (Constraint(type=ConstraintTypeCode.ACCESS), AccessType.NONE),
            (
                Constraint(type=ConstraintTypeCode.ACCESS, restriction_code=ConstraintRestrictionCode.UNRESTRICTED),
                AccessType.PUBLIC,
            ),
            (
                Constraint(
                    type=ConstraintTypeCode.ACCESS,
                    restriction_code=ConstraintRestrictionCode.RESTRICTED,
                    href='%5B{"scheme"%3A"ms_graph"%2C"schemeVersion"%3A"1"%2C"directoryId"%3A"b311db95-32ad-438f-a101-7ba061712a4e"%2C"objectId"%3A"6fa3b48c-393c-455f-b787-c006f839b51f"}%5D',
                ),
                AccessType.BAS_ALL,
            ),
            (None, AccessType.NONE),
        ],
    )
    def test_access(self, fx_lib_record_minimal_item: Record, value: Constraint | None, expected: AccessType):
        """Can get optional access constraint and any associated permissions."""
        if value is not None:
            fx_lib_record_minimal_item.identification.constraints = Constraints([value])
        item = ItemBase(fx_lib_record_minimal_item)

        assert item.access == expected

    def test_aggregations(self, fx_lib_record_minimal_item: Record):
        """Can get aggregations from record."""
        expected = Aggregation(
            identifier=Identifier(identifier="x", href="x", namespace="x"),
            association_type=AggregationAssociationCode.LARGER_WORK_CITATION,
            initiative_type=AggregationInitiativeCode.COLLECTION,
        )
        fx_lib_record_minimal_item.identification.aggregations = Aggregations([expected])
        item = ItemBase(fx_lib_record_minimal_item)

        result = item.aggregations

        assert isinstance(result, Aggregations)
        assert len(result) > 0

    def test_bounding_extent(self, fx_lib_record_minimal_item: Record):
        """Can get bounding extent from record."""
        rec_extent = RecordExtent(
            identifier="bounding",
            geographic=ExtentGeographic(
                bounding_box=BoundingBox(west_longitude=1.0, east_longitude=1.0, south_latitude=1.0, north_latitude=1.0)
            ),
        )
        fx_lib_record_minimal_item.identification.extents = RecordExtents([rec_extent])
        expected = Extent(rec_extent)
        item = ItemBase(fx_lib_record_minimal_item)

        result = item.bounding_extent
        assert isinstance(result, Extent)
        assert result == expected

    @pytest.mark.parametrize("expected", ["x", None])
    def test_citation_raw(self, fx_lib_record_minimal_item: Record, expected: str | None):
        """Raw citation."""
        fx_lib_record_minimal_item.identification.other_citation_details = expected
        item = ItemBase(fx_lib_record_minimal_item)

        assert item.citation_raw == expected

    @pytest.mark.parametrize("expected", ["_x_", None])
    def test_citation_md(self, fx_lib_record_minimal_item: Record, expected: str | None):
        """Citation with Markdown formatting if present."""
        fx_lib_record_minimal_item.identification.other_citation_details = expected
        item = ItemBase(fx_lib_record_minimal_item)

        assert item.citation_md == expected

    @pytest.mark.parametrize(("value", "expected"), [("x", "<p>x</p>"), ("_x_", "<p><em>x</em></p>"), (None, None)])
    def test_citation_html(self, fx_lib_record_minimal_item: Record, value: str | None, expected: str | None):
        """
        Citation with Markdown formatting, if present, encoded as HTML.

        Parameters used to test handling of optional value.
        """
        fx_lib_record_minimal_item.identification.other_citation_details = value
        item = ItemBase(fx_lib_record_minimal_item)

        if value is None:
            assert item.citation_html is None
        if value is not None:
            assert item.citation_html.startswith("<p>")
            assert item.citation_html.endswith("</p>")
        if value == "_Markdown_":
            assert "<em>Markdown</em>" in item.citation_html

    def test_collections(self, fx_lib_record_minimal_item: Record):
        """Can filter collection aggregations from record."""
        expected = Aggregation(
            identifier=Identifier(identifier="x", href="x", namespace="x"),
            association_type=AggregationAssociationCode.LARGER_WORK_CITATION,
            initiative_type=AggregationInitiativeCode.COLLECTION,
        )
        fx_lib_record_minimal_item.identification.aggregations = Aggregations([expected])
        item = ItemBase(fx_lib_record_minimal_item)

        result = item.collections

        assert isinstance(result, Aggregations)
        assert len(result) > 0

        assert expected in result
        assert len(result) == 1
        assert result[0] == expected

    def test_contacts(self, fx_lib_record_minimal_item: Record):
        """Can get record contacts as item contacts."""
        rec_contact = RecordContact(
            organisation=ContactIdentity(name="x", title="ror", href="x"), role=[ContactRoleCode.POINT_OF_CONTACT]
        )
        fx_lib_record_minimal_item.identification.contacts = RecordContacts([rec_contact])
        expected = Contact(rec_contact)
        item = ItemBase(fx_lib_record_minimal_item)

        result = item.contacts
        assert isinstance(result, Contacts)
        assert expected in result

        # check underlying record contacts haven't been modified
        assert type(item._record.identification.contacts) is not type(result)
        assert item._record.identification.contacts != result
        assert item._record.identification.contacts[0] != result[0]
        with pytest.raises(AttributeError):
            # noinspection PyUnresolvedReferences
            _ = item._record.identification.contacts[0].ror

    def test_constraints(self, fx_lib_record_minimal_item: Record):
        """Can get constraints from record."""
        expected = Constraint(type=ConstraintTypeCode.ACCESS)
        fx_lib_record_minimal_item.identification.constraints = Constraints([expected])
        item = ItemBase(fx_lib_record_minimal_item)

        result = item.constraints

        assert isinstance(result, Constraints)
        assert len(result) > 0

    def test_distributions(self, fx_lib_record_minimal_item: Record):
        """Can get record distributions as item distributions."""
        expected = [
            Distribution(
                distributor=RecordContact(organisation=ContactIdentity(name="x"), role=[ContactRoleCode.DISTRIBUTOR]),
                transfer_option=TransferOption(
                    online_resource=OnlineResource(href="x", function=OnlineResourceFunctionCode.DOWNLOAD)
                ),
            )
        ]
        fx_lib_record_minimal_item.distribution = expected

        item = ItemBase(fx_lib_record_minimal_item)

        assert item.distributions == expected

    def test_edition(self, fx_lib_record_minimal_item: Record):
        """Can get edition."""
        expected = "x"
        fx_lib_record_minimal_item.identification.edition = "x"
        item = ItemBase(fx_lib_record_minimal_item)

        assert item.edition == expected

    def test_extents(self, fx_lib_record_minimal_item: Record):
        """Can get record extents as item extents."""
        rec_extent = RecordExtent(
            identifier="bounding",
            geographic=ExtentGeographic(
                bounding_box=BoundingBox(west_longitude=1.0, east_longitude=1.0, south_latitude=1.0, north_latitude=1.0)
            ),
        )
        fx_lib_record_minimal_item.identification.extents = RecordExtents([rec_extent])
        expected = Extent(rec_extent)
        item = ItemBase(fx_lib_record_minimal_item)

        result = item.extents
        assert isinstance(result, Extents)
        assert expected in result

        # check underlying record extents haven't been modified
        assert type(item._record.identification.extents) is not type(result)
        assert item._record.identification.extents != result
        assert item._record.identification.extents[0] != result[0]
        with pytest.raises(AttributeError):
            # noinspection PyUnresolvedReferences
            _ = item._record.identification.extents[0].bounding_box

    def test_graphics(self, fx_lib_record_minimal_item: Record):
        """Can get graphic overviews from record."""
        expected = GraphicOverview(identifier="x", href="x", mime_type="x")
        fx_lib_record_minimal_item.identification.graphic_overviews = GraphicOverviews([expected])
        item = ItemBase(fx_lib_record_minimal_item)

        result = item.graphics

        assert isinstance(result, GraphicOverviews)
        assert len(result) > 0

    def test_identifiers(self, fx_lib_record_minimal_item: Record):
        """Can get identifiers from record."""
        expected = Identifier(identifier="x", href="x", namespace="x")
        fx_lib_record_minimal_item.identification.identifiers = Identifiers([expected])
        item = ItemBase(fx_lib_record_minimal_item)

        result = item.identifiers

        assert isinstance(result, Identifiers)
        assert len(result) > 0

    @pytest.mark.parametrize(
        "value",
        [
            Constraint(
                type=ConstraintTypeCode.USAGE,
                restriction_code=ConstraintRestrictionCode.LICENSE,
                href="x",
                statement="x",
            ),
            None,
        ],
    )
    def test_licence(self, fx_lib_record_minimal_item: Record, value: Constraint | None):
        """Can get optional licence usage constraint."""
        if value is not None:
            fx_lib_record_minimal_item.identification.constraints = Constraints([value])
        item = ItemBase(fx_lib_record_minimal_item)

        assert item.licence == value

    @pytest.mark.parametrize("expected", ["x", None])
    def test_lineage_raw(self, fx_lib_record_minimal_item: Record, expected: str | None):
        """Can get raw lineage statement."""
        if expected is not None:
            fx_lib_record_minimal_item.data_quality = DataQuality(lineage=Lineage(statement=expected))
        item = ItemBase(fx_lib_record_minimal_item)

        assert item.lineage_raw == expected

    @pytest.mark.parametrize("expected", ["_x_", None])
    def test_lineage_md(self, fx_lib_record_minimal_item: Record, expected: str | None):
        """Can get lineage statement with Markdown formatting if present."""
        if expected is not None:
            fx_lib_record_minimal_item.data_quality = DataQuality(lineage=Lineage(statement=expected))
        item = ItemBase(fx_lib_record_minimal_item)

        assert item.lineage_md == expected

    @pytest.mark.parametrize(("value", "expected"), [("x", "<p>x</p>"), ("_x_", "<p><em>x</em></p>"), (None, None)])
    def test_lineage_html(self, fx_lib_record_minimal_item: Record, value: str | None, expected: str | None):
        """Can get lineage statement with Markdown formatting, if present, encoded as HTML."""
        if expected is not None:
            fx_lib_record_minimal_item.data_quality = DataQuality(lineage=Lineage(statement=expected))
        item = ItemBase(fx_lib_record_minimal_item)

        assert item.lineage_html == expected

    def test_resource_id(self, fx_lib_record_minimal_item: Record):
        """Can get resource/file identifier."""
        expected = "x"
        item = ItemBase(fx_lib_record_minimal_item)
        item._record.file_identifier = expected

        assert item.resource_id == expected

    def test_resource_type(self, fx_lib_record_minimal_item: Record):
        """Can get resource type / hierarchy level."""
        expected = HierarchyLevelCode.DATASET
        item = ItemBase(fx_lib_record_minimal_item)

        assert item.resource_type == expected

    @pytest.mark.parametrize("expected", ["x", None])
    def test_summary_raw(self, fx_lib_record_minimal_item: Record, expected: str | None):
        """Can get optional raw Summary (purpose)."""
        fx_lib_record_minimal_item.identification.purpose = expected
        item = ItemBase(fx_lib_record_minimal_item)

        assert item.summary_raw == expected

    @pytest.mark.parametrize("expected", ["_x_", None])
    def test_summary_md(self, fx_lib_record_minimal_item: Record, expected: str | None):
        """Can get optional summary (purpose) with Markdown formatting."""
        fx_lib_record_minimal_item.identification.purpose = expected
        item = ItemBase(fx_lib_record_minimal_item)

        assert item.summary_md == expected

    @pytest.mark.parametrize(("value", "expected"), [("x", "<p>x</p>"), ("_x_", "<p><em>x</em></p>"), (None, None)])
    def test_summary_html(self, fx_lib_record_minimal_item: Record, value: str | None, expected: str | None):
        """Can get summary (purpose) with Markdown formatting, if present, encoded as HTML."""
        if expected is not None:
            fx_lib_record_minimal_item.identification.purpose = value
        item = ItemBase(fx_lib_record_minimal_item)

        assert item.summary_html == expected

    @pytest.mark.parametrize(("value", "expected"), [("x", "x"), ("_x_", "x")])
    def test_summary_plain(self, fx_lib_record_minimal_item: Record, value: str, expected: str):
        """Can get optional summary (purpose) without Markdown formatting."""
        fx_lib_record_minimal_item.identification.purpose = value
        item = ItemBase(fx_lib_record_minimal_item)

        assert item.summary_plain == expected

    def test_title_raw(self, fx_lib_record_minimal_item: Record):
        """Can get raw title."""
        item = ItemBase(fx_lib_record_minimal_item)

        assert item.title_raw == "x"

    def test_title_md(self, fx_lib_record_minimal_item: Record):
        """Can get title with Markdown formatting."""
        item = ItemBase(fx_lib_record_minimal_item)

        assert item.title_md == "x"

    @pytest.mark.parametrize(("value", "expected"), [("x", "x"), ("_x_", "x")])
    def test_title_plain(self, fx_lib_record_minimal_item: Record, value: str, expected: str):
        """Can get title without Markdown formatting."""
        fx_lib_record_minimal_item.identification.title = value
        item = ItemBase(fx_lib_record_minimal_item)

        assert item.title_plain == expected


class TestItemSummaryBase:
    """Test base item summary."""

    def test_init(self, fx_lib_record_summary_minimal_item: RecordSummary):
        """Can create an ItemSummaryBase from a Record."""
        summary = ItemSummaryBase(fx_lib_record_summary_minimal_item)
        assert summary._record_summary == fx_lib_record_summary_minimal_item

    def test_init_invalid(self, fx_lib_record_summary_minimal_item: RecordSummary):
        """Cannot create an ItemSummaryBase with an invalid record."""
        fx_lib_record_summary_minimal_item.file_identifier = None
        with pytest.raises(ValueError, match="Item Summaries require a file_identifier."):
            ItemSummaryBase(fx_lib_record_summary_minimal_item)

    @pytest.mark.parametrize("has_pub", [True, False])
    def test_date(self, fx_lib_record_summary_minimal_item: RecordSummary, has_pub: bool):
        """Can get publication date if set."""
        expected = Date(date=datetime(2014, 6, 30, tzinfo=UTC).date()) if has_pub else None
        if has_pub:
            fx_lib_record_summary_minimal_item.publication = expected
        summary = ItemSummaryBase(fx_lib_record_summary_minimal_item)

        assert summary.date == expected

    @pytest.mark.parametrize("expected", ["x", None])
    def test_edition(self, fx_lib_record_summary_minimal_item: RecordSummary, expected: str | None):
        """Can get edition if defined."""
        fx_lib_record_summary_minimal_item.edition = expected
        summary = ItemSummaryBase(fx_lib_record_summary_minimal_item)

        assert summary.edition == expected

    def test_href(self, fx_lib_record_summary_minimal_item: RecordSummary):
        """Can get item href."""
        expected = f"/items/{fx_lib_record_summary_minimal_item.file_identifier}/"
        summary = ItemSummaryBase(fx_lib_record_summary_minimal_item)

        assert summary.href == expected

    @pytest.mark.parametrize("expected", ["x", None])
    def test_href_graphic(self, fx_lib_record_summary_minimal_item: RecordSummary, expected: str | None):
        """Can get href to graphic overview if defined."""
        fx_lib_record_summary_minimal_item.graphic_overview_href = expected
        summary = ItemSummaryBase(fx_lib_record_summary_minimal_item)

        assert summary.href_graphic == expected

    def test_resource_id(self, fx_lib_record_summary_minimal_item: RecordSummary):
        """Can get resource/file identifier."""
        summary = ItemSummaryBase(fx_lib_record_summary_minimal_item)
        assert summary.resource_id == fx_lib_record_summary_minimal_item.file_identifier

    def test_resource_type(self, fx_lib_record_summary_minimal_item: RecordSummary):
        """Can get resource type / hierarchy level."""
        summary = ItemSummaryBase(fx_lib_record_summary_minimal_item)
        assert summary.resource_type == fx_lib_record_summary_minimal_item.hierarchy_level

    @pytest.mark.parametrize(("value", "expected"), [("x", "x"), (None, "y")])
    def test_summary_raw(self, fx_lib_record_summary_minimal_item: RecordSummary, value: str | None, expected: str):
        """Can get summary as either purpose or if not set, abstract."""
        fx_lib_record_summary_minimal_item.purpose = value
        fx_lib_record_summary_minimal_item.abstract = "y"
        summary = ItemSummaryBase(fx_lib_record_summary_minimal_item)

        assert summary.summary_raw == expected

    @pytest.mark.parametrize(("value", "expected"), [("_x_", "_x_"), (None, "_y_")])
    def test_summary_md(self, fx_lib_record_summary_minimal_item: RecordSummary, value: str | None, expected: str):
        """Can get optional summary (purpose) with Markdown formatting."""
        fx_lib_record_summary_minimal_item.purpose = value
        fx_lib_record_summary_minimal_item.abstract = "_y_"
        summary = ItemSummaryBase(fx_lib_record_summary_minimal_item)

        assert summary.summary_md == expected

    @pytest.mark.parametrize(
        ("value", "expected"), [("x", "<p>x</p>"), ("_x_", "<p><em>x</em></p>"), (None, "<p>y</p>")]
    )
    def test_summary_html(
        self, fx_lib_record_summary_minimal_item: RecordSummary, value: str | None, expected: str | None
    ):
        """Can get summary (purpose) with Markdown formatting, if present, encoded as HTML."""
        if expected is not None:
            fx_lib_record_summary_minimal_item.purpose = value
        fx_lib_record_summary_minimal_item.abstract = "y"
        summary = ItemSummaryBase(fx_lib_record_summary_minimal_item)

        assert summary.summary_html == expected

    @pytest.mark.parametrize(("value", "expected"), [("_x_", "x"), (None, "y")])
    def test_summary_plain(self, fx_lib_record_summary_minimal_item: RecordSummary, value: str, expected: str):
        """Can get optional summary (purpose) without Markdown formatting."""
        fx_lib_record_summary_minimal_item.purpose = value
        fx_lib_record_summary_minimal_item.abstract = "_y_"
        summary = ItemSummaryBase(fx_lib_record_summary_minimal_item)

        assert summary.summary_plain == expected

    def test_title_raw(self, fx_lib_record_summary_minimal_item: RecordSummary):
        """Can get raw title."""
        summary = ItemSummaryBase(fx_lib_record_summary_minimal_item)
        assert summary.title_raw == "x"

    def test_title_md(self, fx_lib_record_summary_minimal_item: RecordSummary):
        """Can get title with Markdown formatting."""
        summary = ItemSummaryBase(fx_lib_record_summary_minimal_item)
        assert summary.title_md == "x"

    @pytest.mark.parametrize(("value", "expected"), [("x", "x"), ("_x_", "x")])
    def test_title_plain(self, fx_lib_record_summary_minimal_item: RecordSummary, value: str, expected: str):
        """Can get title without Markdown formatting."""
        fx_lib_record_summary_minimal_item.title = value
        summary = ItemSummaryBase(fx_lib_record_summary_minimal_item)

        assert summary.title_plain == expected
