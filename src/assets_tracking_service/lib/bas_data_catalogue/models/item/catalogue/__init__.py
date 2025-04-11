from collections.abc import Callable
from datetime import UTC, datetime

from bs4 import BeautifulSoup
from jinja2 import Environment, PackageLoader, select_autoescape

from assets_tracking_service.lib.bas_data_catalogue.models.item.base import ItemBase
from assets_tracking_service.lib.bas_data_catalogue.models.item.base.elements import Link
from assets_tracking_service.lib.bas_data_catalogue.models.item.catalogue.elements import (
    Aggregations,
    Dates,
    Extent,
    PageHeader,
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
    Tab,
)
from assets_tracking_service.lib.bas_data_catalogue.models.record import Record, RecordSummary
from assets_tracking_service.lib.bas_data_catalogue.models.record.enums import ContactRoleCode


class ItemCatalogue(ItemBase):
    """
    Representation of a resource within the BAS Data Catalogue.

    Catalogue items structure a base item into the (HTML) page structure used in the BAS Data Catalogue website using
    Jinja2 templates and classes representing the various tabs and other sections that form these pages.

    In addition to a catalogue Record instance, this Item implementation requires:
    - endpoints for external services used in this template, such as the item contact form and extent map
    - a callable to get a RecordSummary for a given identifier (used for related items from aggregations)

    Note: This class is an incomplete rendering of Record properties (which is itself an incomplete mapping of the
    ISO 19115:2003 / 19115-2:2009 standards). The list below is a work in progress.

    Supported properties:
    - file_identifier
    - hierarchy_level
    - identification.citation.title
    - identification.citation.dates
    - identification.citation.edition
    - identification.citation.contacts ('author' roles and a single 'point of contact' role only, and except `contact.position`)
    - identification.abstract
    - identification.aggregations ('collections' and 'items' only)
    - identification.constraints ('licence' only)
    - identification.extent (single bounding temporal and geographic bounding box extent only)
    - identification.other_citation_details
    - data_quality.lineage.statement
    - distributor.format (`format` and `href` only)
    - distributor.transfer_option (except `online_resource.protocol`)

    Unsupported properties:
    - identification.citation.identifiers
    - identification.aggregations (except 'collections' and 'items')
    - identification.constraints (except 'licence')
    - identification.graphic_overviews
    - identification.maintenance
    - identification.purpose
    - data_quality.domain_consistency

    Intentionally omitted properties:
    - *.character_set (not useful to end-users, present in underlying record)
    - *.language (not useful to end-users, present in underlying record)
    - *.online_resource.protocol (not useful to end-users, present in underlying record)
    - distribution.distributor
    """

    def __init__(
        self,
        record: Record,
        embedded_maps_endpoint: str,
        item_contact_endpoint: str,
        sentry_dsn: str,
        get_record_summary: Callable[[str], RecordSummary],
    ) -> None:
        super().__init__(record)
        self._embedded_maps_endpoint = embedded_maps_endpoint
        self._item_contact_endpoint = item_contact_endpoint
        self._sentry_dsn = sentry_dsn
        self._get_summary = get_record_summary

        _loader = PackageLoader("assets_tracking_service.lib.bas_data_catalogue", "resources/templates")
        self._jinja = Environment(loader=_loader, autoescape=select_autoescape(), trim_blocks=True, lstrip_blocks=True)

    @staticmethod
    def _prettify_html(html: str) -> str:
        """
        Prettify HTML string, removing any empty lines.

        Without careful whitespace control, Jinja templates can look messy where conditionals and other logic is used.
        Whilst this doesn't strictly matter, it is nicer if output looks well-formed.
        """
        return BeautifulSoup(html, parser="html.parser", features="lxml").prettify()

    @property
    def _aggregations(self) -> Aggregations:
        """Aggregations."""
        return Aggregations(aggregations=self.aggregations, get_summary=self._get_summary)

    @property
    def _dates(self) -> Dates:
        """Formatted dates."""
        return Dates(self._record.identification.dates)

    @property
    def _items(self) -> ItemsTab:
        """Items tab."""
        return ItemsTab(aggregations=self._aggregations)

    @property
    def _data(self) -> DataTab:
        """Data tab."""
        return DataTab(self.distributions)

    @property
    def _authors(self) -> AuthorsTab:
        """Authors tab."""
        return AuthorsTab(item_type=self.resource_type, authors=self.contacts.filter(roles=ContactRoleCode.AUTHOR))

    @property
    def _licence(self) -> LicenceTab:
        """Licence tab."""
        return LicenceTab(jinja=self._jinja, item_type=self.resource_type, licence=super().licence)

    @property
    def _extent(self) -> ExtentTab:
        """Extent tab."""
        bounding_ext = self.bounding_extent
        extent = Extent(bounding_ext, embedded_maps_endpoint=self._embedded_maps_endpoint) if bounding_ext else None
        return ExtentTab(extent=extent)

    @property
    def _lineage(self) -> LineageTab:
        """Lineage tab."""
        return LineageTab(statement=self.lineage_html)

    @property
    def _related(self) -> RelatedTab:
        """Related tab."""
        return RelatedTab(item_type=self.resource_type, aggregations=self._aggregations)

    @property
    def _additional_info(self) -> AdditionalInfoTab:
        """Additional Information tab."""
        return AdditionalInfoTab(
            item_id=self.resource_id,
            item_type=self.resource_type,
            dates=self._dates,
            datestamp=self._record.metadata.date_stamp,
            standard=self._record.metadata.metadata_standard,
        )

    @property
    def _contact(self) -> ContactTab:
        """Contact tab."""
        poc = self.contacts.filter(roles=ContactRoleCode.POINT_OF_CONTACT)[0]
        return ContactTab(
            contact=poc, item_id=self.resource_id, item_title=self.title_plain, form_action=self._item_contact_endpoint
        )

    @property
    def sentry_dsn(self) -> str:
        """Sentry DSN."""
        return self._sentry_dsn

    @property
    def html_title(self) -> str:
        """Title with without formatting with site name appended, for HTML title element."""
        return f"{self.title_plain} | BAS Data Catalogue"

    @property
    def page_header(self) -> PageHeader:
        """Page header."""
        return PageHeader(title=self.title_html, item_type=self.resource_type)

    @property
    def summary(self) -> Summary:
        """Item summary."""
        return Summary(
            item_type=self.resource_type,
            edition=self.edition,
            released_date=self._dates.released,
            aggregations=self._aggregations,
            citation=self.citation_html,
            abstract=self.abstract_html,
        )

    @property
    def graphics(self) -> list[Link]:
        """Item graphics."""
        return [Link(href=graphic.href, value=graphic.description) for graphic in super().graphics]

    @property
    def noscript_href(self) -> str:
        """URL for alternate item representation in cases where JavaScript is unavailable."""
        return self._additional_info.record_link_html.href

    @property
    def tabs(self) -> list[Tab]:
        """For generating item navigation."""
        return [
            self._items,
            self._data,
            self._authors,
            self._licence,
            self._extent,
            self._lineage,
            self._related,
            self._additional_info,
            self._contact,
        ]

    @property
    def default_tab_anchor(self) -> str:
        """Anchor of first enabled tab."""
        for tab in [
            self._items,
            self._data,
            self._authors,
            self._licence,
            self._extent,
            self._lineage,
            self._related,
        ]:
            if tab.enabled:
                return tab.anchor
        return self._additional_info.anchor

    def render(self) -> str:
        """Render HTML representation of item."""
        current_year = datetime.now(tz=UTC).year
        raw = self._jinja.get_template("item.html.j2").render(item=self, current_year=current_year)
        return self._prettify_html(raw)
