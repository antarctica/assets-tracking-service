from bs4 import BeautifulSoup

from assets_tracking_service.lib.bas_data_catalogue.models.item.catalogue import ItemCatalogue


class TestItemTemplate:
    """Test base catalogue item template."""

    def test_root_element(self, fx_lib_item_catalogue: ItemCatalogue):
        """
        Can get <html> element.

        Basic sanity check.
        """
        html = BeautifulSoup(fx_lib_item_catalogue.render(), parser="html.parser", features="lxml")
        assert html.select_one("html") is not None
