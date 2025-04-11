from datetime import UTC, datetime

import pytest

from assets_tracking_service.lib.bas_data_catalogue.models.item.base.elements import Contact, Contacts
from assets_tracking_service.lib.bas_data_catalogue.models.item.base.elements import Extent as ItemExtent
from assets_tracking_service.lib.bas_data_catalogue.models.item.catalogue import ItemCatalogue
from assets_tracking_service.lib.bas_data_catalogue.models.item.catalogue.distributions import ArcGisFeatureLayer
from assets_tracking_service.lib.bas_data_catalogue.models.item.catalogue.elements import (
    Aggregations,
    Dates,
    Extent,
    format_date,
)
from assets_tracking_service.lib.bas_data_catalogue.models.item.catalogue.tabs import (
    AdditionalInfoTab,
    AuthorsTab,
    ContactTab,
    DataTab,
    ExtentTab,
    InvalidItemContactError,
    ItemsTab,
    LicenceTab,
    LineageTab,
    RelatedTab,
)
from assets_tracking_service.lib.bas_data_catalogue.models.record import Distribution as RecordDistribution
from assets_tracking_service.lib.bas_data_catalogue.models.record import HierarchyLevelCode
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.common import (
    Address,
    ContactIdentity,
    Date,
    Identifier,
    OnlineResource,
)
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.common import Contact as RecordContact
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.common import Dates as RecordDates
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.distribution import Format, TransferOption
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.identification import (
    Aggregation,
    BoundingBox,
    Constraint,
    ExtentGeographic,
)
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.identification import (
    Aggregations as RecordAggregations,
)
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.identification import Extent as RecordExtent
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.metadata import MetadataStandard
from assets_tracking_service.lib.bas_data_catalogue.models.record.enums import (
    AggregationAssociationCode,
    AggregationInitiativeCode,
    ConstraintRestrictionCode,
    ConstraintTypeCode,
    ContactRoleCode,
    OnlineResourceFunctionCode,
)
from tests.conftest import _lib_get_record_summary


class TestItemsTab:
    """Test items tab."""

    def test_init(self):
        """Can create items tab."""
        aggregations = Aggregations(
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
        )

        tab = ItemsTab(aggregations=aggregations)

        assert tab.enabled is True
        assert len(tab.items) == 1
        # cov
        assert tab.title != ""
        assert tab.icon != ""


class TestDataTab:
    """Test data tab."""

    def test_init(self):
        """Can create data tab."""
        distributions = [
            RecordDistribution(
                distributor=RecordContact(organisation=ContactIdentity(name="x"), role=[ContactRoleCode.DISTRIBUTOR]),
                transfer_option=TransferOption(
                    online_resource=OnlineResource(href="x", function=OnlineResourceFunctionCode.DOWNLOAD)
                ),
            )
        ]

        tab = DataTab(distributions=distributions)

        assert tab.enabled is False
        # cov
        assert tab.title != ""
        assert tab.icon != ""

    def test_enable(self):
        """Can enable data tab with supported distribution options."""
        distributions = [
            RecordDistribution(
                distributor=RecordContact(organisation=ContactIdentity(name="x"), role=[ContactRoleCode.DISTRIBUTOR]),
                format=Format(
                    format="x",
                    href="https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+feature",
                ),
                transfer_option=TransferOption(
                    online_resource=OnlineResource(href="x", function=OnlineResourceFunctionCode.DOWNLOAD)
                ),
            ),
            RecordDistribution(
                distributor=RecordContact(organisation=ContactIdentity(name="x"), role=[ContactRoleCode.DISTRIBUTOR]),
                format=Format(
                    format="x",
                    href="https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+feature",
                ),
                transfer_option=TransferOption(
                    online_resource=OnlineResource(href="x", function=OnlineResourceFunctionCode.DOWNLOAD)
                ),
            ),
        ]
        tab = DataTab(distributions=distributions)
        assert tab.enabled is True

    def test_items(self):
        """Can get processed distribution options."""
        distributions = [
            RecordDistribution(
                distributor=RecordContact(organisation=ContactIdentity(name="x"), role=[ContactRoleCode.DISTRIBUTOR]),
                format=Format(
                    format="x",
                    href="https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+feature",
                ),
                transfer_option=TransferOption(
                    online_resource=OnlineResource(href="x", function=OnlineResourceFunctionCode.DOWNLOAD)
                ),
            ),
            RecordDistribution(
                distributor=RecordContact(organisation=ContactIdentity(name="x"), role=[ContactRoleCode.DISTRIBUTOR]),
                format=Format(
                    format="x",
                    href="https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+feature",
                ),
                transfer_option=TransferOption(
                    online_resource=OnlineResource(href="x", function=OnlineResourceFunctionCode.DOWNLOAD)
                ),
            ),
        ]
        expected = ArcGisFeatureLayer(distributions[0], [distributions[1]])
        tab = DataTab(distributions=distributions)

        assert tab.items[0].format_type == expected.format_type
        assert tab.items[0].action.href == expected.action.href


class TestExtentTab:
    """Test extent tab."""

    def test_init(self):
        """Can create extent tab."""
        extent = Extent(
            extent=ItemExtent(
                RecordExtent(
                    identifier="bounding",
                    geographic=ExtentGeographic(
                        bounding_box=BoundingBox(
                            west_longitude=1.0, east_longitude=1.0, south_latitude=1.0, north_latitude=1.0
                        )
                    ),
                )
            ),
            embedded_maps_endpoint="x",
        )

        tab = ExtentTab(extent=extent)

        assert tab.enabled is True
        assert tab.bounding_box == extent.bounding_box
        # cov
        assert str(tab) != ""  # to test __getattribute__ conditional logic
        assert tab.title != ""
        assert tab.icon != ""

    def test_none(self):
        """Can create extent tab without an extent."""
        tab = ExtentTab(extent=None)

        assert tab.enabled is False


class TestAuthorsTab:
    """Test authors tab."""

    def test_init(self):
        """Can create authors tab."""
        contacts = Contacts(
            [Contact(RecordContact(organisation=ContactIdentity(name="x"), role=[ContactRoleCode.AUTHOR]))]
        )

        tab = AuthorsTab(item_type=HierarchyLevelCode.PRODUCT, authors=contacts)

        assert tab.enabled is True
        assert tab.items == contacts
        # cov
        assert tab.title != ""
        assert tab.icon != ""

    @pytest.mark.parametrize(
        ("item_type", "has_authors", "expected"),
        [
            (HierarchyLevelCode.PRODUCT, True, True),
            (HierarchyLevelCode.PRODUCT, False, False),
            (HierarchyLevelCode.COLLECTION, True, False),
        ],
    )
    def test_disabled(self, item_type: HierarchyLevelCode, has_authors: bool, expected: bool):
        """Can disable authors tab based on item type and if item has any authors."""
        contact = Contact(RecordContact(organisation=ContactIdentity(name="x"), role=[ContactRoleCode.AUTHOR]))
        contacts = Contacts([])
        if has_authors:
            contacts.append(contact)

        tab = AuthorsTab(item_type=item_type, authors=contacts)

        assert tab.enabled == expected


class TestLicenceTab:
    """Test licence tab."""

    def test_init(self, fx_lib_item_catalogue: ItemCatalogue):
        """Can create licence tab."""
        constraint = Constraint(
            type=ConstraintTypeCode.USAGE,
            restriction_code=ConstraintRestrictionCode.LICENSE,
            href="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
            statement="x",
        )
        tab = LicenceTab(jinja=fx_lib_item_catalogue._jinja, item_type=HierarchyLevelCode.PRODUCT, licence=constraint)

        assert tab.enabled is True
        assert tab.content != ""
        # cov
        assert tab.title != ""
        assert tab.icon != ""

    @pytest.mark.parametrize(
        ("item_type", "has_licence", "expected"),
        [
            (HierarchyLevelCode.PRODUCT, True, True),
            (HierarchyLevelCode.PRODUCT, False, False),
            (HierarchyLevelCode.COLLECTION, True, False),
        ],
    )
    def test_disabled(
        self, fx_lib_item_catalogue: ItemCatalogue, item_type: HierarchyLevelCode, has_licence: bool, expected: bool
    ):
        """Can disable licence tab based on item type and if item has a licence."""
        constraint = Constraint(
            type=ConstraintTypeCode.USAGE,
            restriction_code=ConstraintRestrictionCode.LICENSE,
            href="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
            statement="x",
        )
        licence = constraint if has_licence else None

        tab = LicenceTab(jinja=fx_lib_item_catalogue._jinja, item_type=item_type, licence=licence)

        assert tab.enabled == expected
        if not has_licence:
            assert tab.content == ""


class TestLineageTab:
    """Test lineage tab."""

    def test_init(self):
        """Can create lineage tab."""
        expected = "x"

        tab = LineageTab(statement=expected)

        assert tab.enabled is True
        assert tab.statement == expected
        # cov
        assert tab.title != ""
        assert tab.icon != ""


class TestRelatedTab:
    """Test related tab."""

    def test_init(self):
        """Can create related tab."""
        aggregations = Aggregations(
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
        )

        tab = RelatedTab(aggregations=aggregations, item_type=HierarchyLevelCode.PRODUCT)

        assert tab.enabled is True
        assert len(tab.collections) > 0
        # cov
        assert tab.title != ""
        assert tab.icon != ""


class TestAdditionalInfoTab:
    """Test additional information tab."""

    def test_init(self):
        """Can create additional information tab."""
        item_id = "x"
        item_type = HierarchyLevelCode.PRODUCT
        dates = Dates(dates=RecordDates(creation=Date(date=datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC))))
        datestamp = datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC).date()
        standard = MetadataStandard(name="x", version="x")

        xml_href = f"/records/{item_id}.xml"
        html_href = f"/records/{item_id}.html"
        json_href = f"/records/{item_id}.json"

        tab = AdditionalInfoTab(
            item_id=item_id, item_type=item_type, dates=dates, datestamp=datestamp, standard=standard
        )

        assert tab.enabled is True
        assert tab.item_id == item_id
        assert tab.item_type == item_type.value
        assert tab.item_type_icon == "fa-fw far fa-map"
        assert isinstance(tab.dates, dict)
        assert tab.datestamp == format_date(Date(date=datestamp))
        assert tab.standard == "x"
        assert tab.standard_version == "x"
        assert tab.record_link_xml.href == xml_href
        assert tab.record_link_html.href == html_href
        assert tab.record_link_json.href == json_href
        assert len(tab.record_links) == 3
        # cov
        assert tab.title != ""
        assert tab.icon != ""


class TestContactTab:
    """Test contact tab."""

    def test_init(self):
        """Can create contact tab."""
        expected = "x"
        contact = Contact(
            RecordContact(
                organisation=ContactIdentity(name=expected), email=expected, role=[ContactRoleCode.POINT_OF_CONTACT]
            )
        )

        tab = ContactTab(contact=contact, item_id=expected, item_title=expected, form_action="x")

        assert tab.enabled is True
        assert tab.subject_default == f"Message about '{expected}'"
        assert tab.team == expected
        assert tab.email == expected
        # cov
        assert tab.title != ""
        assert tab.icon != ""

    @pytest.mark.parametrize(
        ("endpoint", "action", "params"),
        [
            ("x", "://x", {"item-id": "x"}),
            ("https://example.com?x=x", "https://example.com", {"item-id": "x", "x": "x"}),
        ],
    )
    def test_form(self, endpoint: str, action: str, params: dict[str, str]) -> None:
        """Can get contact form action and parameters."""
        contact = Contact(
            RecordContact(organisation=ContactIdentity(name="x"), email="x", role=[ContactRoleCode.POINT_OF_CONTACT])
        )

        tab = ContactTab(contact=contact, item_id="x", item_title="x", form_action=endpoint)
        assert tab.form_action == action
        assert tab.form_params == params

    @pytest.mark.parametrize("has_value", [True, False])
    def test_phone(self, has_value: bool):
        """Can get phone number if set."""
        expected = "x" if has_value else None
        contact = Contact(
            RecordContact(
                organisation=ContactIdentity(name="x"),
                email="x",
                phone=expected,
                role=[ContactRoleCode.POINT_OF_CONTACT],
            )
        )

        tab = ContactTab(contact=contact, item_id="x", item_title="x", form_action="x")
        assert tab.phone == expected

    @pytest.mark.parametrize("has_value", [True, False])
    def test_address(self, has_value: bool):
        """Can get address if set."""
        expected = "x<br/>y<br/>z<br/>a<br/>b<br/>c" if has_value else None
        address = (
            Address(delivery_point="x, y", city="z", administrative_area="a", postal_code="b", country="c")
            if has_value
            else None
        )
        contact = Contact(
            RecordContact(
                organisation=ContactIdentity(name="x"),
                email="x",
                address=address,
                role=[ContactRoleCode.POINT_OF_CONTACT],
            )
        )

        tab = ContactTab(contact=contact, item_id="x", item_title="x", form_action="x")
        assert tab.address == expected

    def test_no_team(self):
        """Can't create a contact tab without a Contact with an organisation name."""
        contact = Contact(
            RecordContact(individual=ContactIdentity(name="x"), email="x", role=[ContactRoleCode.POINT_OF_CONTACT])
        )
        tab = ContactTab(contact=contact, item_id="x", item_title="x", form_action="x")

        with pytest.raises(InvalidItemContactError):
            _ = tab.team

    def test_no_email(self):
        """Can't create a contact tab without a Contact with an organisation name."""
        contact = Contact(
            RecordContact(organisation=ContactIdentity(name="x"), role=[ContactRoleCode.POINT_OF_CONTACT])
        )
        tab = ContactTab(contact=contact, item_id="x", item_title="x", form_action="x")

        with pytest.raises(InvalidItemContactError):
            _ = tab.email
