import json

import pytest
from bs4 import BeautifulSoup

from assets_tracking_service.lib.bas_data_catalogue.models.item.catalogue import ItemCatalogue


class TestMacrosSite:
    """Test site template macros."""

    def test_head_meta(self, fx_lib_item_catalogue_min: ItemCatalogue):
        """
        Can get static HTML character set.

        Basic sanity check.
        """
        html = BeautifulSoup(fx_lib_item_catalogue_min.render(), parser="html.parser", features="lxml")
        assert html.head.meta["charset"] == "utf-8"

    def test_head_favicon(self, fx_lib_item_catalogue_min: ItemCatalogue):
        """Can get static favicon."""
        html = BeautifulSoup(fx_lib_item_catalogue_min.render(), parser="html.parser", features="lxml")
        assert html.head.find(name="link", rel="icon") is not None

    def test_head_title(self, fx_lib_item_catalogue_min: ItemCatalogue):
        """Can get <title> with expected value from item."""
        html = BeautifulSoup(fx_lib_item_catalogue_min.render(), parser="html.parser", features="lxml")
        assert html.head.title.string == fx_lib_item_catalogue_min.html_title

    @pytest.mark.parametrize(
        "href", ["https://cdn.web.bas.ac.uk/libs/font-awesome-pro/5.13.0/css/all.min.css", "/static/css/main.css"]
    )
    def test_head_styles(self, fx_lib_item_catalogue_min: ItemCatalogue, href: str):
        """Can get static CSS references."""
        html = BeautifulSoup(fx_lib_item_catalogue_min.render(), parser="html.parser", features="lxml")
        assert html.head.find(name="link", rel="stylesheet", href=href) is not None

    def test_head_open_graph(self, fx_lib_item_catalogue_min: ItemCatalogue):
        """
        Can get Open Graph <meta> tags with expected values from item.

        This only checks that Open Graph properties are rendered. The specific properties that should (not) be
        included are tested elsewhere.
        """
        html = BeautifulSoup(fx_lib_item_catalogue_min.render(), parser="html.parser", features="lxml")
        for key, val in fx_lib_item_catalogue_min.html_open_graph.items():
            assert html.head.find(name="meta", property=key)["content"] == val

    def test_head_schema_org(self, fx_lib_item_catalogue_min: ItemCatalogue):
        """
        Can get schema.org script content with expected values from item.

        This only checks that schema.org properties are rendered. The specific properties that should (not) be
        included are tested elsewhere.
        """
        html = BeautifulSoup(fx_lib_item_catalogue_min.render(), parser="html.parser", features="lxml")
        expected = json.loads(fx_lib_item_catalogue_min.html_schema_org)
        data = json.loads(html.head.find(name="script", type="application/ld+json").string)
        assert expected == data

    def test_top_anchor(self, fx_lib_item_catalogue_min: ItemCatalogue):
        """Can get static page top anchor."""
        html = BeautifulSoup(fx_lib_item_catalogue_min.render(), parser="html.parser", features="lxml")
        assert html.find(id="site-top") is not None

    def test_navbar_title(self, fx_lib_item_catalogue_min: ItemCatalogue):
        """Can get site title in navbar with expected static value."""
        html = BeautifulSoup(fx_lib_item_catalogue_min.render(), parser="html.parser", features="lxml")
        assert html.find(id="site-title").string.strip() == "BAS Data Catalogue"

    def test_dev_phase(self, fx_lib_item_catalogue_min: ItemCatalogue):
        """Can get site dev phase label with expected static value."""
        html = BeautifulSoup(fx_lib_item_catalogue_min.render(), parser="html.parser", features="lxml")
        assert html.find(id="site-dev-phase").string.strip() == "alpha"

    def test_footer(self, fx_lib_item_catalogue_min: ItemCatalogue):
        """Can get static site footer."""
        html = BeautifulSoup(fx_lib_item_catalogue_min.render(), parser="html.parser", features="lxml")
        assert html.find(id="site-footer") is not None
