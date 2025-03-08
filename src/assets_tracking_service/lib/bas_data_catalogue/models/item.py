import json
from dataclasses import asdict, dataclass
from enum import Enum
from json import JSONDecodeError
from urllib.parse import unquote

from markdown import markdown

from assets_tracking_service.lib.bas_data_catalogue.models.record import (
    Record,
)
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.common import Identifier as RecordIdentifier
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.identification import (
    Constraint as RecordConstraint,
)
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.identification import (
    GraphicOverview as RecordGraphicOverview,
)
from assets_tracking_service.lib.bas_data_catalogue.models.record.enums import (
    ConstraintRestrictionCode,
    ConstraintTypeCode,
)
from assets_tracking_service.lib.markdown.formats.plaintext import convert_to_plain_text as markdown_plaintext

PERMISSIONS_NERC_DIRECTORY = "b311db95-32ad-438f-a101-7ba061712a4e"
PERMISSIONS_BAS_GROUP = "6fa3b48c-393c-455f-b787-c006f839b51f"


class AccessType(Enum):
    NONE: str = "none"
    PUBLIC: str = "public"
    BAS_ALL: str = "bas_all"


class GraphicLabelNotFoundError(Exception):
    """Raised when a given graphic label can't be found in a record."""

    pass


class GraphicLabelAmbiguityError(Exception):
    """Raised when a record contains multiple graphics with a given label, making it ambiguous which to return."""

    pass


class ConstraintNotFoundError(Exception):
    """Raised when a given constraint can't be found in a record."""

    pass


class ConstraintAmbiguityError(Exception):
    """Raised when a record contains multiple constraints with of a given type/code, making it ambiguous which to return."""

    pass


class IdentifierNamespaceNotFoundError(Exception):
    """Raised when a given identifier namespace can't be found in a record."""

    pass


class IdentifierNamespaceAmbiguityError(Exception):
    """Raised when a record contains multiple identifiers with a given namespace, making it ambiguous which to return."""

    pass


@dataclass
class Graphic:
    """
    Item graphic.

    Wrapper around Record GraphicOverview to rename properties.
    """

    _graphic: RecordGraphicOverview

    @property
    def label(self) -> str:
        return self._graphic.identifier

    @property
    def description(self) -> str | None:
        return self._graphic.description

    @property
    def src(self) -> str:
        return self._graphic.href

    @property
    def media_type(self) -> str:
        return self._graphic.mime_type


class Constraint(RecordConstraint):
    """
    Item constraint.

    Wrapper around Record constraint.
    """

    def __init__(self, constraint: RecordConstraint) -> None:
        # noinspection PyTypeChecker
        super().__init__(**asdict(constraint))


@dataclass
class Licence:
    """
    Item licence.

    Represents a usage constraint relating to licencing.
    """

    href: str
    statement: str | None = None


class Identifier(RecordIdentifier):
    """
    Item identifier.

    Wrapper around Record Identifier.
    """

    def __init__(self, identifier: RecordIdentifier) -> None:
        # noinspection PyTypeChecker
        super().__init__(**asdict(identifier))


class ItemBase:
    """
    Base representation of a resource within the BAS Data Catalogue / Metadata ecosystem.

    Items are a high-level, read-only, and non-standards specific view of a resource via an underlying Record instance,
    abstracting the underlying ISO 19115 information model to make it easier to use through various filtering,
    processing and formatting methods.

    Though not required by records, items require a file_identifier.

    Multiple Item classes are used for different contexts and systems. This base representation contains core/common
    properties and methods shared between all Item classes. It is not expected to be used directly.
    """

    def __init__(self, record: Record) -> None:
        self._record: Record = record

    @staticmethod
    def _md_as_html(string: str) -> str:
        """
        Encode string with possible Markdown as HTML.

        At a minimum the string will be returned as a paragraph.
        """
        return markdown(string, output_format="html", extensions=["tables"])

    @staticmethod
    def _md_as_plain(string: str) -> str:
        """Strip possible Markdown formatting from a string."""
        return markdown_plaintext(string)

    @staticmethod
    def _parse_permissions(href: str | None) -> list[AccessType]:
        """
        Decode permissions encoded in an access constraint.

        Decodes and maps supported payloads to members of the AccessType enum.

        The ISO 19115 information model does not provide for detailed access permissions to be defined. As a workaround
        a local convention is used to encode permissions via a URL fragment containing URL encoded serialised JSON data.

        These permissions are only understood (and only intended to be understood) by systems and tools within the BAS
        Data Catalogue / Metadata ecosystem. They are not considered sensitive information.

        If configured, the JSON data defines a payload defined, and specific to, a scheme name and version. Payloads are
        not intended to be portable between these schemes. Resources may contain multiple payloads, either to encode
        multiple permissions within a given scheme (e.g. using logical OR) or to encode permissions in multiple schemes.

        This method only returns of a list of supported/parsable permissions. Other methods will use this list to
        determine which permissions are applicable in a given context.
        """
        permissions = []

        if href is None:
            return permissions

        href_decoded = unquote(href.replace("#", ""))
        try:
            data = json.loads(href_decoded)
        except JSONDecodeError:
            return permissions

        for item in data:
            if (
                "scheme" not in item
                or item["scheme"] != "ms_graph"
                or "schemeVersion" not in item
                or item["schemeVersion"] != "1"
            ):
                continue
            if item["directoryId"] == PERMISSIONS_NERC_DIRECTORY and item["objectId"] == PERMISSIONS_BAS_GROUP:
                permissions.append(AccessType.BAS_ALL)

        return permissions

    @property
    def resource_id(self) -> str:
        """
        Resource identifier.

        AKA resource/record/item/file identifier.
        """
        return self._record.file_identifier

    @property
    def title_raw(self) -> str:
        """Raw Title."""
        return self._record.identification.title

    @property
    def title_md(self) -> str:
        """Title with Markdown formatting."""
        return f"# {self.title_raw}"

    @property
    def title_plain(self) -> str:
        """Title without Markdown formatting."""
        return self._md_as_plain(self.title_md)

    @property
    def summary_raw(self) -> str | None:
        """Optional raw Summary (purpose)."""
        return self._record.identification.purpose

    @property
    def summary_md(self) -> str | None:
        """Optional summary (purpose) with Markdown formatting if present."""
        return self.summary_raw

    @property
    def summary_plain(self) -> str | None:
        """Optional summary (purpose) without Markdown formatting."""
        _summary_md = self.summary_md
        return None if _summary_md is None else self._md_as_plain(_summary_md)

    @property
    def abstract_raw(self) -> str:
        """Raw Abstract."""
        return self._record.identification.abstract

    @property
    def abstract_md(self) -> str:
        """Abstract with Markdown formatting if present."""
        return self.abstract_raw

    @property
    def abstract_html(self) -> str:
        """Abstract with Markdown formatting, if present, encoded as HTML."""
        return self._md_as_html(self.abstract_md)

    @property
    def lineage_raw(self) -> str | None:
        """Optional raw lineage statement."""
        if self._record.data_quality is None or self._record.data_quality.lineage is None:
            return None
        return self._record.data_quality.lineage.statement

    @property
    def lineage_md(self) -> str | None:
        """Optional lineage statement with Markdown formatting if present."""
        return self.lineage_raw

    @property
    def lineage_html(self) -> str | None:
        """Optional lineage statement with Markdown formatting, if present, encoded as HTML."""
        return self._md_as_html(self.lineage_md) if self.lineage_md is not None else None

    @property
    def graphic_overviews(self) -> list[Graphic]:
        """List of any optional graphic overviews."""
        return [Graphic(graphic) for graphic in self._record.identification.graphic_overviews]

    def get_graphic_overview(self, label: str) -> Graphic:
        """
        Get a specific graphic overview by label.

        Where a label isn't found, or multiple graphics match, an exception is raised.
        """
        _results = []
        for graphic in self.graphic_overviews:
            if graphic.label == label:
                _results.append(graphic)

        if len(_results) == 0:
            msg = f"No graphic with label '{label}' found in item '{self.resource_id}'."
            raise GraphicLabelNotFoundError(msg) from None
        if len(_results) > 1:
            msg = f"Multiple graphics with label '{label}' found in item '{self.resource_id}'."
            raise GraphicLabelAmbiguityError(msg) from None

        return _results[0]

    @property
    def citation_raw(self) -> str | None:
        """Optional raw citation."""
        _citation = self._record.identification.other_citation_details
        return None if _citation is None else _citation

    @property
    def citation_md(self) -> str | None:
        """Optional citation with Markdown formatting if present."""
        return self.citation_raw

    @property
    def citation_html(self) -> str | None:
        """Optional citation with Markdown formatting, if present, encoded as HTML."""
        _citation = self.citation_md
        return None if _citation is None else self._md_as_html(_citation)

    @property
    def constraints(self) -> list[Constraint]:
        """List of any optional constraints."""
        return [Constraint(constraint) for constraint in self._record.identification.constraints]

    def get_constraint(self, type_: ConstraintTypeCode, code: ConstraintRestrictionCode | None = None) -> Constraint:
        """
        Get a specific constraint by its type and optionally code.

        Where a constraint isn't found, or multiple constraints match, an exception is raised.
        """
        _results = []
        for constraint in self.constraints:
            if constraint.type == type_ and (code is None or constraint.restriction_code == code):
                _results.append(constraint)

        _err_clauses = f"label '{type_.name}'"
        if code is not None:
            _err_clauses += f" and code '{code.name}'"
        if len(_results) == 0:
            msg = f"No constraint with {_err_clauses} found in item '{self.resource_id}'."
            raise ConstraintNotFoundError(msg) from None
        if len(_results) > 1:
            clauses = f"label '{type_.name}'"
            if code is not None:
                clauses += f" and code '{code.name}'"
            msg = f"Multiple constraints with {_err_clauses} found in item '{self.resource_id}'."
            raise ConstraintAmbiguityError(msg) from None

        return _results[0]

    @property
    def access(self) -> AccessType:
        """
        Access constraint.

        Who can access this item.

        No graceful error handling as property is required by MAGIC profile.
        """
        try:
            constraint = self.get_constraint(type_=ConstraintTypeCode.ACCESS)
        except ConstraintNotFoundError:
            return AccessType.NONE

        permissions = self._parse_permissions(constraint.href)

        if constraint.restriction_code == ConstraintRestrictionCode.UNRESTRICTED:
            return AccessType.PUBLIC
        if AccessType.BAS_ALL in permissions:
            return AccessType.BAS_ALL

        # fail-safe
        return AccessType.NONE

    @property
    def licence(self) -> Licence | None:
        """
        Licence usage constraint.

        How may this item be used.

        No graceful error handling as property is required by MAGIC profile.
        """
        try:
            constraint = self.get_constraint(type_=ConstraintTypeCode.USAGE, code=ConstraintRestrictionCode.LICENSE)
        except ConstraintNotFoundError:
            return None

        return Licence(href=constraint.href, statement=constraint.statement)

    @property
    def identifiers(self) -> list[Identifier]:
        """List of any identifiers."""
        return [Identifier(identifier) for identifier in self._record.identification.identifiers]

    def get_identifier(self, namespace: str) -> Identifier:
        _results = []
        for identifier in self.identifiers:
            if identifier.namespace == namespace:
                _results.append(identifier)

        if len(_results) == 0:
            msg = f"No identifier with namespace '{namespace}' found in item '{self.resource_id}'."
            raise IdentifierNamespaceNotFoundError(msg) from None
        if len(_results) > 1:
            msg = f"Multiple identifiers with namespace '{namespace}' found in item '{self.resource_id}'."
            raise IdentifierNamespaceAmbiguityError(msg) from None

        return _results[0]
