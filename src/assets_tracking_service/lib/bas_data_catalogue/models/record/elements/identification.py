from dataclasses import dataclass
from typing import TypeVar

import cattrs

from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.common import (
    Citation,
    Date,
    Dates,
    Identifier,
)
from assets_tracking_service.lib.bas_data_catalogue.models.record.enums import (
    AggregationAssociationCode,
    AggregationInitiativeCode,
    ConstraintRestrictionCode,
    ConstraintTypeCode,
    MaintenanceFrequencyCode,
    ProgressCode,
)

TIdentification = TypeVar("TIdentification", bound="Identification")
TPeriod = TypeVar("TPeriod", bound="TemporalPeriod")


@dataclass(kw_only=True)
class Aggregation:
    """
    Aggregation.

    Schema definition: aggregation [1]
    ISO element: gmd:MD_AggregateInformation [2]

    [1] https://github.com/antarctica/metadata-library/blob/v0.15.1/src/bas_metadata_library/schemas/dist/iso_19115_2_v4.json#L74
    [2] https://www.datypic.com/sc/niem21/e-gmd_MD_AggregateInformation.html
    """

    identifier: Identifier
    association_type: AggregationAssociationCode
    initiative_type: AggregationInitiativeCode | None = None


@dataclass(kw_only=True)
class BoundingBox:
    """
    Geographic Extent Bounding Box.

    Schema definition: bounding_box [1]
    ISO element: gmd:EX_GeographicBoundingBox [2]

    [1] https://github.com/antarctica/metadata-library/blob/v0.15.1/src/bas_metadata_library/schemas/dist/iso_19115_2_v4.json#L749
    [2] https://www.datypic.com/sc/niem21/e-gmd_EX_GeographicBoundingBox.html
    """

    west_longitude: float
    east_longitude: float
    south_latitude: float
    north_latitude: float


@dataclass(kw_only=True)
class Constraint:
    """
    Constraint.

    Schema definition: constraint [1]
    ISO element: gmd:MD_LegalConstraints [2]

    [1] https://github.com/antarctica/metadata-library/blob/v0.15.1/src/bas_metadata_library/schemas/dist/iso_19115_2_v4.json#L145
    [2] https://www.datypic.com/sc/niem21/e-gmd_MD_LegalConstraints.html
    """

    type: ConstraintTypeCode
    restriction_code: ConstraintRestrictionCode | None = None
    statement: str | None = None
    href: str | None = None


@dataclass(kw_only=True)
class ExtentGeographic:
    """
    Geographic Extent.

    Schema definition: geographic_extent [1]
    ISO element: gmd:geographicElement [2]

    [1] https://github.com/antarctica/metadata-library/blob/v0.15.1/src/bas_metadata_library/schemas/dist/iso_19115_2_v4.json#L738
    [2] https://www.datypic.com/sc/niem21/e-gmd_geographicElement-1.html
    """

    bounding_box: BoundingBox


@dataclass(kw_only=True)
class TemporalPeriod:
    """
    Temporal Extent Period.

    Schema definition: period [1]
    ISO element: gml:TimePeriod [2]

    [1] https://github.com/antarctica/metadata-library/blob/v0.15.1/src/bas_metadata_library/schemas/dist/iso_19115_2_v4.json#L1652
    [2] https://www.datypic.com/sc/niem21/e-gml32_TimePeriod.html
    """

    start: Date | None = None
    end: Date | None = None


@dataclass(kw_only=True)
class ExtentTemporal:
    """
    Temporal Extent.

    Schema definition: temporal_extent [1]
    ISO element: gmd:temporalElement [2]

    [1] https://github.com/antarctica/metadata-library/blob/v0.15.1/src/bas_metadata_library/schemas/dist/iso_19115_2_v4.json#L1645
    [2] https://www.datypic.com/sc/niem21/e-gmd_temporalElement-1.html
    """

    period: TemporalPeriod | None = None

    def __post_init__(self) -> None:
        """Process defaults."""
        if self.period is None:
            self.period = TemporalPeriod()


@dataclass(kw_only=True)
class Extent:
    """
    Extent.

    Schema definition: extent [1]
    ISO element: gmd:EX_Extent [2]

    [1] https://github.com/antarctica/metadata-library/blob/v0.15.1/src/bas_metadata_library/schemas/dist/iso_19115_2_v4.json#L579
    [2] https://www.datypic.com/sc/niem21/e-gmd_EX_Extent.html
    """

    identifier: str
    geographic: ExtentGeographic
    temporal: ExtentTemporal | None = None


@dataclass(kw_only=True)
class GraphicOverview:
    """
    Graphic Overview.

    Schema definition: graphic_overview [1]
    ISO element: gmd:MD_BrowseGraphic [2]

    [1] https://github.com/antarctica/metadata-library/blob/v0.15.1/src/bas_metadata_library/schemas/dist/iso_19115_2_v4.json#L690
    [2] https://www.datypic.com/sc/niem21/e-gmd_MD_BrowseGraphic.html
    """

    identifier: str
    href: str
    description: str | None = None
    mime_type: str


@dataclass(kw_only=True)
class Maintenance:
    """
    Maintenance.

    Schema definition: maintenance [1]
    ISO element: gmd:MD_MaintenanceInformation [2]

    [1] https://github.com/antarctica/metadata-library/blob/v0.15.1/src/bas_metadata_library/schemas/dist/iso_19115_2_v4.json#L1116
    [2] https://www.datypic.com/sc/niem21/e-gmd_MD_MaintenanceInformation.html
    """

    maintenance_frequency: MaintenanceFrequencyCode | None = None
    progress: ProgressCode | None = None


@dataclass(kw_only=True)
class Identification(Citation):
    """
    Identification.

    Wrapper around citation.

    Schema definition: identification [1]
    ISO element: gmd:MD_DataIdentification [2]

    [1] https://github.com/antarctica/metadata-library/blob/v0.15.1/src/bas_metadata_library/schemas/dist/iso_19115_2_v4.json#L861
    [2] https://www.datypic.com/sc/niem21/e-gmd_MD_DataIdentification.html
    """

    abstract: str
    purpose: str | None = None
    maintenance: Maintenance | None = None
    graphic_overviews: list[GraphicOverview] | None = None
    constraints: list[Constraint] | None = None
    aggregations: list[Aggregation] | None = None
    character_set: str = "utf8"
    language: str = "eng"
    extents: list[Extent] | None = None

    def __post_init__(self) -> None:
        """Process defaults."""
        super().__post_init__()
        if self.maintenance is None:
            self.maintenance = Maintenance()
        if self.graphic_overviews is None:
            self.graphic_overviews = []
        if self.constraints is None:
            self.constraints = []
        if self.aggregations is None:
            self.aggregations = []
        if self.extents is None:
            self.extents = []

    @classmethod
    def structure(cls: type[TIdentification], value: dict) -> "Identification":
        """
        Parse Identification class from plain types.

        Returns a new class instance with parsed data. Intended to be used as a cattrs structure hook.
        E.g. `converter.register_structure_hook(Identification, lambda d, t: Identification.structure(d))`

        Steps:

        1. Unwrap title (i.e. `{'title': {'value': 'x'}, 'abstract': 'x'}` -> `{'title': 'x', 'abstract': 'x'}`)
        2. Convert the input dict to a new instance of this class via cattrs
        """
        converter = cattrs.Converter()
        converter.register_structure_hook(Date, lambda d, t: Date.structure(d))
        converter.register_structure_hook(Dates, lambda d, t: Dates.structure(d))

        title = value.pop("title")["value"]
        value["title"] = title
        return converter.structure(value, cls)

    def unstructure(self) -> dict:
        """
        Convert Identification class into plain types.

        Intended to be used as a cattrs unstructure hook.
        E.g. `converter.register_unstructure_hook(Identification, lambda d: d.unstructure())`

        Steps:

        1. Convert the class instance into plain types via cattrs
        2. Wrap title (i.e. `{'title': 'x', 'abstract': 'x'}` -> {'title': {'value': 'x'}, 'abstract': 'x'})
        """
        converter = cattrs.Converter()
        converter.register_unstructure_hook(Date, lambda d: d.unstructure())
        converter.register_unstructure_hook(Dates, lambda d: d.unstructure())
        value = converter.unstructure(self)

        title = value.pop("title")
        value["title"] = {"value": title}

        return value
