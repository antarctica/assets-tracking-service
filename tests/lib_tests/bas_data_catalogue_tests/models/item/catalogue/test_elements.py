from datetime import UTC, date, datetime

import pytest

from assets_tracking_service.lib.bas_data_catalogue.models.item.base.elements import Extent as ItemExtent
from assets_tracking_service.lib.bas_data_catalogue.models.item.base.elements import Link
from assets_tracking_service.lib.bas_data_catalogue.models.item.catalogue import (
    Aggregations,
    Dates,
    Extent,
    PageHeader,
    Summary,
)
from assets_tracking_service.lib.bas_data_catalogue.models.item.catalogue.elements import (
    ItemSummaryCatalogue,
    format_date,
)
from assets_tracking_service.lib.bas_data_catalogue.models.item.catalogue.enums import ResourceTypeIcon
from assets_tracking_service.lib.bas_data_catalogue.models.record import RecordSummary
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.common import Date, Identifier
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.common import Dates as RecordDates
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.identification import (
    Aggregation,
    BoundingBox,
    ExtentGeographic,
    ExtentTemporal,
    TemporalPeriod,
)
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.identification import (
    Aggregations as RecordAggregations,
)
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.identification import Extent as RecordExtent
from assets_tracking_service.lib.bas_data_catalogue.models.record.enums import (
    AggregationAssociationCode,
    AggregationInitiativeCode,
    DatePrecisionCode,
    DateTypeCode,
    HierarchyLevelCode,
)
from tests.conftest import _lib_get_record_summary


class TestFormatDate:
    """Test `format_date` util function."""

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (Date(date=date(2014, 1, 1), precision=DatePrecisionCode.YEAR), "2014"),
            (Date(date=date(2014, 6, 1), precision=DatePrecisionCode.MONTH), "June 2014"),
            (Date(date=date(2014, 6, 30)), "30 June 2014"),
            (Date(date=datetime(2014, 6, 30, 13, tzinfo=UTC)), "30 June 2014 13:00:00 UTC"),
            (Date(date=datetime(2014, 6, 29, 1, tzinfo=UTC)), "29 June 2014"),
        ],
    )
    def test_format(self, value: Date, expected: str):
        """Can format a date(time) as a string."""
        now = datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC)
        result = format_date(value, relative_to=now)
        assert result == expected

    def test_invalid_date(self):
        """Cannot process an invalid value."""
        now = datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC)
        with pytest.raises(TypeError):
            # noinspection PyTypeChecker
            format_date("", relative_to=now)


class TestAggregations:
    """Test Catalogue aggregations."""

    def test_init(self):
        """Can create an Aggregations collection."""
        expected_aggregation = Aggregation(
            identifier=Identifier(identifier="x", href="x", namespace="x"),
            association_type=AggregationAssociationCode.LARGER_WORK_CITATION,
            initiative_type=AggregationInitiativeCode.COLLECTION,
        )
        expected_summary = _lib_get_record_summary("x")
        record_aggregations = RecordAggregations([expected_aggregation])

        aggregations = Aggregations(aggregations=record_aggregations, get_summary=_lib_get_record_summary)

        assert isinstance(aggregations, Aggregations)
        assert len(aggregations) == 1
        assert aggregations._aggregations[0] == expected_aggregation
        assert aggregations._summaries["x"]._record_summary == expected_summary

    def test_as_links(self):
        """Can get any item summaries as generic links."""
        expected = Aggregation(
            identifier=Identifier(identifier="x", href="x", namespace="x"),
            association_type=AggregationAssociationCode.LARGER_WORK_CITATION,
            initiative_type=AggregationInitiativeCode.COLLECTION,
        )
        record_aggregations = RecordAggregations([expected])
        aggregations = Aggregations(record_aggregations, get_summary=_lib_get_record_summary)

        links = aggregations.as_links(aggregations.collections)

        assert all(isinstance(link, Link) for link in links)

    def test_collections(self):
        """Can get any collection aggregations (item is part of)."""
        expected = Aggregation(
            identifier=Identifier(identifier="x", href="x", namespace="x"),
            association_type=AggregationAssociationCode.LARGER_WORK_CITATION,
            initiative_type=AggregationInitiativeCode.COLLECTION,
        )
        record_aggregations = RecordAggregations([expected])
        aggregations = Aggregations(record_aggregations, get_summary=_lib_get_record_summary)

        assert len(aggregations.collections) > 0

    def test_items(self):
        """Can get any item aggregations (item is made up of)."""
        expected = Aggregation(
            identifier=Identifier(identifier="x", href="x", namespace="x"),
            association_type=AggregationAssociationCode.IS_COMPOSED_OF,
            initiative_type=AggregationInitiativeCode.COLLECTION,
        )
        record_aggregations = RecordAggregations([expected])
        aggregations = Aggregations(record_aggregations, get_summary=_lib_get_record_summary)

        assert len(aggregations.items) > 0


class TestDates:
    """Test Catalogue dates."""

    def test_init(self):
        """Can create a Dates collection."""
        record_dates = RecordDates(
            creation=Date(date=datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC)),
        )

        dates = Dates(dates=record_dates)

        assert isinstance(dates, Dates)

    def test_formatting(self):
        """Can get a formatted date when accessed."""
        date_ = Date(date=datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC))
        expected = format_date(date_)

        dates = Dates(dates=RecordDates(creation=date_))

        assert dates.creation == expected

    def test_as_dict_enum(self):
        """Can get dates as a DateTypeCode indexed dict."""
        date_ = Date(date=datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC))
        dates = Dates(dates=RecordDates(creation=date_))
        expected = {DateTypeCode.CREATION: format_date(date_)}

        assert dates.as_dict_enum() == expected

    def test_as_dict_labeled(self):
        """Can get dates as a dict with human formatted keys."""
        date_ = Date(date=datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC))
        dates = Dates(dates=RecordDates(creation=date_))
        expected = {"Item created": format_date(date_)}

        assert dates.as_dict_labeled() == expected


class TestExtent:
    """Test extent."""

    def test_init(self):
        """Can create an Extent element."""
        item_extent = ItemExtent(
            RecordExtent(
                identifier="bounding",
                geographic=ExtentGeographic(
                    bounding_box=BoundingBox(
                        west_longitude=1.0, east_longitude=1.0, south_latitude=1.0, north_latitude=1.0
                    )
                ),
            )
        )

        extent = Extent(extent=item_extent, embedded_maps_endpoint="x")

        assert isinstance(extent, Extent)

    @pytest.mark.parametrize("has_value", [True, False])
    def test_start_end(self, has_value: bool):
        """Can get formated dates for temporal extent period."""
        date_ = Date(date=datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC))
        expected = format_date(date_) if has_value else None
        record_extent = RecordExtent(
            identifier="bounding",
            geographic=ExtentGeographic(
                bounding_box=BoundingBox(west_longitude=1.0, east_longitude=1.0, south_latitude=1.0, north_latitude=1.0)
            ),
        )
        if has_value:
            record_extent.temporal = ExtentTemporal(period=TemporalPeriod(start=date_, end=date_))
        item_extent = ItemExtent(record_extent)

        extent = Extent(extent=item_extent, embedded_maps_endpoint="x")

        assert extent.start == expected
        assert extent.end == expected

    def test_map_iframe(self):
        """Can get iframe fragment for embedded map of extent."""
        item_extent = ItemExtent(
            RecordExtent(
                identifier="bounding",
                geographic=ExtentGeographic(
                    bounding_box=BoundingBox(
                        west_longitude=1.0, east_longitude=2.0, south_latitude=3.0, north_latitude=4.0
                    )
                ),
            )
        )
        expected_bbox = "[1.0,2.0,4.0,3.0]"
        expected_url = f"https://example.com/?bbox={expected_bbox}&globe-overview"
        expected = f"<iframe src='{expected_url}' width='100%' height='400' frameborder='0'></iframe>"

        extent = Extent(extent=item_extent, embedded_maps_endpoint="https://example.com")
        assert extent.map_iframe == expected


class TestItemSummaryCatalogue:
    """Test catalogue item summary."""

    def test_init(self, fx_lib_record_summary_minimal_item: RecordSummary):
        """Can create an ItemSummaryCatalogue."""
        summary = ItemSummaryCatalogue(fx_lib_record_summary_minimal_item)

        assert isinstance(summary, ItemSummaryCatalogue)
        assert summary._record_summary == fx_lib_record_summary_minimal_item

    @pytest.mark.parametrize(("value", "expected"), [("x", "<p>x</p>"), ("_x_", "<p><em>x</em></p>")])
    def test_title_html(self, fx_lib_record_summary_minimal_item: RecordSummary, value: str, expected: str):
        """Can get title with Markdown formatting, if present, encoded as HTML."""
        fx_lib_record_summary_minimal_item.title = value
        summary = ItemSummaryCatalogue(fx_lib_record_summary_minimal_item)

        assert summary.title_html == expected

    def test_resource_type_icon(self, fx_lib_record_summary_minimal_item: RecordSummary):
        """Can get icon for resource type."""
        summary = ItemSummaryCatalogue(fx_lib_record_summary_minimal_item)
        assert summary._resource_type_icon == ResourceTypeIcon[summary.resource_type.name].value

    @pytest.mark.parametrize("has_date", [True, False])
    def test_date(self, fx_lib_record_summary_minimal_item: RecordSummary, has_date: bool):
        """Can get formatted publication date if set."""
        publication = Date(date=datetime(2014, 6, 30, tzinfo=UTC).date())
        expected = "30 June 2014" if has_date else None
        if has_date:
            fx_lib_record_summary_minimal_item.publication = publication
        summary = ItemSummaryCatalogue(fx_lib_record_summary_minimal_item)
        assert summary._date == expected

    @pytest.mark.parametrize(
        ("resource_type", "edition", "expected_edition", "has_pub", "expected_date"),
        [
            (HierarchyLevelCode.PRODUCT, "x", "x", True, "30 June 2014"),
            (HierarchyLevelCode.PRODUCT, "x", "x", False, None),
            (HierarchyLevelCode.PRODUCT, None, None, True, "30 June 2014"),
            (HierarchyLevelCode.COLLECTION, "x", None, True, False),
            (HierarchyLevelCode.COLLECTION, "x", None, False, None),
        ],
    )
    def test_fragments(
        self,
        fx_lib_record_summary_minimal_item: RecordSummary,
        resource_type: HierarchyLevelCode,
        edition: str | None,
        expected_edition: str | None,
        has_pub: bool,
        expected_date: str | None,
    ):
        """Can get fragments to use as part of item summary UI."""
        fx_lib_record_summary_minimal_item.hierarchy_level = resource_type
        fx_lib_record_summary_minimal_item.edition = edition
        if has_pub:
            fx_lib_record_summary_minimal_item.publication = Date(date=datetime(2014, 6, 30, tzinfo=UTC).date())
        summary = ItemSummaryCatalogue(fx_lib_record_summary_minimal_item)

        result = summary.fragments

        if resource_type != HierarchyLevelCode.COLLECTION:
            if edition and has_pub:
                assert len(result) == 3
            elif edition or has_pub:
                assert len(result) == 2
            else:
                assert len(result) == 1
        else:
            assert len(result) == 1

    @pytest.mark.parametrize(
        ("href", "expected"),
        [
            ("x", "x"),
            (
                None,
                "data:image/png;base64, iVB",
            ),
        ],
    )
    def test_href_graphic(self, fx_lib_record_summary_minimal_item: RecordSummary, href: str | None, expected: str):
        """Can get href graphic."""
        fx_lib_record_summary_minimal_item.graphic_overview_href = href
        summary = ItemSummaryCatalogue(fx_lib_record_summary_minimal_item)
        if href is not None:
            assert summary.href_graphic == expected
        else:
            assert summary.href_graphic.startswith(expected)


class TestPageHeader:
    """Test page header."""

    def test_init(self):
        """Can create a page header element."""
        expected_title = "x"
        title = f"<p>{expected_title}</p>"
        type_ = HierarchyLevelCode.PRODUCT
        expected_icon = ResourceTypeIcon[type_.name].value
        expected_type = HierarchyLevelCode.PRODUCT.value

        header = PageHeader(title=title, item_type=type_)

        assert header.title == expected_title
        assert header.subtitle == (expected_type, expected_icon)


class TestSummary:
    """Test summary panel."""

    @pytest.mark.parametrize(
        ("item_type", "edition", "published", "aggregations", "citation"),
        [
            (
                HierarchyLevelCode.PRODUCT,
                "x",
                "x",
                Aggregations(
                    aggregations=RecordAggregations(
                        [
                            Aggregation(
                                identifier=Identifier(identifier="x", href="x", namespace="x"),
                                association_type=AggregationAssociationCode.LARGER_WORK_CITATION,
                                initiative_type=AggregationInitiativeCode.COLLECTION,
                            )
                        ]
                    ),
                    get_summary=_lib_get_record_summary,
                ),
                "x",
            ),
            (
                HierarchyLevelCode.PRODUCT,
                None,
                None,
                Aggregations(aggregations=RecordAggregations([]), get_summary=_lib_get_record_summary),
                None,
            ),
            (
                HierarchyLevelCode.COLLECTION,
                "x",
                "x",
                Aggregations(
                    aggregations=RecordAggregations(
                        [
                            Aggregation(
                                identifier=Identifier(identifier="x", href="x", namespace="x"),
                                association_type=AggregationAssociationCode.IS_COMPOSED_OF,
                                initiative_type=AggregationInitiativeCode.COLLECTION,
                            )
                        ]
                    ),
                    get_summary=_lib_get_record_summary,
                ),
                "x",
            ),
        ],
    )
    def test_init(
        self,
        item_type: HierarchyLevelCode,
        edition: str | None,
        published: str | None,
        aggregations: Aggregations,
        citation: str | None,
    ):
        """Can create class for summary panel."""
        collections = aggregations.as_links(aggregations.collections)
        items_count = len(aggregations.items)

        summary = Summary(
            item_type=item_type,
            edition=edition,
            published_date=published,
            revision_date=None,
            aggregations=aggregations,
            citation=citation,
            abstract="x",
        )

        assert summary.abstract == "x"
        assert summary.collections == collections
        assert summary.items_count == items_count

        if item_type != HierarchyLevelCode.COLLECTION:
            assert summary.edition == edition
            assert summary.published == published
            assert summary.citation == citation
        else:
            assert summary.edition is None
            assert summary.published is None
            assert summary.citation is None

    @pytest.mark.parametrize(
        ("item_type", "published", "revision", "expected"),
        [
            (HierarchyLevelCode.PRODUCT, None, None, None),
            (HierarchyLevelCode.PRODUCT, "x", None, "x"),
            (HierarchyLevelCode.PRODUCT, None, "x", None),
            (HierarchyLevelCode.PRODUCT, "x", "x", "x"),
            (HierarchyLevelCode.PRODUCT, "x", "y", "x (last updated: y)"),
            (HierarchyLevelCode.COLLECTION, "x", "y", None),
        ],
    )
    def test_published(self, item_type: HierarchyLevelCode, published: str, revision: str, expected: str):
        """Can show combination of publication and revision date if relevant."""
        summary = Summary(
            item_type=item_type,
            edition=None,
            published_date=published,
            revision_date=revision,
            aggregations=Aggregations(aggregations=RecordAggregations([]), get_summary=_lib_get_record_summary),
            citation=None,
            abstract="x",
        )

        assert summary.published == expected
