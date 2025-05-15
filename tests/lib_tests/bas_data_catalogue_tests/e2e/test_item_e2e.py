from subprocess import Popen

from playwright.sync_api import Page, expect

from tests.resources.lib.data_catalogue.records.item_cat_product_min import record as product_min_supported


class TestItemTabs:
    """Test tabs implementation in Catalogue Item template."""

    def test_switch(self, fx_lib_exporter_static_hostname: str, fx_lib_exporter_static_server: Popen, page: Page):
        """Can switch between tabs."""
        endpoint = (
            f"http://{fx_lib_exporter_static_hostname}:8123/items/{product_min_supported.file_identifier}/index.html"
        )
        page.goto(endpoint)

        # initial tab will be 'licence', expect element from another tab not to be visible
        expect(page.locator("strong", has_text="Item licence")).to_be_visible()
        expect(page.locator("dt", has_text="Item ID")).not_to_be_visible()

        # change to another tab and expect its content to now be visible
        expect(page.locator("#item-tabs label[for='tab-info']")).to_be_visible()
        page.locator("#item-tabs label[for='tab-info']").click()
        expect(page.locator("dt", has_text="Item ID")).to_be_visible()
        expect(page.locator("strong", has_text="Item licence")).not_to_be_visible()
