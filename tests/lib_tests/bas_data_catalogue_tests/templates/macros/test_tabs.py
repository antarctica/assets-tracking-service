import json
from datetime import date

import pytest
from bs4 import BeautifulSoup

from assets_tracking_service.lib.bas_data_catalogue.models.item.catalogue import ItemCatalogue
from assets_tracking_service.lib.bas_data_catalogue.models.record import DataQuality, Distribution, ReferenceSystemInfo
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.common import (
    Address,
    Citation,
    Contact,
    ContactIdentity,
    Contacts,
    Date,
    Dates,
    Identifier,
    OnlineResource,
    Series,
)
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.data_quality import (
    DomainConsistency,
    Lineage,
)
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.distribution import (
    Format,
    Size,
    TransferOption,
)
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.identification import (
    Aggregation,
    Aggregations,
    BoundingBox,
    Constraint,
    Constraints,
    Extent,
    ExtentGeographic,
    Extents,
    ExtentTemporal,
    Maintenance,
    TemporalPeriod,
)
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.projection import Code
from assets_tracking_service.lib.bas_data_catalogue.models.record.enums import (
    AggregationAssociationCode,
    AggregationInitiativeCode,
    ConstraintRestrictionCode,
    ConstraintTypeCode,
    ContactRoleCode,
    MaintenanceFrequencyCode,
    OnlineResourceFunctionCode,
    ProgressCode,
)


class TestItemsTab:
    """Test items tab template macros."""

    @pytest.mark.parametrize(
        "value",
        [
            Aggregations([]),
            Aggregations(
                [
                    Aggregation(
                        identifier=Identifier(identifier="x", href="x", namespace="x"),
                        association_type=AggregationAssociationCode.IS_COMPOSED_OF,
                        initiative_type=AggregationInitiativeCode.COLLECTION,
                    )
                ]
            ),
        ],
    )
    def test_enabled(self, fx_lib_item_catalogue_min: ItemCatalogue, value: Aggregations):
        """Can get items tab if enabled in item."""
        fx_lib_item_catalogue_min._record.identification.aggregations = value
        expected = fx_lib_item_catalogue_min._items.enabled
        html = BeautifulSoup(fx_lib_item_catalogue_min.render(), parser="html.parser", features="lxml")

        if expected:
            assert html.select_one("#tab-content-items") is not None
        else:
            assert html.select_one("#tab-content-items") is None

    def test_items(self, fx_lib_item_catalogue_min: ItemCatalogue):
        """
        Can get item summaries with expected values from item.

        Detailed item summary tests are run in common macro tests.
        """
        items = Aggregations(
            [
                Aggregation(
                    identifier=Identifier(identifier="x", href="x", namespace="x"),
                    association_type=AggregationAssociationCode.IS_COMPOSED_OF,
                    initiative_type=AggregationInitiativeCode.COLLECTION,
                ),
                Aggregation(
                    identifier=Identifier(identifier="y", href="x", namespace="y"),
                    association_type=AggregationAssociationCode.IS_COMPOSED_OF,
                    initiative_type=AggregationInitiativeCode.COLLECTION,
                ),
            ]
        )
        fx_lib_item_catalogue_min._record.identification.aggregations = items
        expected = fx_lib_item_catalogue_min._items.items
        html = BeautifulSoup(fx_lib_item_catalogue_min.render(), parser="html.parser", features="lxml")

        for item in expected:
            assert html.select_one(f"a[href='{item.href}']") is not None


class TestDataTab:
    """Test data tab template macros."""

    @pytest.mark.parametrize(
        "value",
        [
            [],
            [
                Distribution(
                    distributor=Contact(organisation=ContactIdentity(name="x"), role=[ContactRoleCode.DISTRIBUTOR]),
                    transfer_option=TransferOption(
                        online_resource=OnlineResource(href="x", function=OnlineResourceFunctionCode.DOWNLOAD)
                    ),
                )
            ],
        ],
    )
    def test_enabled(self, fx_lib_item_catalogue_min: ItemCatalogue, value: list[Distribution]):
        """Can get data tab if enabled in item."""
        fx_lib_item_catalogue_min._record.distribution = value
        expected = fx_lib_item_catalogue_min._data.enabled
        html = BeautifulSoup(fx_lib_item_catalogue_min.render(), parser="html.parser", features="lxml")

        if expected:
            assert html.select_one("#tab-content-data") is not None
        else:
            assert html.select_one("#tab-content-data") is None

    def test_data_download(self, fx_lib_item_catalogue_min: ItemCatalogue):
        """Can get individual data elements for download distributions based on values from item."""
        fx_lib_item_catalogue_min._record.distribution = [
            Distribution(
                distributor=Contact(organisation=ContactIdentity(name="x"), role=[ContactRoleCode.DISTRIBUTOR]),
                format=Format(format="x", href="https://www.iana.org/assignments/media-types/image/png"),
                transfer_option=TransferOption(
                    size=Size(unit="bytes", magnitude=1024),
                    online_resource=OnlineResource(href="x", function=OnlineResourceFunctionCode.DOWNLOAD),
                ),
            )
        ]
        expected = fx_lib_item_catalogue_min._data.items[0]
        html = BeautifulSoup(fx_lib_item_catalogue_min.render(), parser="html.parser", features="lxml")

        assert html.select_one(f"a[href='{expected.action.href}']") is not None
        assert html.find(name="div", string=expected.format_type.value) is not None
        assert html.find(name="div", string=expected.size) is not None

    @pytest.mark.parametrize(
        ("value", "text"),
        [
            (
                [
                    "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+feature",
                    "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+feature",
                ],
                "ArcGIS Feature Services",
            ),
            (
                [
                    "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+feature+ogc",
                    "https://metadata-resources.data.bas.ac.uk/media-types/x-service/ogc+api+feature",
                ],
                "This service is implemented using ArcGIS Server.",
            ),
            (
                ["https://www.bas.ac.uk/data/our-data/maps/how-to-order-a-map/"],
                "This item is currently only available to purchase as a physical paper map",
            ),
            (
                [
                    "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+tile+vector",
                    "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+tile+vector",
                ],
                "ArcGIS Vector Tiles",
            ),
        ],
    )
    def test_data_access(self, fx_lib_item_catalogue_min: ItemCatalogue, value: list[str], text: str):
        """
        Can get matching data access template based on values from item.

        Checking these templates is tricky:
        - templates vary significantly and don't contain any single common/predictable value to check against
        - templates do not contain a value we can use as a boundary to search within
        - templates could repeat if multiple distribution options of the same type are defined

        This test is therefore a best efforts attempt, checking for a freetext value. anywhere in the item template.
        Using a single distribution option set, with an otherwise minimal item, can hopefully limit irrelevant content.

        Note: This test does not check the contents of the rendered template, except for the freetext value. For
        example it does not verify a service endpoint (if used) is populated correctly.
        """
        for href in value:
            fx_lib_item_catalogue_min._record.distribution.append(
                Distribution(
                    distributor=Contact(organisation=ContactIdentity(name="x"), role=[ContactRoleCode.DISTRIBUTOR]),
                    format=Format(format="x", href=href),
                    transfer_option=TransferOption(
                        online_resource=OnlineResource(href=href, function=OnlineResourceFunctionCode.DOWNLOAD)
                    ),
                )
            )
        expected = fx_lib_item_catalogue_min._data.items[0]
        html = BeautifulSoup(fx_lib_item_catalogue_min.render(), parser="html.parser", features="lxml")

        assert html.select_one(f"button[data-target='{expected.access_target}']") is not None
        assert html.find(name="div", string=expected.format_type.value) is not None
        assert str(html).count(text) == 1


class TestAuthorsTab:
    """Test authors tab template macros."""

    base_contact = Contact(organisation=ContactIdentity(name="x"), email="x", role=[ContactRoleCode.POINT_OF_CONTACT])

    @pytest.mark.parametrize(
        "value",
        [
            Contacts([base_contact]),
            Contacts(
                [
                    base_contact,
                    Contact(organisation=ContactIdentity(name="x"), role=[ContactRoleCode.AUTHOR]),
                ]
            ),
        ],
    )
    def test_enabled(self, fx_lib_item_catalogue_min: ItemCatalogue, value: Contacts):
        """
        Can get items tab if enabled in item.

        Point of Contact role always required.
        """
        fx_lib_item_catalogue_min._record.identification.contacts = value
        expected = fx_lib_item_catalogue_min._authors.enabled
        html = BeautifulSoup(fx_lib_item_catalogue_min.render(), parser="html.parser", features="lxml")

        if expected:
            assert html.select_one("#tab-content-authors") is not None
        else:
            assert html.select_one("#tab-content-authors") is None

    def test_authors(self, fx_lib_item_catalogue_min: ItemCatalogue):
        """
        Can get item authors with expected values from item.

        Basic count test. Subsequent tests check for author item elements.
        """
        items = Contacts(
            [
                self.base_contact,
                Contact(organisation=ContactIdentity(name="x"), role=[ContactRoleCode.AUTHOR]),
                Contact(organisation=ContactIdentity(name="y"), role=[ContactRoleCode.AUTHOR]),
            ]
        )
        fx_lib_item_catalogue_min._record.identification.contacts = items
        expected = fx_lib_item_catalogue_min._authors.items
        html = BeautifulSoup(fx_lib_item_catalogue_min.render(), parser="html.parser", features="lxml")

        for item in expected:
            assert html.find("div", string=item.organisation.name) is not None

    @pytest.mark.parametrize(
        "value",
        [
            Contact(organisation=ContactIdentity(name="x"), role=[ContactRoleCode.AUTHOR]),
            Contact(individual=ContactIdentity(name="x"), role=[ContactRoleCode.AUTHOR]),
            Contact(
                individual=ContactIdentity(name="x"),
                organisation=ContactIdentity(name="y"),
                role=[ContactRoleCode.AUTHOR],
            ),
            Contact(individual=ContactIdentity(name="x"), email="x", role=[ContactRoleCode.AUTHOR]),
            Contact(individual=ContactIdentity(name="x", href="x"), role=[ContactRoleCode.AUTHOR]),
        ],
    )
    def test_author(self, fx_lib_item_catalogue_min: ItemCatalogue, value: Contact):
        """Can get individual author elements based on values from item."""
        items = Contacts([self.base_contact, value])
        fx_lib_item_catalogue_min._record.identification.contacts = items
        expected = fx_lib_item_catalogue_min._authors.items[0]
        html = BeautifulSoup(fx_lib_item_catalogue_min.render(), parser="html.parser", features="lxml")

        if expected.organisation is not None:
            assert html.find("div", string=expected.organisation.name) is not None
        if expected.individual is not None:
            assert html.find("div", string=expected.individual.name) is not None
        if expected.email is not None:
            assert html.find("a", href=f"mailto:{expected.email}") is not None
        if expected.orcid is not None:
            assert html.find("a", href=expected.orcid) is not None


class TestLicenceTab:
    """Test licence tab template macros."""

    @pytest.mark.parametrize(
        "value",
        [
            Constraints([]),
            Constraints(
                [
                    Constraint(
                        type=ConstraintTypeCode.USAGE,
                        restriction_code=ConstraintRestrictionCode.LICENSE,
                        href="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
                    )
                ]
            ),
        ],
    )
    def test_enabled(self, fx_lib_item_catalogue_min: ItemCatalogue, value: Constraints):
        """Can get licence tab if enabled in item."""
        fx_lib_item_catalogue_min._record.identification.constraints = value
        expected = fx_lib_item_catalogue_min._licence.enabled
        html = BeautifulSoup(fx_lib_item_catalogue_min.render(), parser="html.parser", features="lxml")

        if expected:
            assert html.select_one("#tab-content-licence") is not None
        else:
            assert html.select_one("#tab-content-licence") is None

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (
                "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
                "Open Government Licence (OGL 3.0)",
            ),
            (
                "https://creativecommons.org/licenses/by/4.0/",
                "Creative Commons Attribution 4.0 International Licence (CC BY 4.0)",
            ),
            (
                "https://metadata-resources.data.bas.ac.uk/licences/all-rights-reserved-v1/",
                "BAS All Rights Reserved Licence (v1)",
            ),
            (
                "https://metadata-resources.data.bas.ac.uk/licences/operations-mapping-v1/",
                "BAS Operations Mapping Internal Use Licence (v1)",
            ),
        ],
    )
    def test_licence(self, fx_lib_item_catalogue_min: ItemCatalogue, value: str, expected: str):
        """Can get matching licence template based on value from item."""
        fx_lib_item_catalogue_min._record.identification.constraints = Constraints(
            [Constraint(type=ConstraintTypeCode.USAGE, restriction_code=ConstraintRestrictionCode.LICENSE, href=value)]
        )
        html = BeautifulSoup(fx_lib_item_catalogue_min.render(), parser="html.parser", features="lxml")

        assert html.find(name="strong", string="Item licence") is not None

        licence = html.select_one(f"a[href='{value}']")
        assert licence is not None
        assert licence.text.strip() == expected


class TestExtentTab:
    """Test extent tab template macros."""

    @pytest.mark.parametrize(
        "value",
        [
            Extents([]),
            Extents(
                [
                    Extent(
                        identifier="bounding",
                        geographic=ExtentGeographic(
                            bounding_box=BoundingBox(
                                west_longitude=1.0, east_longitude=1.0, south_latitude=1.0, north_latitude=1.0
                            )
                        ),
                    ),
                ]
            ),
        ],
    )
    def test_enabled(self, fx_lib_item_catalogue_min: ItemCatalogue, value: Extents):
        """Can get data tab if enabled in item."""
        fx_lib_item_catalogue_min._record.identification.extents = value
        expected = fx_lib_item_catalogue_min._extent.enabled
        html = BeautifulSoup(fx_lib_item_catalogue_min.render(), parser="html.parser", features="lxml")

        if expected:
            assert html.select_one("#tab-content-extent") is not None
        else:
            assert html.select_one("#tab-content-extent") is None

    @pytest.mark.parametrize(
        "value",
        [
            Extent(
                identifier="bounding",
                geographic=ExtentGeographic(
                    bounding_box=BoundingBox(
                        west_longitude=1.0, east_longitude=1.0, south_latitude=1.0, north_latitude=1.0
                    )
                ),
            ),
            Extent(
                identifier="bounding",
                geographic=ExtentGeographic(
                    bounding_box=BoundingBox(
                        west_longitude=1.0, east_longitude=1.0, south_latitude=1.0, north_latitude=1.0
                    )
                ),
                temporal=ExtentTemporal(period=TemporalPeriod(start=Date(date=date(2023, 10, 31)))),
            ),
            Extent(
                identifier="bounding",
                geographic=ExtentGeographic(
                    bounding_box=BoundingBox(
                        west_longitude=1.0, east_longitude=1.0, south_latitude=1.0, north_latitude=1.0
                    )
                ),
                temporal=ExtentTemporal(period=TemporalPeriod(end=Date(date=date(2023, 10, 31)))),
            ),
            Extent(
                identifier="bounding",
                geographic=ExtentGeographic(
                    bounding_box=BoundingBox(
                        west_longitude=1.0, east_longitude=1.0, south_latitude=1.0, north_latitude=1.0
                    )
                ),
                temporal=ExtentTemporal(
                    period=TemporalPeriod(start=Date(date=date(2023, 10, 31)), end=Date(date=date(2023, 11, 1)))
                ),
            ),
        ],
    )
    def test_extent(self, fx_lib_item_catalogue_min: ItemCatalogue, value: Extent):
        """Can get individual extent elements based on values from item."""
        fx_lib_item_catalogue_min._record.identification.extents = Extents([value])
        expected = fx_lib_item_catalogue_min._extent
        html = BeautifulSoup(fx_lib_item_catalogue_min.render(), parser="html.parser", features="lxml")
        bbox = expected.bounding_box
        bbox_min = f"South: {bbox[1]}, West: {bbox[0]}"
        bbox_max = f"North: {bbox[3]}, East: {bbox[2]}"

        assert html.select_one(f"iframe[src='{expected.map_iframe}']") is not None
        assert html.select_one("#bbox-min").text.strip() == bbox_min
        assert html.select_one("#bbox-max").text.strip() == bbox_max

        if expected.start:
            assert html.select_one("#period-start").text.strip() == expected.start.value
            assert html.select_one("#period-start")["datetime"] == expected.start.datetime
        else:
            assert html.select_one("#period-start") is None

        if expected.end:
            assert html.select_one("#period-end").text.strip() == expected.end.value
            assert html.select_one("#period-end")["datetime"] == expected.end.datetime
        else:
            assert html.select_one("#period-end") is None


class TestLineageTab:
    """Test lineage tab template macros."""

    @pytest.mark.parametrize("value", [None, "x"])
    def test_enabled(self, fx_lib_item_catalogue_min: ItemCatalogue, value: str | None):
        """Can get lineage tab if enabled in item."""
        fx_lib_item_catalogue_min._record.data_quality = DataQuality(lineage=Lineage(statement=value))
        expected = fx_lib_item_catalogue_min._lineage.enabled
        html = BeautifulSoup(fx_lib_item_catalogue_min.render(), parser="html.parser", features="lxml")

        if expected:
            assert html.select_one("#tab-content-lineage") is not None
        else:
            assert html.select_one("#tab-content-lineage") is None

    @pytest.mark.parametrize("value", [None, "x"])
    def test_collections(self, fx_lib_item_catalogue_min: ItemCatalogue, value: str | None):
        """Can get optional lineage statement with expected values from item."""
        fx_lib_item_catalogue_min._record.data_quality = DataQuality(lineage=Lineage(statement=value))
        expected = fx_lib_item_catalogue_min._lineage.statement
        html = BeautifulSoup(fx_lib_item_catalogue_min.render(), parser="html.parser", features="lxml")

        if fx_lib_item_catalogue_min._lineage.enabled:
            assert expected in str(html.select_one("#lineage-statement"))


class TestRelatedTab:
    """Test related tab template macros."""

    @pytest.mark.parametrize(
        "value",
        [
            Aggregations([]),
            Aggregations(
                [
                    Aggregation(
                        identifier=Identifier(identifier="x", href="x", namespace="x"),
                        association_type=AggregationAssociationCode.CROSS_REFERENCE,
                        initiative_type=AggregationInitiativeCode.COLLECTION,
                    ),
                    Aggregation(
                        identifier=Identifier(identifier="y", href="y", namespace="y"),
                        association_type=AggregationAssociationCode.CROSS_REFERENCE,
                        initiative_type=AggregationInitiativeCode.COLLECTION,
                    ),
                ]
            ),
        ],
    )
    def test_peer_collections(self, fx_lib_item_catalogue_min: ItemCatalogue, value: Aggregations):
        """
        Can get optional peer collections with expected values from item.

        Detailed item summary tests are run in common macro tests.
        """
        fx_lib_item_catalogue_min._record.identification.aggregations = value
        expected = fx_lib_item_catalogue_min._related.peer_collections
        html = BeautifulSoup(fx_lib_item_catalogue_min.render(), parser="html.parser", features="lxml")

        collections = html.select_one("#related-peer-collections")
        if len(expected) > 0:
            for item in expected:
                assert collections.select_one(f"a[href='{item.href}']") is not None
        else:
            assert collections is None

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
        ],
    )
    def test_enabled(self, fx_lib_item_catalogue_min: ItemCatalogue, value: Aggregations):
        """Can get related tab if enabled in item."""
        fx_lib_item_catalogue_min._record.identification.aggregations = value
        expected = fx_lib_item_catalogue_min._related.enabled
        html = BeautifulSoup(fx_lib_item_catalogue_min.render(), parser="html.parser", features="lxml")

        if expected:
            assert html.select_one("#tab-content-related") is not None
        else:
            assert html.select_one("#tab-content-related") is None

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
                    ),
                    Aggregation(
                        identifier=Identifier(identifier="y", href="y", namespace="y"),
                        association_type=AggregationAssociationCode.LARGER_WORK_CITATION,
                        initiative_type=AggregationInitiativeCode.COLLECTION,
                    ),
                ]
            ),
        ],
    )
    def test_parent_collections(self, fx_lib_item_catalogue_min: ItemCatalogue, value: Aggregations):
        """
        Can get optional parent collections with expected values from item.

        Detailed item summary tests are run in common macro tests.
        """
        fx_lib_item_catalogue_min._record.identification.aggregations = value
        expected = fx_lib_item_catalogue_min._related.parent_collections
        html = BeautifulSoup(fx_lib_item_catalogue_min.render(), parser="html.parser", features="lxml")

        collections = html.select_one("#related-parent-collections")
        if len(expected) > 0:
            for item in expected:
                assert collections.select_one(f"a[href='{item.href}']") is not None
        else:
            assert collections is None


class TestInfoTab:
    """Test additional information tab template macros."""

    def test_enabled(self, fx_lib_item_catalogue_min: ItemCatalogue):
        """Can get additional information tab (always enabled)."""
        html = BeautifulSoup(fx_lib_item_catalogue_min.render(), parser="html.parser", features="lxml")

        assert html.select_one("#tab-content-info") is not None

    def test_id(self, fx_lib_item_catalogue_min: ItemCatalogue):
        """Can get item id based on value from item."""
        expected = fx_lib_item_catalogue_min._additional_info.item_id
        html = BeautifulSoup(fx_lib_item_catalogue_min.render(), parser="html.parser", features="lxml")

        assert html.select_one("#info-id").text.strip() == expected

    def test_type(self, fx_lib_item_catalogue_min: ItemCatalogue):
        """Can get item type based on value from item."""
        expected = fx_lib_item_catalogue_min._additional_info
        html = BeautifulSoup(fx_lib_item_catalogue_min.render(), parser="html.parser", features="lxml")

        assert html.select_one("#info-type i")["class"] == expected.item_type_icon.split(" ")
        assert html.select_one("#info-type").text.strip().lower() == expected.item_type

    @pytest.mark.parametrize("value", [Series, Series(name="x", edition="x")])
    def test_series(self, fx_lib_item_catalogue_min: ItemCatalogue, value: Series):
        """Can get optional item series based on value from item."""
        fx_lib_item_catalogue_min._record.identification.series = value
        expected = fx_lib_item_catalogue_min._additional_info.series
        html = BeautifulSoup(fx_lib_item_catalogue_min.render(), parser="html.parser", features="lxml")

        series = html.select_one("#info-series")
        if expected:
            assert series.text.strip() == expected
        else:
            assert series is None

    @pytest.mark.parametrize("value", [None, 1.0])
    def test_scale(self, fx_lib_item_catalogue_min: ItemCatalogue, value: float | None):
        """Can get optional item scale based on value from item."""
        fx_lib_item_catalogue_min._record.identification.scale = value
        expected = fx_lib_item_catalogue_min._additional_info.scale
        html = BeautifulSoup(fx_lib_item_catalogue_min.render(), parser="html.parser", features="lxml")

        scale = html.select_one("#info-scale")
        if expected:
            assert scale.text.strip() == expected
        else:
            assert scale is None

    @pytest.mark.parametrize("value", [None, ReferenceSystemInfo(code=Code(value="x"))])
    def test_projection(self, fx_lib_item_catalogue_min: ItemCatalogue, value: ReferenceSystemInfo):
        """Can get optional item projection based on value from item."""
        fx_lib_item_catalogue_min._record.reference_system_info = value
        expected = fx_lib_item_catalogue_min._additional_info.projection
        html = BeautifulSoup(fx_lib_item_catalogue_min.render(), parser="html.parser", features="lxml")

        projection = html.select_one("#info-projection")
        if expected:
            assert projection.text.strip() == expected.value
            assert projection["href"] == expected.href
        else:
            assert projection is None

    @pytest.mark.parametrize(
        "value",
        [
            None,
            json.dumps({"width": 1, "height": 1}),
            json.dumps({"width": 210, "height": 297}),
            json.dumps({"width": 297, "height": 210}),
        ],
    )
    def test_size(self, fx_lib_item_catalogue_min: ItemCatalogue, value: str | None):
        """Can get optional item physical page size based on value from item."""
        fx_lib_item_catalogue_min._record.identification.supplemental_information = value
        expected = fx_lib_item_catalogue_min._additional_info.page_size
        html = BeautifulSoup(fx_lib_item_catalogue_min.render(), parser="html.parser", features="lxml")

        size = html.select_one("#info-page-size")
        if expected:
            assert size.text.strip() == expected
        else:
            assert size is None
        if expected is not None and "portrait" in expected.lower():
            assert size.select_one("i.fa-rectangle-portrait") is not None
        if expected is not None and "landscape" in expected.lower():
            assert size.select_one("i.fa-rectangle-landscape") is not None

    @pytest.mark.parametrize(
        "value",
        [
            [],
            [
                Identifier(identifier="x", href="x", namespace="doi"),
                Identifier(identifier="y", href="y", namespace="doi"),
            ],
        ],
    )
    def test_doi(self, fx_lib_item_catalogue_min: ItemCatalogue, value: list[Identifier]):
        """Can get optional item DOIs based on value from item."""
        fx_lib_item_catalogue_min._record.identification.identifiers.extend(value)
        expected = fx_lib_item_catalogue_min._additional_info.doi
        html = BeautifulSoup(fx_lib_item_catalogue_min.render(), parser="html.parser", features="lxml")

        doi = html.select_one("#info-doi")
        if expected:
            for item in expected:
                assert doi.select_one(f"a[href='{item.href}']") is not None
        else:
            assert doi is None

    @pytest.mark.parametrize(
        "value",
        [
            [],
            [
                Identifier(identifier="x", href="x", namespace="isbn"),
                Identifier(identifier="y", href="y", namespace="isbn"),
            ],
        ],
    )
    def test_isbn(self, fx_lib_item_catalogue_min: ItemCatalogue, value: list[Identifier]):
        """Can get optional item ISBNs based on value from item."""
        fx_lib_item_catalogue_min._record.identification.identifiers.extend(value)
        expected = fx_lib_item_catalogue_min._additional_info.isbn
        html = BeautifulSoup(fx_lib_item_catalogue_min.render(), parser="html.parser", features="lxml")

        isbn = html.select_one("#info-isbn")
        if expected:
            for item in expected:
                assert isbn.find(name="li", string=item) is not None
        else:
            assert isbn is None

    @pytest.mark.parametrize(
        "value",
        [
            [],
            [
                Identifier(
                    identifier="x",
                    href="https://gitlab.data.bas.ac.uk/MAGIC/x/-/issues/123",
                    namespace="gitlab.data.bas.ac.uk",
                ),
                Identifier(
                    identifier="y",
                    href="https://gitlab.data.bas.ac.uk/MAGIC/x/-/issues/234",
                    namespace="gitlab.data.bas.ac.uk",
                ),
            ],
        ],
    )
    def test_issues(self, fx_lib_item_catalogue_min: ItemCatalogue, value: list[Identifier]):
        """Can get optional item GitLab issues based on value from item."""
        fx_lib_item_catalogue_min._record.identification.identifiers.extend(value)
        expected = fx_lib_item_catalogue_min._additional_info.gitlab_issues
        html = BeautifulSoup(fx_lib_item_catalogue_min.render(), parser="html.parser", features="lxml")

        issues = html.select_one("#info-issues")
        if expected:
            for item in expected:
                assert issues.find(name="li", string=item) is not None
        else:
            assert issues is None

    def test_dates(self, fx_lib_item_catalogue_min: ItemCatalogue):
        """Can get item dates based on values from item."""
        expected = fx_lib_item_catalogue_min._additional_info.dates
        html = BeautifulSoup(fx_lib_item_catalogue_min.render(), parser="html.parser", features="lxml")

        for label, item in expected.items():
            element = html.select_one(f"#info-{label.lower().replace(' ', '-')}")
            assert element.text.strip() == item.value
            assert element["datetime"] == item.datetime

    @pytest.mark.parametrize(
        "value",
        [Maintenance(), Maintenance(progress=ProgressCode.COMPLETED)],
    )
    def test_status(self, fx_lib_item_catalogue_min: ItemCatalogue, value: Maintenance):
        """Can get optional item status info based on value from item."""
        fx_lib_item_catalogue_min._record.identification.maintenance = value
        expected = fx_lib_item_catalogue_min._additional_info.status
        html = BeautifulSoup(fx_lib_item_catalogue_min.render(), parser="html.parser", features="lxml")

        status = html.select_one("#info-status")
        if expected:
            assert status.text.strip() == expected
        else:
            assert status is None

    @pytest.mark.parametrize(
        "value",
        [Maintenance(), Maintenance(maintenance_frequency=MaintenanceFrequencyCode.AS_NEEDED)],
    )
    def test_frequency(self, fx_lib_item_catalogue_min: ItemCatalogue, value: Maintenance):
        """Can get optional item update frequency info based on value from item."""
        fx_lib_item_catalogue_min._record.identification.maintenance = value
        expected = fx_lib_item_catalogue_min._additional_info.frequency
        html = BeautifulSoup(fx_lib_item_catalogue_min.render(), parser="html.parser", features="lxml")

        frequency = html.select_one("#info-frequency")
        if expected:
            assert frequency.text.strip() == expected
        else:
            assert frequency is None

    def test_datestamp(self, fx_lib_item_catalogue_min: ItemCatalogue):
        """Can get metadata datestamp based on value from item."""
        expected = fx_lib_item_catalogue_min._additional_info.datestamp
        html = BeautifulSoup(fx_lib_item_catalogue_min.render(), parser="html.parser", features="lxml")

        assert html.select_one("#info-datestamp").text.strip() == expected.value
        assert html.select_one("#info-datestamp")["datetime"] == expected.datetime

    def test_standard(self, fx_lib_item_catalogue_min: ItemCatalogue):
        """Can get metadata standard and version based on value from item."""
        expected = fx_lib_item_catalogue_min._additional_info
        html = BeautifulSoup(fx_lib_item_catalogue_min.render(), parser="html.parser", features="lxml")

        assert html.select_one("#info-standard").text.strip() == expected.standard
        assert html.select_one("#info-standard-version").text.strip() == expected.standard_version

    @pytest.mark.parametrize(
        "value",
        [
            [],
            [
                DomainConsistency(
                    specification=Citation(title="x", href="x", dates=Dates(publication=Date(date=date(2010, 10, 31)))),
                    explanation="x",
                    result=True,
                )
            ],
        ],
    )
    def test_profiles(self, fx_lib_item_catalogue_min: ItemCatalogue, value: list[DomainConsistency]):
        """Can get metadata profiles based on values from item."""
        fx_lib_item_catalogue_min._record.data_quality = DataQuality(domain_consistency=value)
        expected = fx_lib_item_catalogue_min._additional_info.profiles
        html = BeautifulSoup(fx_lib_item_catalogue_min.render(), parser="html.parser", features="lxml")

        profiles = html.select_one("#info-profiles")
        if len(expected) > 0:
            for item in expected:
                assert profiles.select_one(f"a[href='{item.href}']") is not None
        else:
            assert profiles is None

    def test_record_links(self, fx_lib_item_catalogue_min: ItemCatalogue):
        """Can get metadata record links based on values from item."""
        expected = fx_lib_item_catalogue_min._additional_info.record_links
        html = BeautifulSoup(fx_lib_item_catalogue_min.render(), parser="html.parser", features="lxml")

        links = html.select_one("#info-records")
        if len(expected) > 0:
            for item in expected:
                assert links.select_one(f"a[href='{item.href}']") is not None
        else:
            assert links is None


class TestContactTab:
    """Test contact tab template macros."""

    def test_enabled(self, fx_lib_item_catalogue_min: ItemCatalogue):
        """Can get contact tab (always enabled)."""
        html = BeautifulSoup(fx_lib_item_catalogue_min.render(), parser="html.parser", features="lxml")

        assert html.select_one("#tab-content-contact") is not None

    def test_subject(self, fx_lib_item_catalogue_min: ItemCatalogue):
        """Can get contact form subject with expected value from item."""
        expected = fx_lib_item_catalogue_min._contact.subject_default
        html = BeautifulSoup(fx_lib_item_catalogue_min.render(), parser="html.parser", features="lxml")

        assert html.select_one("#message-subject")["value"] == expected

    @pytest.mark.parametrize(
        "value",
        [
            Contact(organisation=ContactIdentity(name="x"), email="x", role=[ContactRoleCode.POINT_OF_CONTACT]),
            Contact(
                organisation=ContactIdentity(name="x"), phone="x", email="x", role=[ContactRoleCode.POINT_OF_CONTACT]
            ),
            Contact(
                organisation=ContactIdentity(name="x"),
                address=Address(delivery_point="x"),
                email="x",
                role=[ContactRoleCode.POINT_OF_CONTACT],
            ),
        ],
    )
    def test_alternate(self, fx_lib_item_catalogue_min: ItemCatalogue, value: Contact):
        """
        Can get optional alternate contact information based on, and with, values from item.

        Email is always expected as the ItemCatalogue class requires it.
        """
        fx_lib_item_catalogue_min._record.identification.contacts = Contacts([value])
        expected = fx_lib_item_catalogue_min._contact
        html = BeautifulSoup(fx_lib_item_catalogue_min.render(), parser="html.parser", features="lxml")

        assert html.select_one("#contact-email").text == expected.email

        phone = html.select_one("#contact-phone")
        if expected.phone:
            assert phone.text == expected.phone
        else:
            assert phone is None

        post = html.select_one("#contact-post")
        if expected.address:
            assert post.text == expected.address
        else:
            assert post is None
