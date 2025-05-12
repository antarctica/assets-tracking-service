"""
Test specific common template macros.

By their nature common macros are used across multiple templates and so captured in numerous other tests.
Some macros with conditional logic for example are tested here specifically to verify their behaviour.
"""

from copy import deepcopy
from datetime import date

import pytest
from bs4 import BeautifulSoup
from jinja2 import Environment, PackageLoader, select_autoescape

from assets_tracking_service.lib.bas_data_catalogue.models.item.catalogue.elements import ItemSummaryCatalogue
from assets_tracking_service.lib.bas_data_catalogue.models.record import Date, HierarchyLevelCode, RecordSummary


class TestPageHeader:
    """Test page header common macro."""

    @staticmethod
    def _render(config: dict) -> str:
        _loader = PackageLoader("assets_tracking_service.lib.bas_data_catalogue", "resources/templates")
        jinja = Environment(loader=_loader, autoescape=select_autoescape(), trim_blocks=True, lstrip_blocks=True)
        template = """{% import '_macros/common.html.j2' as com %}{{ com.page_header(**config) }}"""
        return jinja.from_string(template).render(config=config)

    def test_main(self):
        """Can render a minimal page header with main content only."""
        expected = "x"
        html = BeautifulSoup(self._render({"main": expected}), parser="html.parser", features="lxml")
        assert html.select_one("h1").text.strip() == expected

    @pytest.mark.parametrize(("sub", "sub_i"), [("x", None), ("x", "x")])
    def test_subheader(self, sub: str, sub_i: str | None):
        """Can render a page header with optional subheader with and without icon."""
        html = BeautifulSoup(self._render({"sub": sub, "sub_i": sub_i}), parser="html.parser", features="lxml")

        assert html.select_one("small").text.strip() == sub
        if sub_i is not None:
            assert html.select_one("small i")["class"] == sub_i.split(" ")

    def test_id(self):
        """Can render a page header with optional id selectors for each component."""
        html = BeautifulSoup(
            self._render({"id_wrapper": "x", "id_sub": "y", "id_main": "z", "sub": "..."}),
            parser="html.parser",
            features="lxml",
        )

        assert html.select_one("#x") is not None
        assert html.select_one("#y") is not None
        assert html.select_one("#z") is not None


class TestItemSummaryMacro:
    """Test item summary common macro."""

    summary_base = ItemSummaryCatalogue(
        record_summary=RecordSummary(
            file_identifier="x",
            hierarchy_level=HierarchyLevelCode.PRODUCT,
            title="y",
            abstract="z",
            creation=Date(date=date(2023, 10, 31)),
        )
    )

    @staticmethod
    def _render(item: ItemSummaryCatalogue) -> str:
        _loader = PackageLoader("assets_tracking_service.lib.bas_data_catalogue", "resources/templates")
        jinja = Environment(loader=_loader, autoescape=select_autoescape(), trim_blocks=True, lstrip_blocks=True)
        template = """{% import '_macros/common.html.j2' as com %}{{ com.item_summary(item) }}"""
        return jinja.from_string(template).render(item=item)

    def test_anchor(self):
        """Can get title and href with expected values from summary."""
        summary = self.summary_base
        html = BeautifulSoup(self._render(summary), parser="html.parser", features="lxml")
        assert summary.title_html in str(html.select_one("a"))
        assert html.select_one("a")["href"] == summary.href

    def test_summary(self):
        """Can get summary description with expected value from summary."""
        summary = self.summary_base
        html = BeautifulSoup(self._render(summary), parser="html.parser", features="lxml")
        assert summary.summary_html in str(html.select_one("article"))

    def test_graphic(self):
        """Can get graphic with expected value from summary."""
        summary = self.summary_base
        html = BeautifulSoup(self._render(summary), parser="html.parser", features="lxml")
        assert html.select_one("img")["src"] == summary.href_graphic

    def test_type(self):
        """Can get item type with expected value from summary."""
        summary = self.summary_base
        html = BeautifulSoup(self._render(summary), parser="html.parser", features="lxml")

        # span containing item type can only be matched by text. Can't match directly because span contains <i> tag
        assert any(summary.fragments.item_type in span.text for span in html.find_all(name="span"))
        assert html.select_one("i")["class"] == summary.fragments.item_type_icon.split(" ")

    @pytest.mark.parametrize("edition", [None, "x"])
    def test_edition(self, edition: str | None):
        """Can get optional edition with expected value from summary."""
        summary = deepcopy(self.summary_base)
        summary._record_summary.edition = edition
        expected = summary.fragments.edition
        html = BeautifulSoup(self._render(summary), parser="html.parser", features="lxml")

        if expected:
            assert html.find(name="span", string=expected) is not None

    @pytest.mark.parametrize("published", [None, Date(date=date(2023, 10, 31))])
    def test_published(self, published: Date | None):
        """Can get optional publication date with expected value from summary."""
        summary = deepcopy(self.summary_base)
        summary._record_summary.publication = published
        expected = summary.fragments.published
        html = BeautifulSoup(self._render(summary), parser="html.parser", features="lxml")

        if expected:
            assert html.select_one("time").text.strip() == expected.value
            assert html.select_one("time")["datetime"] == expected.datetime
