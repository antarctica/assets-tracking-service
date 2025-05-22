from dataclasses import dataclass
from datetime import date
from typing import TypeVar

from assets_tracking_service.lib.bas_data_catalogue.models.record import Record
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.common import Date
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.identification import (
    Aggregations,
    Constraints,
    GraphicOverviews,
)
from assets_tracking_service.lib.bas_data_catalogue.models.record.enums import HierarchyLevelCode

TRecordSummary = TypeVar("TRecordSummary", bound="RecordSummary")


@dataclass(kw_only=True)
class RecordSummary:
    """
    Summary of a resource within the BAS Data Catalogue / Metadata ecosystem.

    RecordSummaries are a low-level view of key aspects of a resource, using the ISO 19115 information model. They are
    intended to be used where full records are unnecessary or would be impractical - such as describing/listing large
    numbers of resources, or for resources related to a selected resource.

    RecordSummaries can be created independently but are intended to be derived from a Record instance using `loads()`.
    This class does not support loading/dumping record configurations encoded in JSON or XML.
    """

    file_identifier: str | None = None
    hierarchy_level: HierarchyLevelCode
    date_stamp: date
    title: str
    purpose: str | None = None
    edition: str | None = None
    creation: Date
    revision: Date | None = None
    publication: Date | None = None
    graphic_overviews: GraphicOverviews | None = None
    constraints: Constraints | None = None
    aggregations: Aggregations | None = None

    def __post_init__(self) -> None:
        """Process defaults."""
        if self.graphic_overviews is None:
            self.graphic_overviews = GraphicOverviews()
        if self.constraints is None:
            self.constraints = Constraints()
        if self.aggregations is None:
            self.aggregations = Aggregations()

    @classmethod
    def loads(cls: type[TRecordSummary], record: Record) -> "RecordSummary":
        """Create a RecordSummary from a Record."""
        return cls(
            file_identifier=record.file_identifier,
            hierarchy_level=record.hierarchy_level,
            date_stamp=record.metadata.date_stamp,
            title=record.identification.title,
            purpose=record.identification.purpose,
            edition=record.identification.edition,
            creation=record.identification.dates.creation,
            revision=record.identification.dates.revision,
            publication=record.identification.dates.publication,
            graphic_overviews=record.identification.graphic_overviews,
            constraints=record.identification.constraints,
            aggregations=record.identification.aggregations,
        )

    @property
    def revision_creation(self) -> Date:
        """Revision date, or creation if not defined."""
        return self.revision if self.revision else self.creation
