import json
from datetime import date

from assets_tracking_service.lib.bas_data_catalogue.models.templates import PageMetadata


class TestPageMetadata:
    """Test page metadata dataclass."""

    def test_init(self):
        """Can create a PageMetadata instance with default values."""
        meta = PageMetadata()

        assert meta.html_title == " | BAS Data Catalogue"
        assert meta.html_open_graph == {}
        assert meta.html_schema_org is None
        assert meta.current_year == date.today().year  # noqa: DTZ011

    def test_populated(self):
        """Can create a PageMetadata instance with populated values."""
        expected_str = "x"
        expected_dict = {"x": "y"}
        expected_int = 666
        meta = PageMetadata(
            html_title=expected_str,
            html_open_graph=expected_dict,
            html_schema_org=json.dumps(expected_dict),
            current_year=expected_int,
        )

        assert meta.html_title == f"{expected_str} | BAS Data Catalogue"
        assert meta.html_open_graph == expected_dict
        assert json.loads(meta.html_schema_org) == expected_dict
        assert meta.current_year == expected_int
