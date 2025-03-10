from copy import deepcopy
from dataclasses import astuple, dataclass, field
from datetime import UTC, date, datetime
from typing import TypeVar

import cattrs

from assets_tracking_service.lib.bas_data_catalogue.models.record.enums import (
    ContactRoleCode,
    DatePrecisionCode,
    DateTypeCode,
    OnlineResourceFunctionCode,
)

TDate = TypeVar("TDate", bound="Date")
TDates = TypeVar("TDates", bound="Dates")
TCitation = TypeVar("TCitation", bound="Citation")


def _clean_val(value: dict | list | str | float) -> dict | list | str | float:
    if isinstance(value, dict):
        cleaned_dict = {k: _clean_val(v) for k, v in value.items() if v not in (None, [], {})}
        return {k: v for k, v in cleaned_dict.items() if v not in (None, [], {})}
    if isinstance(value, list):
        cleaned_list = [_clean_val(v) for v in value if v not in (None, [], {})]
        return cleaned_list if cleaned_list else None
    return value


def clean_dict(d: dict) -> dict:
    """Remove any None or empty list/dict values from a dict."""
    cleaned = _clean_val(d)
    return {k: v for k, v in cleaned.items() if v not in (None, [], {})}


@dataclass(kw_only=True)
class OnlineResource:
    """
    Online Resource.

    Schema definition: online_resource [1]
    ISO element: gmd:CI_OnlineResource [2]

    [1] https://github.com/antarctica/metadata-library/blob/v0.15.1/src/bas_metadata_library/schemas/dist/iso_19115_2_v4.json#L1205
    [2] https://www.datypic.com/sc/niem21/e-gmd_CI_OnlineResource.html
    """

    href: str
    protocol: str | None = None
    title: str | None = None
    description: str | None = None
    function: OnlineResourceFunctionCode


@dataclass(kw_only=True)
class ContactIdentity:
    """
    Individual or Organisation.

    Meta element representing a xlink:anchor (name/value, href/title) element for either a person or organisation.

    Schema definition: contact_identity [1]
    ISO element: gmd:organisationName, gmd:individualName [2]

    [1] https://github.com/antarctica/metadata-library/blob/v0.15.1/src/bas_metadata_library/schemas/dist/iso_19115_2_v4.json#L359
    [2] https://www.datypic.com/sc/niem21/e-gmd_organisationName-1.html
        https://www.datypic.com/sc/niem21/e-gmd_individualName-1.html
    """

    name: str
    href: str | None = None
    title: str | None = None


@dataclass(kw_only=True)
class Address:
    """
    Address.

    Schema definition: address [1]
    ISO element: gmd:CI_Address [2]

    [1] https://github.com/antarctica/metadata-library/blob/v0.15.1/src/bas_metadata_library/schemas/dist/iso_19115_2_v4.json#L16
    [2] https://www.datypic.com/sc/niem21/e-gmd_CI_Address.html
    """

    delivery_point: str | None = None
    city: str | None = None
    administrative_area: str | None = None
    postal_code: str | None = None
    country: str | None = None


@dataclass(kw_only=True)
class Contact:
    """
    Contact.

    Schema definition: contact [1]
    ISO element: gmd:CI_ResponsibleParty [2]

    [1] https://github.com/antarctica/metadata-library/blob/v0.15.1/src/bas_metadata_library/schemas/dist/iso_19115_2_v4.json#L260
    [2] https://www.datypic.com/sc/niem21/e-gmd_CI_ResponsibleParty.html
    """

    individual: ContactIdentity | None = None
    organisation: ContactIdentity | None = None
    phone: str | None = None
    address: Address | None = None
    email: str | None = None
    online_resource: OnlineResource | None = None
    role: list[ContactRoleCode]
    _role: list[ContactRoleCode] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """Process defaults."""
        if self.individual is None and self.organisation is None:
            msg = "At least one of individual or organisation is required"
            raise ValueError(msg) from None

        if len(self.role) < 1:
            msg = "At least one role is required"
            raise ValueError(msg) from None

    @property
    def role(self) -> list[ContactRoleCode]:
        """Role(s)."""
        return self._role

    @role.setter
    def role(self, roles: list[ContactRoleCode]) -> None:
        # set to unique values
        self._role = list(set(roles))

    def eq_no_roles(self, other: "Contact") -> bool:
        """Compare if contacts are the same if roles are ignored."""
        self_ = deepcopy(self)
        self_.role = []
        other_ = deepcopy(other)
        other_.role = []

        return self_ == other_

    def eq_contains_roles(self, other: "Contact") -> bool:
        """Compare if contacts are the same if contact contains all roles of another."""
        if all(role in self.role for role in other.role):
            return self.eq_no_roles(other)
        return False


@dataclass(kw_only=True)
class Date:
    """
    Date.

    Schema definition: date [1]
    ISO element: gmd:CI_Date [2]

    [1] https://github.com/antarctica/metadata-library/blob/v0.15.1/src/bas_metadata_library/schemas/dist/iso_19115_2_v4.json#L415
    [2] https://www.datypic.com/sc/niem21/e-gmd_CI_Date.html
    """

    date: date | datetime
    precision: DatePrecisionCode | None = None

    def __post_init__(self) -> None:
        """Process defaults."""
        if isinstance(self.date, datetime) and (self.date.tzinfo is None or self.date.tzinfo != UTC):
            msg = f"Invalid timezone: [{self.date.tzinfo}]. It must be UTC."
            raise ValueError(msg)

    @property
    def isoformat(self) -> str:
        """Return date as ISO 8601 string accounting for possible date precision."""
        if self.precision is DatePrecisionCode.YEAR:
            return self.date.strftime("%Y")
        if self.precision is DatePrecisionCode.MONTH:
            return self.date.strftime("%Y-%m")
        if isinstance(self.date, datetime):
            return self.date.replace(microsecond=0).isoformat()
        return self.date.isoformat()

    @staticmethod
    def _fromisoformat(date_str: str) -> tuple[datetime | date, DatePrecisionCode | None]:
        """Parse date(time) from ISO 8601 string."""
        elements = date_str.split("T")
        if len(elements) > 1:
            return datetime.fromisoformat(date_str), None

        date_elements = elements[0].split("-")
        if len(date_elements) == 1:
            return date(int(date_elements[0]), 1, 1), DatePrecisionCode.YEAR
        if len(date_elements) == 2:
            return date(int(date_elements[0]), int(date_elements[1]), 1), DatePrecisionCode.MONTH
        return date.fromisoformat(date_str), None

    @classmethod
    def structure(cls: type[TDate], value: str) -> "Date":
        """
        Parse date from string.

        Returns a new class instance with parsed data. Intended to be used as a cattrs structure hook.
        E.g. `converter.register_structure_hook(Date, lambda d, t: Date.structure(d))`
        """
        date_, precision = cls._fromisoformat(value)
        return cls(date=date_, precision=precision)

    def unstructure(self) -> str:
        """
        Convert to plain types.

        Intended to be used as a cattrs unstructure hook.
        E.g. `converter.register_unstructure_hook(Date, lambda d: d.unstructure())`
        """
        return self.isoformat


@dataclass(kw_only=True)
class Dates:
    """
    Date.

    Schema definition: date [1]
    ISO element: N/A [2]

    [1] https://github.com/antarctica/metadata-library/blob/v0.15.1/src/bas_metadata_library/schemas/dist/iso_19115_2_v4.json#L415
    [2] -
    """

    creation: Date | None = None
    publication: Date | None = None
    revision: Date | None = None
    adopted: Date | None = None
    deprecated: Date | None = None
    distribution: Date | None = None
    expiry: Date | None = None
    in_force: Date | None = None
    last_revision: Date | None = None
    last_update: Date | None = None
    next_update: Date | None = None
    released: Date | None = None
    superseded: Date | None = None
    unavailable: Date | None = None
    validity_begins: Date | None = None
    validity_expires: Date | None = None

    def __post_init__(self) -> None:
        """Process defaults."""
        # noinspection PyTypeChecker
        if set(astuple(self)) == {None}:
            msg = "At least one date is required"
            raise ValueError(msg) from None

    @classmethod
    def structure(cls: type[TDates], value: dict[str, str]) -> "Dates":
        """
        Parse dates from plain types.

        Returns a new class instance with parsed data. Intended to be used as a cattrs structure hook.
        E.g. `converter.register_structure_hook(Dates, lambda d, t: Dates.structure(d))`

        Steps:
        1. for each key in the input dict, create a dict with each value as a new Date instance
        2. map each dict key to a DateTypeCode enum term and convert each key to lowercase

        Example input: {lastRevision: "2021"}
        Example output: Dates(last_revision=Date(date=date(2021, 1, 1), precision=DatePrecisionCode.YEAR))
        """
        dict_ = {DateTypeCode(k).name.lower(): Date.structure(v) for k, v in value.items()}
        return cls(**dict_)

    def unstructure(self) -> dict[str, str]:
        """
        Convert to plain types.

        Intended to be used as a cattrs unstructure hook.
        E.g. `converter.register_unstructure_hook(Dates, lambda d: d.unstructure())`

        Steps:
        1. create a dict of non-None class attributes
        3. map each dict key to a DateTypeCode enum term by converting each key to uppercase
        4. create and return a new dict using the mapped enum values as keys and Date.isoformat as values

        Example input: Dates(last_revision=Date(date=date(2021, 1, 1), precision=DatePrecisionCode.YEAR))
        Example output: {lastRevision: "2021"}
        """
        dict_ = {k: getattr(self, k) for k in self.__dataclass_fields__ if getattr(self, k) is not None}
        return {DateTypeCode[k.upper()].value: v.isoformat for k, v in dict_.items()}


@dataclass(kw_only=True)
class Identifier:
    """
    Identifier.

    Schema definition: identifier [1]
    ISO element: gmd:MD_Identifier [2]

    [1] https://github.com/antarctica/metadata-library/blob/v0.15.1/src/bas_metadata_library/schemas/dist/iso_19115_2_v4.json#L953
    [2] https://www.datypic.com/sc/niem21/e-gmd_MD_Identifier.html
    """

    identifier: str
    href: str
    namespace: str


@dataclass(kw_only=True)
class Citation:
    """
    Citation.

    Represents an ISO citation which forms part of identification, specification, authority, etc. The JSON schema
    dissolves this concept of a citation and embeds its properties into these contextual uses as needed. In these
    Python classes this is done by either inheriting from this class (as in identification), or by using it as an
    aliases property (as in specification for example).

    Schema definition: N/A [1]
    ISO element: gmd:CI_Citation [2]

    [1] -
    [2] https://www.datypic.com/sc/niem21/e-gmd_CI_Citation.html
    """

    title: str
    dates: Dates
    edition: str | None = None
    href: str | None = None
    identifiers: list[Identifier] | None = None
    other_citation_details: str | None = None
    contacts: list[Contact] = None

    def __post_init__(self) -> None:
        """Process defaults."""
        if self.identifiers is None:
            self.identifiers = []
        if self.contacts is None:
            self.contacts = []

    @classmethod
    def structure(cls: type[TCitation], value: dict) -> "Citation":
        """
        Parse Citation class from plain types.

        Returns a new class instance with parsed data. Intended to be used as a cattrs structure hook.
        E.g. `converter.register_structure_hook(Citation, lambda d, t: Citation.structure(d))`

        Note: Where this class is inherited and expanded (e.g. Identification), this method should be overridden and
        registered as a structure hook for the subclass.

        Steps:

        1. Unwrap title and href (i.e. `{'title': {'value': 'x', 'href': 'x'}, ...}` -> `{'title': 'x', 'href': 'x', ...}`)
        2. Convert the input dict to a new instance of this class via cattrs
        """
        converter = cattrs.Converter()
        converter.register_structure_hook(Dates, lambda d, t: Dates.structure(d))

        if "href" in value["title"]:
            href = value["title"].pop("href")
            value["href"] = href
        title = value.pop("title")["value"]
        value["title"] = title
        return converter.structure(value, cls)

    def unstructure(self) -> dict:
        """
        Convert Citation class into plain types.

        Intended to be used as a cattrs unstructure hook.
        E.g. `converter.register_unstructure_hook(Citation, lambda d: d.unstructure())`

        Note: Where this class is inherited and expanded (e.g. Identification), this method should be overridden and
        registered as a structure hook for the subclass.

        Steps:

        1. Convert the class instance into a dict via cattrs
        2. Wrap title and href (i.e. `{'title': 'x', 'href': 'x', ...}`) -> `{'title': {'value': 'x', 'href': 'x'}, ...}`
        """
        converter = cattrs.Converter()
        converter.register_unstructure_hook(Dates, lambda d: d.unstructure())
        value = converter.unstructure(self)

        title = {"value": value.pop("title")}
        if value["href"] is not None:
            title["href"] = value.pop("href")
        value["title"] = title

        return value
