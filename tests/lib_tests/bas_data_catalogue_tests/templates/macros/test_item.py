from datetime import date

import pytest
from bs4 import BeautifulSoup
from conftest import _lib_item_catalogue_min

from assets_tracking_service.lib.bas_data_catalogue.models.item.catalogue import ItemCatalogue, Tab
from assets_tracking_service.lib.bas_data_catalogue.models.record import Date
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.common import Identifier
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.identification import (
    Aggregation,
    Aggregations,
    GraphicOverview,
    GraphicOverviews,
)
from assets_tracking_service.lib.bas_data_catalogue.models.record.enums import (
    AggregationAssociationCode,
    AggregationInitiativeCode,
)


class TestMacrosItem:
    """Test item template macros."""

    def test_header(self, fx_lib_item_catalogue: ItemCatalogue):
        """Can get item header with expected values from item."""
        html = BeautifulSoup(fx_lib_item_catalogue.render(), parser="html.parser", features="lxml")
        expected = fx_lib_item_catalogue.page_header

        assert html.select_one("#item-header-type i")["class"] == expected.subtitle[1].split(" ")
        assert html.select_one("#item-header-type").text.strip() == expected.subtitle[0]
        assert html.select_one("#item-header-title").text.strip() == expected.title

    @pytest.mark.parametrize(
        "value",
        [
            Aggregations([]),
            Aggregations(
                [
                    Aggregation(
                        identifier=Identifier(identifier="x", href="x", namespace="x"),
                        association_type=AggregationAssociationCode.LARGER_WORK_CITATION,
                        initiative_type=AggregationInitiativeCode.COLLECTION,
                    )
                ]
            ),
            Aggregations(
                [
                    Aggregation(
                        identifier=Identifier(identifier="x", href="x", namespace="x"),
                        association_type=AggregationAssociationCode.LARGER_WORK_CITATION,
                        initiative_type=AggregationInitiativeCode.COLLECTION,
                    ),
                    Aggregation(
                        identifier=Identifier(identifier="y", href="x", namespace="y"),
                        association_type=AggregationAssociationCode.LARGER_WORK_CITATION,
                        initiative_type=AggregationInitiativeCode.COLLECTION,
                    ),
                ]
            ),
        ],
    )
    def test_collections(self, fx_lib_item_catalogue: ItemCatalogue, value: Aggregations):
        """Can get item graphics with expected values from item."""
        fx_lib_item_catalogue._record.identification.aggregations = value
        expected = fx_lib_item_catalogue.summary.collections
        html = BeautifulSoup(fx_lib_item_catalogue.render(), parser="html.parser", features="lxml")

        if len(expected) > 0:
            assert html.select_one("#summary-collections") is not None
        else:
            assert html.select_one("#summary-collections") is None

        for collection in expected:
            assert html.select_one(f"a[href='{collection.href}']") is not None

    @pytest.mark.parametrize("value", [None, "x"])
    def test_edition(self, fx_lib_item_catalogue: ItemCatalogue, value: str | None):
        """Can get item edition with expected value from item."""
        fx_lib_item_catalogue._record.identification.edition = value
        expected = fx_lib_item_catalogue.summary.edition
        html = BeautifulSoup(fx_lib_item_catalogue.render(), parser="html.parser", features="lxml")

        if expected is None:
            assert html.select_one("#summary-edition") is None
        else:
            assert html.select_one("#summary-edition").text.strip() == expected

    @pytest.mark.parametrize("value", [None, (Date(date=date(2023, month=10, day=31)))])
    def test_published(self, fx_lib_item_catalogue: ItemCatalogue, value: Date | None):
        """Can get item publication with expected value from item."""
        fx_lib_item_catalogue._record.identification.dates.publication = value
        expected = fx_lib_item_catalogue.summary.published
        html = BeautifulSoup(fx_lib_item_catalogue.render(), parser="html.parser", features="lxml")

        if expected is None:
            assert html.select_one("#summary-published") is None
        else:
            assert html.select_one("#summary-published").text.strip() == expected.value
            assert html.select_one("#summary-published")["datetime"] == expected.datetime

    @pytest.mark.parametrize("value", [None, "x"])
    def test_citation(self, fx_lib_item_catalogue: ItemCatalogue, value: str | None):
        """Can get item citation with expected value from item."""
        fx_lib_item_catalogue._record.identification.other_citation_details = value
        expected = fx_lib_item_catalogue.summary.citation
        html = BeautifulSoup(fx_lib_item_catalogue.render(), parser="html.parser", features="lxml")

        if expected is None:
            assert html.select_one("#summary-citation") is None
        else:
            assert expected in str(html.select_one("#summary-citation"))

    _published = Date(date=date(2023, month=10, day=31))

    def test_abstract(self, fx_lib_item_catalogue: ItemCatalogue):
        """Can get item abstract with expected value from item."""
        html = BeautifulSoup(fx_lib_item_catalogue.render(), parser="html.parser", features="lxml")
        expected = fx_lib_item_catalogue.summary.abstract
        assert expected in str(html.select_one("#summary-abstract"))

    @pytest.mark.parametrize(
        "value",
        [
            GraphicOverviews([]),
            GraphicOverviews([GraphicOverview(identifier="x", href="x", mime_type="x")]),
            GraphicOverviews(
                [
                    GraphicOverview(identifier="x", href="x", mime_type="x"),
                    GraphicOverview(identifier="y", href="y", mime_type="y"),
                ]
            ),
        ],
    )
    def test_graphics(self, fx_lib_item_catalogue: ItemCatalogue, value: GraphicOverviews):
        """Can get item graphics with expected values from item."""
        fx_lib_item_catalogue._record.identification.graphic_overviews = value
        expected = fx_lib_item_catalogue.graphics
        html = BeautifulSoup(fx_lib_item_catalogue.render(), parser="html.parser", features="lxml")

        assert html.select_one("#item-graphics") is not None

        for graphic in expected:
            graphic_html = html.select_one(f"#graphics-{graphic.identifier}")
            assert graphic_html is not None
            assert graphic_html["src"] == graphic.href

    @pytest.mark.parametrize("tab", _lib_item_catalogue_min().tabs)
    def test_tabs_nav(self, fx_lib_item_catalogue: ItemCatalogue, tab: Tab):
        """Can get enabled tabs based on item."""
        html = BeautifulSoup(fx_lib_item_catalogue.render(), parser="html.parser", features="lxml")
        tab_input = html.select_one(f"#tab-{tab.anchor}")
        tab_label = html.select_one(f"label[for=tab-{tab.anchor}]")
        tab_content = html.select_one(f"#tab-content-{tab.anchor}")

        if tab.enabled:
            assert tab_input is not None
            assert tab_content is not None
            assert tab_label.select_one("i")["class"] == tab.icon.split(" ")
            assert tab_label.text.strip() == tab.title
        else:
            assert tab_input is None
            assert tab_label is None
            assert tab_content is None

    def test_tab_nav_default(self, fx_lib_item_catalogue: ItemCatalogue):
        """
        Can get default tab based on item.

        Tab switching is not tested here as it's dynamic, see e2e tests.
        """
        html = BeautifulSoup(fx_lib_item_catalogue.render(), parser="html.parser", features="lxml")
        expected = fx_lib_item_catalogue.default_tab_anchor

        tab_input = html.select_one(f"#tab-{expected}")["checked"]
        assert tab_input is not None
