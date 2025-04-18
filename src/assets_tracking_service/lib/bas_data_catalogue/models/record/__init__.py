import contextlib
import json
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from typing import TypeVar

import cattrs
from importlib_resources import as_file as resources_as_file
from importlib_resources import files as resources_files
from jsonschema.exceptions import ValidationError
from jsonschema.validators import validate

from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.common import Date, clean_dict
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.data_quality import DataQuality
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.distribution import Distribution
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.identification import Identification
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.metadata import Metadata
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.projection import ReferenceSystemInfo
from assets_tracking_service.lib.bas_data_catalogue.models.record.enums import HierarchyLevelCode

TRecord = TypeVar("TRecord", bound="Record")
TRecordSummary = TypeVar("TRecordSummary", bound="RecordSummary")


class RecordInvalidError(Exception):
    """Raised when a record has invalid content."""

    def __init__(self, validation_error: Exception) -> None:
        self.validation_error = validation_error


class RecordSchema(Enum):
    """Record validation schemas."""

    ISO_2_V4 = "iso_2_v4"
    MAGIC_V1 = "magic_v1"


RECORD_SCHEMA_MAPPING = {
    "https://metadata-standards.data.bas.ac.uk/profiles/magic-discovery-v1/": RecordSchema.MAGIC_V1
}


@dataclass(kw_only=True)
class Record:
    """
    Representation of a resource within the BAS Data Catalogue / Metadata ecosystem.

    Records are low-level view of a resource using the ISO 19115 information model. This class is an incomplete mapping
    of the BAS Metadata Library ISO 19115:2003 / 19115-2:2009 v4 configuration schema [1] to Python dataclasses, with
    code lists represented by Python enums. See [4]/[5] for (un)supported config elements.

    Complete record configurations can be loaded from a plain Python dict using `loads_schema()` and dumped back using
    `dumps_schema()`. This class cannot be used to load/dump from/to XML.

    Schema definition: resource [2]
    ISO element: gmd:MD_Metadata [3]

    [1] https://metadata-resources.data.bas.ac.uk/bas-metadata-generator-configuration-schemas/v2/iso-19115-2-v4.json
    [2] https://github.com/antarctica/metadata-library/blob/v0.15.1/src/bas_metadata_library/schemas/dist/iso_19115_2_v4.json#L1430
    [3] https://www.datypic.com/sc/niem21/e-gmd_MD_Metadata.html
    [4] Supported elements:
        - `$schema`
        - `*.character_set` (hard-coded)
        - `*.citation.title`
        - `*.citation.dates`
        - `*.citation.edition`
        - `*.citation.contacts` (except `contact.position`)
        - `*.citation.identifiers`
        - `common.online_resource.protocol`
        - `(identification.)data_quality.domain_consistency`
        - `(identification.)data_quality.lineage.statement`
        - `distribution.distributor`
        - `distributor.format` (`format` and `href` only)
        - `distributor.transfer_option`
        - `file_identifier`
        - `hierarchy_level`
        - `identification.abstract`
        - `identification.aggregations`
        - `identification.constraints` (except permissions)
        - `identification.extent` (temporal and bounding box extents only)
        - `identification.graphic_overviews`
        - `identification.maintenance`
        - `identification.purpose`
        - `identification.other_citation_details`
        - `language` (hard-coded)
        - `metadata.date_stamp`
        - `metadata.metadata.standard`
    [5] Unsupported elements:
        - `contact.position`
        - `(identification.)data_quality.lineage.process_step`
        - `(identification.)data_quality.lineage.sources`
        - `distribution.format` (except name and URL)
        - `identification.credit`
        - `identification.constraint.permissions`
        - `identification.extent.geographic.identifier`
        - `identification.extent.vertical`
        - `identification.keywords`
        - `identification.resource_formats`
        - `identification.spatial_representation_type`
        - `identification.spatial_resolution`
        - `identification.series`
        - `identification.status`
        - `identification.supplemental_information`
        - `identification.topics`
        - `metadata.maintenance` (identification only)
    """

    _schema: str = (
        "https://metadata-resources.data.bas.ac.uk/bas-metadata-generator-configuration-schemas/v2/iso-19115-2-v4.json"
    )

    file_identifier: str | None = None
    hierarchy_level: HierarchyLevelCode
    metadata: Metadata
    reference_system_info: ReferenceSystemInfo | None = None
    identification: Identification
    data_quality: DataQuality | None = None
    distribution: list[Distribution] | None = None

    def __post_init__(self) -> None:
        """Process defaults."""
        if self.distribution is None:
            self.distribution = []

    @staticmethod
    def _move_dq_elements(value: dict) -> dict:
        """
        Move any data quality elements out of identification until v5 schema available.

        See https://gitlab.data.bas.ac.uk/uk-pdc/metadata-infrastructure/metadata-library/-/issues/255.
        """
        dq = {}
        if (
            "identification" in value
            and "lineage" in value["identification"]
            and "statement" in value["identification"]["lineage"]
        ):
            dq["lineage"] = value["identification"]["lineage"]
        if "identification" in value and "domain_consistency" in value["identification"]:
            dq["domain_consistency"] = value["identification"]["domain_consistency"]
        if dq:
            value["data_quality"] = dq
        return value

    @classmethod
    def structure(cls: type[TRecord], value: dict) -> "Record":
        """
        Parse Record class from plain types.

        Returns a new class instance with parsed data. Intended to be used as a cattrs structure hook.
        E.g. `converter.register_structure_hook(Record, lambda d, t: Record.structure(d))`
        """
        value_ = deepcopy(value)

        # move any data quality elements out of identification
        # https://gitlab.data.bas.ac.uk/uk-pdc/metadata-infrastructure/metadata-library/-/issues/255
        value_ = cls._move_dq_elements(value_)

        # rename keys
        value_["_schema"] = value_.pop("$schema", None)

        converter = cattrs.Converter()
        converter.register_structure_hook(Metadata, lambda d, t: Metadata.structure(d))
        converter.register_structure_hook(ReferenceSystemInfo, lambda d, t: ReferenceSystemInfo.structure(d))
        converter.register_structure_hook(Identification, lambda d, t: Identification.structure(d))
        converter.register_structure_hook(DataQuality, lambda d, t: DataQuality.structure(d))
        return converter.structure(value_, cls)

    def unstructure(self) -> dict:
        """
        Convert Record to plain types.

        Intended to be used as a cattrs structure hook.
        E.g. `converter.register_unstructure_hook(Record, lambda d: d.unstructure())`
        """
        converter = cattrs.Converter()
        converter.register_unstructure_hook(Metadata, lambda d: d.unstructure())
        converter.register_unstructure_hook(ReferenceSystemInfo, lambda d: d.unstructure())
        converter.register_unstructure_hook(Identification, lambda d: d.unstructure())
        converter.register_unstructure_hook(DataQuality, lambda d: d.unstructure())
        value = clean_dict(converter.unstructure(self))

        # move data quality elements into identification until v5 schema available
        # https://gitlab.data.bas.ac.uk/uk-pdc/metadata-infrastructure/metadata-library/-/issues/255
        if "data_quality" in value:
            value["identification"] = {**value["identification"], **value["data_quality"]}
            del value["data_quality"]

        # rename keys
        value["$schema"] = value.pop("_schema", None)

        return value

    @classmethod
    def loads(cls, value: dict) -> "Record":
        """Create a Record from a dict loaded from a JSON schema instance."""
        converter = cattrs.Converter()
        converter.register_structure_hook(Record, lambda d, t: Record.structure(d))
        return converter.structure(value, cls)

    def dumps(self) -> dict:
        """Create a dict from a Record for a JSON schema instance."""
        converter = cattrs.Converter()
        converter.register_unstructure_hook(Record, lambda d: d.unstructure())
        return converter.unstructure(self)

    @staticmethod
    def _get_resource_contents(file: str) -> dict:
        """Get contents of package resource file."""
        package_ref = "assets_tracking_service.lib.bas_data_catalogue.resources.schemas"
        with (
            resources_as_file(resources_files(package_ref)) as resources_path,
            resources_path.joinpath(file).open() as f,
        ):
            return json.load(f)

    @property
    def _profile_schemas(self) -> list[RecordSchema]:
        """Determine any schemas to validate a record against based on any domain consistency elements."""
        if self.data_quality is None:
            return []

        schemas = []
        for dc in self.data_quality.domain_consistency:
            with contextlib.suppress(KeyError):
                schemas.append(RECORD_SCHEMA_MAPPING[dc.specification.href])

        return schemas

    def _get_validation_schemas(
        self, use_profiles: bool = True, force_schemas: list[RecordSchema] | None = None
    ) -> list[dict]:
        """Load validation schemas."""
        selected_schemas = [RecordSchema.ISO_2_V4]
        if use_profiles:
            selected_schemas.extend(self._profile_schemas)
        if force_schemas is not None:
            selected_schemas = force_schemas

        schemas = []
        for schema in selected_schemas:
            schemas.append(self._get_resource_contents(file=f"{schema.value}.json"))
        return schemas

    def validate(self, use_profiles: bool = True, force_schemas: list[RecordSchema] | None = None) -> None:
        """
        Validate record against JSON Schemas.

        By default, records are validated against the BAS Metadata Library ISO 19115:2003 / 19115-2:2009 v4 schema,
        plus schemas matched from any domain consistency elements. Set `use_profiles = False`to disable.

        Use `force_schemas` to select specific schemas to validating against.

        Failed validation will raise a `RecordInvalidError` exception.

        validate(instance=config, schema=schemas["magic_v1"])
        - the MAGIC Discovery Profile v1 schema
        """
        config = self.dumps()
        schemas = self._get_validation_schemas(use_profiles=use_profiles, force_schemas=force_schemas)

        for schema in schemas:
            try:
                validate(instance=config, schema=schema)
            except ValidationError as e:
                raise RecordInvalidError(e) from e


@dataclass(kw_only=True)
class RecordSummary:
    """
    Summary of a resource within the BAS Data Catalogue / Metadata ecosystem.

    RecordSummaries are a low-level view of key aspects of a resource, using the ISO 19115 information model. They are
    intended to be used where full records are unnecessary or would be impractical - such as describing/listing large
    numbers of resources, or for resources related to a selected resource.

    RecordSummaries can be created independently but are intended to be derived from a Record instance using `loads()`.
    This class does not support loading/dumping record configurations encoded in JSON or XML.

    When derived from a Record, the `graphic_overview_href` is populated from the first graphic overview, if any exist.
    """

    file_identifier: str | None = None
    hierarchy_level: HierarchyLevelCode
    title: str
    abstract: str
    purpose: str | None = None
    edition: str | None = None
    creation: Date
    revision: Date | None = None
    publication: Date | None = None
    graphic_overview_href: str | None = None

    @classmethod
    def loads(cls: type[TRecordSummary], record: Record) -> "RecordSummary":
        """Create a RecordSummary from a Record."""
        graphic = record.identification.graphic_overviews[0].href if record.identification.graphic_overviews else None
        return cls(
            file_identifier=record.file_identifier,
            hierarchy_level=record.hierarchy_level,
            title=record.identification.title,
            abstract=record.identification.abstract,
            purpose=record.identification.purpose,
            edition=record.identification.edition,
            creation=record.identification.dates.creation,
            revision=record.identification.dates.revision,
            publication=record.identification.dates.publication,
            graphic_overview_href=graphic,
        )

    @property
    def purpose_abstract(self) -> str:
        """Purpose, or abstract if not defined."""
        return self.purpose if self.purpose else self.abstract

    @property
    def revision_creation(self) -> Date:
        """Revision date, or creation if not defined."""
        return self.revision if self.revision else self.creation
