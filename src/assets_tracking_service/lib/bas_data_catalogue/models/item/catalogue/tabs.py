from abc import ABC, abstractmethod
from datetime import date
from urllib.parse import parse_qs, urlparse

from jinja2 import Environment

from assets_tracking_service.lib.bas_data_catalogue.models.item.base.elements import Contact, Link
from assets_tracking_service.lib.bas_data_catalogue.models.item.base.elements import Extent as ItemExtent
from assets_tracking_service.lib.bas_data_catalogue.models.item.catalogue.distributions import (
    ArcGisFeatureLayer,
    ArcGisOgcApiFeatures,
    Distribution,
)
from assets_tracking_service.lib.bas_data_catalogue.models.item.catalogue.elements import (
    Aggregations,
    Dates,
    ItemSummaryCatalogue,
    format_date,
)
from assets_tracking_service.lib.bas_data_catalogue.models.item.catalogue.enums import ResourceTypeIcon
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.common import Date
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.distribution import (
    Distribution as RecordDistribution,
)
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.identification import Constraint
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.metadata import MetadataStandard
from assets_tracking_service.lib.bas_data_catalogue.models.record.enums import (
    HierarchyLevelCode,
)


class Tab(ABC):
    """Abstract item/page tab."""

    @property
    @abstractmethod
    def enabled(self) -> bool:
        """Whether tab is enabled."""
        ...

    @property
    @abstractmethod
    def anchor(self) -> str:
        """HTML anchor for tab."""
        ...

    @property
    @abstractmethod
    def title(self) -> str:
        """Tab title."""
        ...

    @property
    @abstractmethod
    def icon(self) -> bool:
        """Tab icon class."""
        ...


class ItemsTab(Tab):
    """Items tab."""

    def __init__(self, aggregations: Aggregations) -> None:
        self._aggregations = aggregations
        self._items = self._aggregations.items

    @property
    def enabled(self) -> bool:
        """Whether tab is enabled."""
        return len(self._items) > 0

    @property
    def anchor(self) -> str:
        """HTML anchor for tab."""
        return "items"

    @property
    def title(self) -> str:
        """Tab title."""
        return "Items"

    @property
    def icon(self) -> str:
        """Tab icon class."""
        return "far fa-ball-pile"

    @property
    def items(self) -> list[ItemSummaryCatalogue]:
        """Items that form the current item."""
        return self._items


class DataTab(Tab):
    """Data tab."""

    def __init__(self, distributions: list[RecordDistribution]) -> None:
        self._resource_distributions = distributions
        self._supported_distributions = [ArcGisFeatureLayer, ArcGisOgcApiFeatures]
        self._processed_distributions = self._process_distributions()

    def _process_distributions(self) -> list[Distribution]:
        """
        Determine supported distribution options.

        Checks each (unprocessed) resource distribution against supported catalogue distribution types.
        """
        processed = []
        for dist_option in self._resource_distributions:
            for dist_type in self._supported_distributions:
                if dist_type.matches(option=dist_option, other_options=self._resource_distributions):
                    processed.append(dist_type(option=dist_option, other_options=self._resource_distributions))
        return processed

    @property
    def enabled(self) -> bool:
        """Whether tab is enabled."""
        return len(self._processed_distributions) > 0

    @property
    def anchor(self) -> str:
        """HTML anchor for tab."""
        return "data"

    @property
    def title(self) -> str:
        """Tab title."""
        return "Data"

    @property
    def icon(self) -> str:
        """Tab icon class."""
        return "far fa-cube"

    @property
    def items(self) -> list[Distribution]:
        """Processed distribution options."""
        return self._processed_distributions


class ExtentTab(Tab):
    """Extent tab."""

    def __init__(self, extent: ItemExtent | None = None) -> None:
        self._extent = extent

    def __getattribute__(self, name: str) -> str | None:
        """Proxy calls to self._extent if applicable."""
        extent = object.__getattribute__(self, "_extent")
        if extent is not None and hasattr(extent, name):
            return getattr(extent, name)

        # pass-through
        return object.__getattribute__(self, name)

    @property
    def enabled(self) -> bool:
        """Whether tab is enabled."""
        return self._extent is not None

    @property
    def anchor(self) -> str:
        """HTML anchor for tab."""
        return "extent"

    @property
    def title(self) -> str:
        """Tab title."""
        return "Extent"

    @property
    def icon(self) -> str:
        """Tab icon class."""
        return "far fa-expand-arrows"


class AuthorsTab(Tab):
    """Authors tab."""

    def __init__(self, item_type: HierarchyLevelCode, authors: list[Contact]) -> None:
        self._item_type = item_type
        self._authors = authors

    @property
    def enabled(self) -> bool:
        """Whether tab is enabled."""
        if self._item_type == HierarchyLevelCode.COLLECTION:
            return False
        return len(self._authors) > 0

    @property
    def anchor(self) -> str:
        """HTML anchor for tab."""
        return "authors"

    @property
    def title(self) -> str:
        """Tab title."""
        return "Authors"

    @property
    def icon(self) -> str:
        """Tab icon class."""
        return "far fa-user-friends"

    @property
    def items(self) -> list[Contact]:
        """Authors."""
        return self._authors


class LicenceTab(Tab):
    """Licence tab."""

    def __init__(self, jinja: Environment, item_type: HierarchyLevelCode, licence: Constraint | None) -> None:
        self._jinja = jinja
        self._item_type = item_type
        self._licence = licence

    @property
    def enabled(self) -> bool:
        """Whether tab is enabled."""
        if self._item_type == HierarchyLevelCode.COLLECTION:
            return False
        return self._licence is not None

    @property
    def anchor(self) -> str:
        """HTML anchor for tab."""
        return "licence"

    @property
    def title(self) -> str:
        """Tab title."""
        return "Licence"

    @property
    def icon(self) -> str:
        """Tab icon class."""
        return "far fa-file-certificate"

    @property
    def content(self) -> str:
        """Render licence template."""
        mapping = {
            "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/": "licence-ogl-uk-3-0.j2"
        }

        if self._licence is None:
            return ""

        return self._jinja.get_template(f"_licences/{mapping[self._licence.href]}").render()


class LineageTab(Tab):
    """Lineage tab."""

    def __init__(self, statement: str | None) -> None:
        self._statement = statement

    @property
    def enabled(self) -> bool:
        """Whether tab is enabled."""
        return self._statement is not None

    @property
    def anchor(self) -> str:
        """HTML anchor for tab."""
        return "lineage"

    @property
    def title(self) -> str:
        """Tab title."""
        return "Lineage"

    @property
    def icon(self) -> str:
        """Tab icon class."""
        return "far fa-scroll-old"

    @property
    def statement(self) -> str | None:
        """Lineage statement."""
        return self._statement


class RelatedTab(Tab):
    """Related tab."""

    def __init__(self, item_type: HierarchyLevelCode, aggregations: Aggregations) -> None:
        self._item_type = item_type
        self._aggregations = aggregations

    def __getattribute__(self, name: str) -> str | int | None:
        """Proxy calls to self._aggregations and convert ItemSummaries to Links, if applicable."""
        aggregation = object.__getattribute__(self, "_aggregations")
        if hasattr(aggregation, name):
            result = getattr(aggregation, name)
            if isinstance(result, list) and all(isinstance(item, ItemSummaryCatalogue) for item in result):
                return aggregation.as_links(result)
            return result

        # pass-through
        return object.__getattribute__(self, name)

    @property
    def enabled(self) -> bool:
        """Whether tab is enabled."""
        all_agg = len(self._aggregations)
        if self._item_type == HierarchyLevelCode.COLLECTION:
            # if all aggregations are a collections items, disable tab as these are shown in item tab
            return len(self._aggregations.items) != all_agg
        return all_agg > 0

    @property
    def anchor(self) -> str:
        """HTML anchor for tab."""
        return "related"

    @property
    def title(self) -> str:
        """Tab title."""
        return "Related"

    @property
    def icon(self) -> str:
        """Tab icon class."""
        return "far fa-network-wired"


class AdditionalInfoTab(Tab):
    """Additional Information tab."""

    def __init__(
        self, item_id: str, item_type: HierarchyLevelCode, dates: Dates, datestamp: date, standard: MetadataStandard
    ) -> None:
        self._item_id = item_id
        self._item_type = item_type
        self._dates = dates
        self._datestamp = datestamp
        self._standard = standard

    @property
    def enabled(self) -> bool:
        """Whether tab is enabled."""
        return True

    @property
    def anchor(self) -> str:
        """HTML anchor for tab."""
        return "info"

    @property
    def title(self) -> str:
        """Tab title."""
        return "Additional Information"

    @property
    def icon(self) -> str:
        """Tab icon class."""
        return "far fa-info-square"

    @property
    def item_id(self) -> str:
        """Item ID."""
        return self._item_id

    @property
    def item_type(self) -> str:
        """Item type."""
        return self._item_type.value

    @property
    def item_type_icon(self) -> str:
        """Item type icon."""
        return ResourceTypeIcon[self._item_type.name].value

    @property
    def dates(self) -> dict[str, str]:
        """Dates."""
        return self._dates.as_dict_labeled()

    @property
    def datestamp(self) -> str:
        """Metadata datestamp."""
        return format_date(Date(date=self._datestamp))

    @property
    def standard(self) -> str:
        """Metadata standard."""
        return self._standard.name

    @property
    def standard_version(self) -> str:
        """Metadata standard version."""
        return self._standard.version

    @property
    def record_link_xml(self) -> Link:
        """Record link (raw XML)."""
        record = self.item_id
        return Link(value="View record as ISO 19115 XML", href=f"/records/{record}.xml")

    @property
    def record_link_html(self) -> Link:
        """Record link (XML HTML)."""
        record = self.item_id
        return Link(value="View record XML as ISO 19115 HTML", href=f"/records/{record}.html")

    @property
    def record_link_json(self) -> Link:
        """Record JSON (BAS ISO)."""
        record = self.item_id
        return Link(value="View record as ISO 19115 JSON (BAS schema)", href=f"/records/{record}.json")

    @property
    def record_links(self) -> list[Link]:
        """Record links."""
        return [self.record_link_xml, self.record_link_html, self.record_link_json]


class InvalidItemContactError(Exception):
    """Raised when the contact for the Item Contact tab is unsuitable."""

    pass


class ContactTab(Tab):
    """Content tab."""

    def __init__(self, contact: Contact, item_id: str, item_title: str, form_action: str) -> None:
        self._contact = contact
        self._id = item_id
        self._title = item_title
        self._form_action, self._form_required_params = self._parse_form_action(form_action)

    @staticmethod
    def _parse_form_action(form_action: str) -> tuple[str, dict[str, str]]:
        """
        Parse form action into base URL and required parameters.

        The item contact form uses Power Automate which uses an endpoint with required query parameters. When submitted
        the form fields are appended to the URL as query parameters, replacing Power Automates.

        To work around this, required parameters are converted to form parameters (as hidden inputs), which will then
        be included as query parameters when the form is submitted.
        """
        parsed_url = urlparse(form_action)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
        query_params = parse_qs(parsed_url.query)
        # parse_qs returns dict[str, list[str]] so convert to single values
        params = {k: v[0] for k, v in query_params.items()}

        return base_url, params

    @property
    def enabled(self) -> bool:
        """Whether tab is enabled."""
        return True

    @property
    def anchor(self) -> str:
        """HTML anchor for tab."""
        return "contact"

    @property
    def title(self) -> str:
        """Tab title."""
        return "Contact"

    @property
    def icon(self) -> str:
        """Tab icon class."""
        return "far fa-comment-alt-lines"

    @property
    def form_action(self) -> str:
        """Contact form action URL."""
        return self._form_action

    @property
    def form_params(self) -> dict[str, str]:
        """Contact form required parameters."""
        return {"item-id": self._id, **self._form_required_params}

    @property
    def subject_default(self) -> str:
        """Item title."""
        return f"Message about '{self._title}'"

    @property
    def team(self) -> str:
        """Team."""
        if self._contact.organisation is None:
            msg = "Item contact must have an organisation."
            raise InvalidItemContactError(msg)

        return self._contact.organisation.name

    @property
    def email(self) -> str:
        """Email."""
        if self._contact.email is None:
            msg = "Item contact must have an email."
            raise InvalidItemContactError(msg)

        return self._contact.email

    @property
    def phone(self) -> str | None:
        """Phone number."""
        return self._contact.phone

    @property
    def address(self) -> str | None:
        """Address."""
        if self._contact.address is None:
            return None

        address = self._contact.address
        parts = [
            *address.delivery_point.split(", "),
            address.city,
            address.administrative_area,
            address.postal_code,
            address.country,
        ]
        return "<br/>".join([part for part in parts if part is not None])
