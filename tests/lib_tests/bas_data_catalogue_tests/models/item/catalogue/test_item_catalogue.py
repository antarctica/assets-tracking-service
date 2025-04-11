from datetime import UTC, datetime

import pytest

from assets_tracking_service.lib.bas_data_catalogue.models.item.catalogue import ItemCatalogue
from assets_tracking_service.lib.bas_data_catalogue.models.item.catalogue.elements import (
    Summary,
)
from assets_tracking_service.lib.bas_data_catalogue.models.item.catalogue.tabs import (
    AdditionalInfoTab,
    AuthorsTab,
    ContactTab,
    DataTab,
    ExtentTab,
    ItemsTab,
    LicenceTab,
    LineageTab,
    RelatedTab,
)
from assets_tracking_service.lib.bas_data_catalogue.models.record import Record
from tests.conftest import _lib_get_record_summary


class TestItemCatalogue:
    """Test catalogue item."""

    def test_init(self, fx_lib_record_minimal_item: Record):
        """Can create an ItemCatalogue."""
        item = ItemCatalogue(
            fx_lib_record_minimal_item,
            embedded_maps_endpoint="x",
            item_contact_endpoint="x",
            sentry_dsn="x",
            get_record_summary=_lib_get_record_summary,
        )

        assert isinstance(item, ItemCatalogue)
        assert item._record == fx_lib_record_minimal_item

    def test_sentry_dsn(self, fx_lib_item_catalogue: ItemCatalogue):
        """Can get Sentry DSN."""
        expected = "x"
        fx_lib_item_catalogue._sentry_dsn = expected

        assert fx_lib_item_catalogue.sentry_dsn == expected

    def test_html_title(self, fx_lib_item_catalogue: ItemCatalogue):
        """Can get HTML title."""
        expected = "x | BAS Data Catalogue"
        fx_lib_item_catalogue._record.identification.title = "_x_"

        assert fx_lib_item_catalogue.html_title == expected

    def test_page_header(self, fx_lib_item_catalogue: ItemCatalogue):
        """Can get page header element."""
        expected = "<em>x</em>"
        fx_lib_item_catalogue._record.identification.title = "_x_"

        assert fx_lib_item_catalogue.page_header.title == expected
        assert fx_lib_item_catalogue.page_header.subtitle[0] == fx_lib_item_catalogue._record.hierarchy_level.value

    def test_summary(self, fx_lib_item_catalogue: ItemCatalogue):
        """
        Can get summary element.

        Summary element is checked in more detail in catalogue element tests.
        """
        assert isinstance(fx_lib_item_catalogue.summary, Summary)

    def test_graphics(self, fx_lib_item_catalogue: ItemCatalogue):
        """Can get list of graphics."""
        assert isinstance(fx_lib_item_catalogue.graphics, list)

    def test_noscript_href(self, fx_lib_item_catalogue: ItemCatalogue):
        """
        Can get link for use in noscript element.

        Not a great test but this is effectively static content.
        """
        assert fx_lib_item_catalogue.noscript_href is not None

    def test_tabs(self, fx_lib_item_catalogue: ItemCatalogue):
        """Can get list of tabs."""
        assert isinstance(fx_lib_item_catalogue.tabs[0], ItemsTab)
        assert isinstance(fx_lib_item_catalogue.tabs[1], DataTab)
        assert isinstance(fx_lib_item_catalogue.tabs[2], AuthorsTab)
        assert isinstance(fx_lib_item_catalogue.tabs[3], LicenceTab)
        assert isinstance(fx_lib_item_catalogue.tabs[4], ExtentTab)
        assert isinstance(fx_lib_item_catalogue.tabs[5], LineageTab)
        assert isinstance(fx_lib_item_catalogue.tabs[6], RelatedTab)
        assert isinstance(fx_lib_item_catalogue.tabs[7], AdditionalInfoTab)
        assert isinstance(fx_lib_item_catalogue.tabs[8], ContactTab)

    base_record = {  # noqa: RUF012
        "$schema": "https://metadata-resources.data.bas.ac.uk/bas-metadata-generator-configuration-schemas/v2/iso-19115-2-v4.json",
        "file_identifier": "x",
        "hierarchy_level": "dataset",
        "metadata": {
            "contacts": [{"organisation": {"name": "x"}, "role": ["pointOfContact"]}],
            "date_stamp": datetime(2014, 6, 30, tzinfo=UTC).date().isoformat(),
        },
        "identification": {
            "title": {"value": "x"},
            "dates": {"creation": "2014-06-30"},
            "abstract": "x",
        },
    }

    @pytest.mark.parametrize(
        ("values", "anchor"),
        [
            (
                {
                    **base_record,
                    "identification": {
                        **base_record["identification"],
                        "aggregations": [
                            {
                                "identifier": {"identifier": "x", "href": "x", "namespace": "x"},
                                "association_type": "isComposedOf",
                                "initiative_type": "collection",
                            }
                        ],
                    },
                },
                "items",
            ),
            (
                {
                    **base_record,
                    "distribution": [
                        {
                            "distributor": {"organisation": {"name": "x"}, "role": ["distributor"]},
                            "format": {
                                "format": "x",
                                "href": "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+feature",
                            },
                            "transfer_option": {
                                "online_resource": {"href": "x", "function": "download"},
                            },
                        },
                        {
                            "distributor": {"organisation": {"name": "x"}, "role": ["distributor"]},
                            "format": {
                                "format": "x",
                                "href": "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+feature",
                            },
                            "transfer_option": {
                                "online_resource": {"href": "x", "function": "download"},
                            },
                        },
                    ],
                },
                "data",
            ),
            (
                {
                    **base_record,
                    "identification": {
                        **base_record["identification"],
                        "contacts": [{"individual": {"name": "x"}, "role": ["author"]}],
                    },
                },
                "authors",
            ),
            (
                {
                    **base_record,
                    "identification": {
                        **base_record["identification"],
                        "constraints": [
                            {"type": "usage", "restriction_code": "license", "statement": "x", "href": "x"}
                        ],
                    },
                },
                "licence",
            ),
            (
                {
                    **base_record,
                    "identification": {
                        **base_record["identification"],
                        "extents": [
                            {
                                "identifier": "bounding",
                                "geographic": {
                                    "bounding_box": {
                                        "west_longitude": 1.0,
                                        "east_longitude": 1.0,
                                        "south_latitude": 1.0,
                                        "north_latitude": 1.0,
                                    }
                                },
                            }
                        ],
                    },
                },
                "extent",
            ),
            (
                {
                    **base_record,
                    "identification": {
                        **base_record["identification"],
                        "lineage": {"statement": "x"},
                    },
                },
                "lineage",
            ),
            (
                {
                    **base_record,
                    "identification": {
                        **base_record["identification"],
                        "aggregations": [
                            {
                                "identifier": {"identifier": "x", "href": "x", "namespace": "x"},
                                "association_type": "largerWorkCitation",
                                "initiative_type": "collection",
                            }
                        ],
                    },
                },
                "related",
            ),
            (
                base_record,
                "info",
            ),
        ],
    )
    def test_default_tab_anchor(self, fx_lib_item_catalogue: ItemCatalogue, values: dict, anchor: str):
        """Can get default tab anchor depending on enabled tabs."""
        record = Record.loads(values)
        fx_lib_item_catalogue._record = record

        assert fx_lib_item_catalogue.default_tab_anchor == anchor

    def test_render(self, fx_lib_item_catalogue: ItemCatalogue):
        """
        Can render template for item.

        This is a basic sanity check that the template can be rendered without error.
        It does not check the content of the rendered template in any detail.
        """
        assert fx_lib_item_catalogue.render() != ""
