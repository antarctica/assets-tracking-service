from datetime import UTC, date, datetime

import pytest
from pytest_mock import MockerFixture

from assets_tracking_service.lib.bas_data_catalogue.models.record import (
    Record,
    RecordInvalidError,
    RecordSchema,
    RecordSummary,
)
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.common import (
    Address,
    Citation,
    Contact,
    ContactIdentity,
    Contacts,
    Date,
    Dates,
    Identifier,
    Identifiers,
    OnlineResource,
)
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.data_quality import (
    DataQuality,
    DomainConsistency,
    Lineage,
)
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.identification import (
    BoundingBox,
    Constraint,
    Constraints,
    Extent,
    ExtentGeographic,
    Extents,
    GraphicOverview,
    GraphicOverviews,
    Identification,
    Maintenance,
)
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.metadata import Metadata
from assets_tracking_service.lib.bas_data_catalogue.models.record.enums import (
    ConstraintRestrictionCode,
    ConstraintTypeCode,
    ContactRoleCode,
    HierarchyLevelCode,
    MaintenanceFrequencyCode,
    OnlineResourceFunctionCode,
    ProgressCode,
)


class TestRecord:
    """Test root Record element."""

    def test_init(self):
        """Can create a minimal Record element from directly assigned properties."""
        value = "x"
        expected_schema = "https://metadata-resources.data.bas.ac.uk/bas-metadata-generator-configuration-schemas/v2/iso-19115-2-v4.json"
        date_stamp = datetime(2014, 6, 30, tzinfo=UTC).date()
        hierarchy_level = HierarchyLevelCode.DATASET
        record = Record(
            hierarchy_level=hierarchy_level,
            metadata=Metadata(
                contacts=Contacts(
                    [Contact(organisation=ContactIdentity(name=value), role=[ContactRoleCode.POINT_OF_CONTACT])]
                ),
                date_stamp=date_stamp,
            ),
            identification=Identification(title=value, abstract=value, dates=Dates(creation=Date(date=date_stamp))),
        )

        assert record._schema == expected_schema
        assert record.hierarchy_level == hierarchy_level
        assert record.metadata.contacts[0].organisation.name == value
        assert record.metadata.date_stamp == date_stamp
        assert record.identification.abstract == value

    def test_loads(self):
        """
        Can create a Record from a JSON serialised dict.

        This is not intended as an exhaustive/comprehensive test of all properties, rather it tests any properties
        that require special processing, such as non-standard nesting or enumerations.
        """
        expected_str = "x"
        expected_date = date(2014, 6, 30)
        expected_enums = {
            "hierarchy_level": HierarchyLevelCode.DATASET,
            "contact_role": ContactRoleCode.POINT_OF_CONTACT,
            "constraint_type": ConstraintTypeCode.USAGE,
            "constraint_code": ConstraintRestrictionCode.LICENSE,
        }
        config = {
            "$schema": "https://metadata-resources.data.bas.ac.uk/bas-metadata-generator-configuration-schemas/v2/iso-19115-2-v4.json",
            "hierarchy_level": expected_enums["hierarchy_level"].value,
            "metadata": {
                "contacts": [{"organisation": {"name": expected_str}, "role": [expected_enums["contact_role"].value]}],
                "date_stamp": expected_date.isoformat(),
            },
            "identification": {
                "title": {"value": expected_str},
                "dates": {"creation": expected_date.isoformat()},
                "abstract": expected_str,
                "constraints": [
                    {
                        "type": expected_enums["constraint_type"].value,
                        "restriction_code": expected_enums["constraint_code"].value,
                    }
                ],
                "lineage": {"statement": expected_str},
            },
        }
        record = Record.loads(config)

        assert record._schema is not None
        assert record.identification.title == expected_str  # specially nested property
        assert record.data_quality.lineage.statement == expected_str  # moved property
        assert record.hierarchy_level == expected_enums["hierarchy_level"]  # enum property
        assert record.metadata.contacts[0].role[0] == expected_enums["contact_role"]  # enum property
        assert record.metadata.date_stamp == expected_date  # date property
        assert record.identification.dates.creation.date == expected_date  # date property
        assert record.identification.constraints[0].type == expected_enums["constraint_type"]  # enum property
        assert (
            record.identification.constraints[0].restriction_code == expected_enums["constraint_code"]
        )  # enum property

    def test_dumps(self, fx_lib_record_minimal_iso: Record):
        """
        Can create a dict that can be serialised to JSON from a Record.

        This is not intended as an exhaustive/comprehensive test of all properties, rather it tests any properties
        that require special processing, such as non-standard nesting or enumerations.
        """
        value_str = "x"
        value_schema = "https://metadata-resources.data.bas.ac.uk/bas-metadata-generator-configuration-schemas/v2/iso-19115-2-v4.json"
        value_enums = {
            "hierarchy_level": HierarchyLevelCode.DATASET,
            "contact_role": ContactRoleCode.POINT_OF_CONTACT,
            "constraint_type": ConstraintTypeCode.USAGE,
            "constraint_code": ConstraintRestrictionCode.LICENSE,
        }
        expected = {
            "$schema": value_schema,
            "hierarchy_level": value_enums["hierarchy_level"].value,
            "metadata": {
                "character_set": "utf8",
                "language": "eng",
                "contacts": [{"organisation": {"name": value_str}, "role": [value_enums["contact_role"].value]}],
                "date_stamp": fx_lib_record_minimal_iso.metadata.date_stamp.isoformat(),
                "metadata_standard": {
                    "name": "ISO 19115-2 Geographic Information - Metadata - Part 2: Extensions for Imagery and Gridded Data",
                    "version": "ISO 19115-2:2009(E)",
                },
            },
            "identification": {
                "title": {"value": value_str},
                "abstract": value_str,
                "dates": {"creation": "2014-06-30"},
                "constraints": [
                    {
                        "type": value_enums["constraint_type"].value,
                        "restriction_code": value_enums["constraint_code"].value,
                    }
                ],
                "character_set": "utf8",
                "language": "eng",
            },
        }
        fx_lib_record_minimal_iso.identification.constraints = Constraints(
            [Constraint(type=value_enums["constraint_type"], restriction_code=value_enums["constraint_code"])]
        )
        config = fx_lib_record_minimal_iso.dumps()

        assert config == expected

    def test_validate_min_iso(self):
        """A minimally valid ISO record can be validated."""
        record = Record(
            hierarchy_level=HierarchyLevelCode.DATASET,
            metadata=Metadata(
                contacts=Contacts(
                    [Contact(organisation=ContactIdentity(name="x"), role=[ContactRoleCode.POINT_OF_CONTACT])]
                ),
                date_stamp=datetime(2014, 6, 30, tzinfo=UTC).date(),
            ),
            identification=Identification(
                title="x", abstract="x", dates=Dates(creation=Date(date=datetime(2014, 6, 30, tzinfo=UTC).date()))
            ),
        )

        assert record.validate() is None

    def test_validate_min_magic(self):
        """A minimally valid MAGIC profile record can be validated."""
        record = Record(
            file_identifier="x",
            hierarchy_level=HierarchyLevelCode.DATASET,
            metadata=Metadata(
                contacts=Contacts(
                    [
                        Contact(
                            organisation=ContactIdentity(
                                name="Mapping and Geographic Information Centre, British Antarctic Survey",
                                href="https://ror.org/01rhff309",
                                title="ror",
                            ),
                            phone="+44 (0)1223 221400",
                            email="magic@bas.ac.uk",
                            address=Address(
                                delivery_point="British Antarctic Survey, High Cross, Madingley Road",
                                city="Cambridge",
                                administrative_area="Cambridgeshire",
                                postal_code="CB3 0ET",
                                country="United Kingdom",
                            ),
                            online_resource=OnlineResource(
                                href="https://www.bas.ac.uk/teams/magic",
                                title="Mapping and Geographic Information Centre (MAGIC) - BAS public website",
                                description="General information about the BAS Mapping and Geographic Information Centre (MAGIC) from the British Antarctic Survey (BAS) public website.",
                                function=OnlineResourceFunctionCode.INFORMATION,
                            ),
                            role=[ContactRoleCode.POINT_OF_CONTACT],
                        )
                    ]
                ),
                date_stamp=datetime(2014, 6, 30, tzinfo=UTC).date(),
            ),
            identification=Identification(
                title="x",
                edition="x",
                identifiers=Identifiers(
                    [Identifier(identifier="x", href="https://data.bas.ac.uk/items/x", namespace="data.bas.ac.uk")]
                ),
                abstract="x",
                dates=Dates(creation=Date(date=datetime(2014, 6, 30, tzinfo=UTC).date())),
                contacts=Contacts(
                    [
                        Contact(
                            organisation=ContactIdentity(
                                name="Mapping and Geographic Information Centre, British Antarctic Survey",
                                href="https://ror.org/01rhff309",
                                title="ror",
                            ),
                            phone="+44 (0)1223 221400",
                            email="magic@bas.ac.uk",
                            address=Address(
                                delivery_point="British Antarctic Survey, High Cross, Madingley Road",
                                city="Cambridge",
                                administrative_area="Cambridgeshire",
                                postal_code="CB3 0ET",
                                country="United Kingdom",
                            ),
                            online_resource=OnlineResource(
                                href="https://www.bas.ac.uk/teams/magic",
                                title="Mapping and Geographic Information Centre (MAGIC) - BAS public website",
                                description="General information about the BAS Mapping and Geographic Information Centre (MAGIC) from the British Antarctic Survey (BAS) public website.",
                                function=OnlineResourceFunctionCode.INFORMATION,
                            ),
                            role=[ContactRoleCode.POINT_OF_CONTACT],
                        )
                    ]
                ),
                maintenance=Maintenance(
                    maintenance_frequency=MaintenanceFrequencyCode.AS_NEEDED, progress=ProgressCode.ON_GOING
                ),
                constraints=Constraints(
                    [
                        Constraint(
                            type=ConstraintTypeCode.ACCESS,
                            restriction_code=ConstraintRestrictionCode.UNRESTRICTED,
                            statement="Open Access (Anonymous)",
                        ),
                        Constraint(
                            type=ConstraintTypeCode.USAGE,
                            restriction_code=ConstraintRestrictionCode.LICENSE,
                            href="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
                            statement="This information is licensed under the Open Government Licence v3.0. To view this licence, visit https://www.nationalarchives.gov.uk/doc/open-government-licence/.",
                        ),
                    ]
                ),
                extents=Extents(
                    [
                        Extent(
                            identifier="bounding",
                            geographic=ExtentGeographic(
                                bounding_box=BoundingBox(
                                    west_longitude=0, east_longitude=0, south_latitude=0, north_latitude=0
                                )
                            ),
                        )
                    ]
                ),
            ),
            data_quality=DataQuality(
                lineage=Lineage(statement="x"),
                domain_consistency=[
                    DomainConsistency(
                        specification=Citation(
                            title="British Antarctic Survey (BAS) Mapping and Geographic Information Centre (MAGIC) Discovery Metadata Profile",
                            href="https://metadata-standards.data.bas.ac.uk/profiles/magic-discovery-v1/",
                            dates=Dates(publication=Date(date=date(2024, 11, 1))),
                            edition="1",
                            contacts=Contacts(
                                [
                                    Contact(
                                        organisation=ContactIdentity(
                                            name="Mapping and Geographic Information Centre, British Antarctic Survey",
                                            href="https://ror.org/01rhff309",
                                            title="ror",
                                        ),
                                        phone="+44 (0)1223 221400",
                                        email="magic@bas.ac.uk",
                                        address=Address(
                                            delivery_point="British Antarctic Survey, High Cross, Madingley Road",
                                            city="Cambridge",
                                            administrative_area="Cambridgeshire",
                                            postal_code="CB3 0ET",
                                            country="United Kingdom",
                                        ),
                                        online_resource=OnlineResource(
                                            href="https://www.bas.ac.uk/teams/magic",
                                            title="Mapping and Geographic Information Centre (MAGIC) - BAS public website",
                                            description="General information about the BAS Mapping and Geographic Information Centre (MAGIC) from the British Antarctic Survey (BAS) public website.",
                                            function=OnlineResourceFunctionCode.INFORMATION,
                                        ),
                                        role=[ContactRoleCode.PUBLISHER],
                                    )
                                ]
                            ),
                        ),
                        explanation="Resource within scope of British Antarctic Survey (BAS) Mapping and Geographic Information Centre (MAGIC) Discovery Metadata Profile.",
                        result=True,
                    )
                ],
            ),
        )

        assert record.validate() is None

    def test_validate_invalid_iso(self, mocker: MockerFixture, fx_lib_record_minimal_iso: Record):
        """Can't validate a record that does not comply with the ISO schema."""
        mocker.patch.object(fx_lib_record_minimal_iso, "dumps", return_value={"invalid": "invalid"})

        with pytest.raises(RecordInvalidError):
            fx_lib_record_minimal_iso.validate()

    def test_validate_invalid_profile(self, fx_lib_record_minimal_iso: Record):
        """Can't validate a record that does not comply with a schema inferred from a domain consistency element."""
        fx_lib_record_minimal_iso.data_quality = DataQuality(
            domain_consistency=[
                DomainConsistency(
                    specification=Citation(
                        title="British Antarctic Survey (BAS) Mapping and Geographic Information Centre (MAGIC) Discovery Metadata Profile",
                        href="https://metadata-standards.data.bas.ac.uk/profiles/magic-discovery-v1/",
                        dates=Dates(publication=Date(date=date(2024, 11, 1))),
                        edition="1",
                        contacts=Contacts(
                            [
                                Contact(
                                    organisation=ContactIdentity(
                                        name="Mapping and Geographic Information Centre, British Antarctic Survey",
                                        href="https://ror.org/01rhff309",
                                        title="ror",
                                    ),
                                    phone="+44 (0)1223 221400",
                                    email="magic@bas.ac.uk",
                                    address=Address(
                                        delivery_point="British Antarctic Survey, High Cross, Madingley Road",
                                        city="Cambridge",
                                        administrative_area="Cambridgeshire",
                                        postal_code="CB3 0ET",
                                        country="United Kingdom",
                                    ),
                                    online_resource=OnlineResource(
                                        href="https://www.bas.ac.uk/teams/magic",
                                        title="Mapping and Geographic Information Centre (MAGIC) - BAS public website",
                                        description="General information about the BAS Mapping and Geographic Information Centre (MAGIC) from the British Antarctic Survey (BAS) public website.",
                                        function=OnlineResourceFunctionCode.INFORMATION,
                                    ),
                                    role=[ContactRoleCode.PUBLISHER],
                                )
                            ]
                        ),
                    ),
                    explanation="Resource within scope of British Antarctic Survey (BAS) Mapping and Geographic Information Centre (MAGIC) Discovery Metadata Profile.",
                    result=True,
                )
            ]
        )

        with pytest.raises(RecordInvalidError):
            fx_lib_record_minimal_iso.validate()

    def test_validate_invalid_forced_schemas(self, fx_lib_record_minimal_iso: Record):
        """Can't validate a record that does not comply with a forced set of schemas."""
        with pytest.raises(RecordInvalidError):
            fx_lib_record_minimal_iso.validate(force_schemas=[RecordSchema.MAGIC_V1])

    def test_validate_ignore_profiles(self, fx_lib_record_minimal_iso: Record):
        """Can validate a record that would not normally comply because of a schema indicated via domain consistency."""
        fx_lib_record_minimal_iso.data_quality = DataQuality(
            domain_consistency=[
                DomainConsistency(
                    specification=Citation(
                        title="British Antarctic Survey (BAS) Mapping and Geographic Information Centre (MAGIC) Discovery Metadata Profile",
                        href="https://metadata-standards.data.bas.ac.uk/profiles/magic-discovery-v1/",
                        dates=Dates(publication=Date(date=date(2024, 11, 1))),
                        edition="1",
                        contacts=Contacts(
                            [
                                Contact(
                                    organisation=ContactIdentity(
                                        name="Mapping and Geographic Information Centre, British Antarctic Survey",
                                        href="https://ror.org/01rhff309",
                                        title="ror",
                                    ),
                                    phone="+44 (0)1223 221400",
                                    email="magic@bas.ac.uk",
                                    address=Address(
                                        delivery_point="British Antarctic Survey, High Cross, Madingley Road",
                                        city="Cambridge",
                                        administrative_area="Cambridgeshire",
                                        postal_code="CB3 0ET",
                                        country="United Kingdom",
                                    ),
                                    online_resource=OnlineResource(
                                        href="https://www.bas.ac.uk/teams/magic",
                                        title="Mapping and Geographic Information Centre (MAGIC) - BAS public website",
                                        description="General information about the BAS Mapping and Geographic Information Centre (MAGIC) from the British Antarctic Survey (BAS) public website.",
                                        function=OnlineResourceFunctionCode.INFORMATION,
                                    ),
                                    role=[ContactRoleCode.PUBLISHER],
                                )
                            ]
                        ),
                    ),
                    explanation="Resource within scope of British Antarctic Survey (BAS) Mapping and Geographic Information Centre (MAGIC) Discovery Metadata Profile.",
                    result=True,
                )
            ]
        )

        fx_lib_record_minimal_iso.validate(use_profiles=False)

    @pytest.mark.parametrize(
        ("run", "values"),
        [
            (
                "minimal-iso",
                {
                    "$schema": "https://metadata-resources.data.bas.ac.uk/bas-metadata-generator-configuration-schemas/v2/iso-19115-2-v4.json",
                    "metadata": {
                        "contacts": [{"organisation": {"name": "x"}, "role": ["pointOfContact"]}],
                        "date_stamp": datetime(2014, 6, 30, tzinfo=UTC).date().isoformat(),
                    },
                    "hierarchy_level": "dataset",
                    "identification": {
                        "title": {"value": "x"},
                        "dates": {"creation": "2014-06-30"},
                        "abstract": "x",
                    },
                },
            ),
            (
                "minimal-magic",
                {
                    "$schema": "https://metadata-resources.data.bas.ac.uk/bas-metadata-generator-configuration-schemas/v2/iso-19115-2-v4.json",
                    "file_identifier": "x",
                    "hierarchy_level": "dataset",
                    "metadata": {
                        "character_set": "utf8",
                        "contacts": [
                            {
                                "address": {
                                    "administrative_area": "Cambridgeshire",
                                    "city": "Cambridge",
                                    "country": "United Kingdom",
                                    "delivery_point": "British Antarctic Survey, High Cross, Madingley Road",
                                    "postal_code": "CB3 0ET",
                                },
                                "email": "magic@bas.ac.uk",
                                "online_resource": {
                                    "description": "General information about the BAS Mapping and Geographic Information Centre (MAGIC) from the British Antarctic Survey (BAS) public website.",
                                    "function": "information",
                                    "href": "https://www.bas.ac.uk/teams/magic",
                                    "title": "Mapping and Geographic Information Centre (MAGIC) - BAS public website",
                                },
                                "organisation": {
                                    "href": "https://ror.org/01rhff309",
                                    "name": "Mapping and Geographic Information Centre, British Antarctic Survey",
                                    "title": "ror",
                                },
                                "phone": "+44 (0)1223 221400",
                                "role": ["pointOfContact"],
                            }
                        ],
                        "date_stamp": "2014-06-30",
                        "language": "eng",
                        "metadata_standard": {
                            "name": "ISO 19115-2 Geographic Information - Metadata - Part 2: Extensions for Imagery and Gridded Data",
                            "version": "ISO 19115-2:2009(E)",
                        },
                    },
                    "identification": {
                        "abstract": "x",
                        "character_set": "utf8",
                        "constraints": [
                            {
                                "restriction_code": "unrestricted",
                                "statement": "Open Access (Anonymous)",
                                "type": "access",
                            },
                            {
                                "href": "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
                                "restriction_code": "license",
                                "statement": "This information is licensed under the Open Government Licence v3.0. To view this licence, visit https://www.nationalarchives.gov.uk/doc/open-government-licence/.",
                                "type": "usage",
                            },
                        ],
                        "contacts": [
                            {
                                "address": {
                                    "administrative_area": "Cambridgeshire",
                                    "city": "Cambridge",
                                    "country": "United Kingdom",
                                    "delivery_point": "British Antarctic Survey, High Cross, Madingley Road",
                                    "postal_code": "CB3 0ET",
                                },
                                "email": "magic@bas.ac.uk",
                                "online_resource": {
                                    "description": "General information about the BAS Mapping and Geographic Information Centre (MAGIC) from the British Antarctic Survey (BAS) public website.",
                                    "function": "information",
                                    "href": "https://www.bas.ac.uk/teams/magic",
                                    "title": "Mapping and Geographic Information Centre (MAGIC) - BAS public website",
                                },
                                "organisation": {
                                    "href": "https://ror.org/01rhff309",
                                    "name": "Mapping and Geographic Information Centre, British Antarctic Survey",
                                    "title": "ror",
                                },
                                "phone": "+44 (0)1223 221400",
                                "role": ["pointOfContact"],
                            }
                        ],
                        "dates": {"creation": "2014-06-30"},
                        "domain_consistency": [
                            {
                                "specification": {
                                    "title": {
                                        "value": "British Antarctic Survey (BAS) Mapping and Geographic Information Centre (MAGIC) Discovery Metadata Profile",
                                        "href": "https://metadata-standards.data.bas.ac.uk/profiles/magic-discovery-v1/",
                                    },
                                    "dates": {"publication": "2024-11-01"},
                                    "edition": "1",
                                    "contact": {
                                        "organisation": {
                                            "name": "Mapping and Geographic Information Centre, British Antarctic Survey",
                                            "href": "https://ror.org/01rhff309",
                                            "title": "ror",
                                        },
                                        "phone": "+44 (0)1223 221400",
                                        "address": {
                                            "delivery_point": "British Antarctic Survey, High Cross, Madingley Road",
                                            "city": "Cambridge",
                                            "administrative_area": "Cambridgeshire",
                                            "postal_code": "CB3 0ET",
                                            "country": "United Kingdom",
                                        },
                                        "email": "magic@bas.ac.uk",
                                        "online_resource": {
                                            "href": "https://www.bas.ac.uk/teams/magic",
                                            "title": "Mapping and Geographic Information Centre (MAGIC) - BAS public website",
                                            "description": "General information about the BAS Mapping and Geographic Information Centre (MAGIC) from the British Antarctic Survey (BAS) public website.",
                                            "function": "information",
                                        },
                                        "role": ["publisher"],
                                    },
                                },
                                "explanation": "Resource within scope of British Antarctic Survey (BAS) Mapping and Geographic Information Centre (MAGIC) Discovery Metadata Profile.",
                                "result": True,
                            }
                        ],
                        "edition": "x",
                        "extents": [
                            {
                                "geographic": {
                                    "bounding_box": {
                                        "east_longitude": 0,
                                        "north_latitude": 0,
                                        "south_latitude": 0,
                                        "west_longitude": 0,
                                    }
                                },
                                "identifier": "bounding",
                            }
                        ],
                        "identifiers": [
                            {"href": "https://data.bas.ac.uk/items/x", "identifier": "x", "namespace": "data.bas.ac.uk"}
                        ],
                        "language": "eng",
                        "lineage": {"statement": "x"},
                        "maintenance": {"maintenance_frequency": "asNeeded", "progress": "onGoing"},
                        "title": {"value": "x"},
                    },
                },
            ),
            (
                "complete",
                {
                    "$schema": "https://metadata-resources.data.bas.ac.uk/bas-metadata-generator-configuration-schemas/v2/iso-19115-2-v4.json",
                    "file_identifier": "x",
                    "hierarchy_level": "dataset",
                    "metadata": {
                        "character_set": "utf8",
                        "language": "eng",
                        "contacts": [
                            {
                                "organisation": {"name": "x", "title": "x", "href": "x"},
                                "individual": {"name": "x", "title": "x", "href": "x"},
                                "phone": "x",
                                "address": {
                                    "delivery_point": "x",
                                    "city": "x",
                                    "administrative_area": "x",
                                    "postal_code": "x",
                                    "country": "x",
                                },
                                "email": "x",
                                "online_resource": {
                                    "href": "x",
                                    "protocol": "x",
                                    "title": "x",
                                    "description": "x",
                                    "function": "download",
                                },
                                "role": ["pointOfContact"],
                            }
                        ],
                        "date_stamp": datetime(2014, 6, 30, tzinfo=UTC).date().isoformat(),
                        "metadata_standard": {
                            "name": "ISO 19115-2 Geographic Information - Metadata - Part 2: Extensions for Imagery and Gridded Data",
                            "version": "ISO 19115-2:2009(E)",
                        },
                    },
                    "reference_system_info": {
                        "code": {"value": "x", "href": "x"},
                        "version": "x",
                        "authority": {
                            "title": {"value": "x", "href": "x"},
                            "dates": {
                                "creation": "2014-06-30",
                                "publication": "2014-06-30",
                                "revision": "2014-06-30",
                                "adopted": "2014-06-30",
                                "deprecated": "2014-06-30",
                                "distribution": "2014-06-30",
                                "expiry": "2014-06-30",
                                "inForce": "2014-06-30",
                                "lastRevision": "2014-06-30",
                                "lastUpdate": "2014-06-30",
                                "nextUpdate": "2014-06-30",
                                "released": "2014-06-30",
                                "superseded": "2014-06-30",
                                "unavailable": "2014-06-30",
                                "validityBegins": "2014-06-30",
                                "validityExpires": "2014-06-30",
                            },
                            "edition": "x",
                            "identifiers": [{"identifier": "x", "href": "x", "namespace": "x"}],
                            "other_citation_details": "x",
                            "contact": {
                                "organisation": {"name": "x", "title": "x", "href": "x"},
                                "individual": {"name": "x", "title": "x", "href": "x"},
                                "phone": "x",
                                "address": {
                                    "delivery_point": "x",
                                    "city": "x",
                                    "administrative_area": "x",
                                    "postal_code": "x",
                                    "country": "x",
                                },
                                "email": "x",
                                "online_resource": {
                                    "href": "x",
                                    "protocol": "x",
                                    "title": "x",
                                    "description": "x",
                                    "function": "download",
                                },
                                "role": ["pointOfContact"],
                            },
                        },
                    },
                    "identification": {
                        "title": {"value": "x"},
                        "dates": {
                            "creation": "2014-06-30",
                            "publication": "2014-06-30",
                            "revision": "2014-06-30",
                            "adopted": "2014-06-30",
                            "deprecated": "2014-06-30",
                            "distribution": "2014-06-30",
                            "expiry": "2014-06-30",
                            "inForce": "2014-06-30",
                            "lastRevision": "2014-06-30",
                            "lastUpdate": "2014-06-30",
                            "nextUpdate": "2014-06-30",
                            "released": "2014-06-30",
                            "superseded": "2014-06-30",
                            "unavailable": "2014-06-30",
                            "validityBegins": "2014-06-30",
                            "validityExpires": "2014-06-30",
                        },
                        "edition": "x",
                        "identifiers": [{"identifier": "x", "href": "x", "namespace": "x"}],
                        "other_citation_details": "x",
                        "abstract": "x",
                        "purpose": "x",
                        "contacts": [
                            {
                                "organisation": {"name": "x", "title": "x", "href": "x"},
                                "individual": {"name": "x", "title": "x", "href": "x"},
                                "phone": "x",
                                "address": {
                                    "delivery_point": "x",
                                    "city": "x",
                                    "administrative_area": "x",
                                    "postal_code": "x",
                                    "country": "x",
                                },
                                "email": "x",
                                "online_resource": {
                                    "href": "x",
                                    "protocol": "x",
                                    "title": "x",
                                    "description": "x",
                                    "function": "download",
                                },
                                "role": ["pointOfContact"],
                            }
                        ],
                        "graphic_overviews": [{"identifier": "x", "description": "x", "href": "x", "mime_type": "x"}],
                        "constraints": [
                            {"type": "usage", "restriction_code": "license", "statement": "x", "href": "x"}
                        ],
                        "aggregations": [
                            {
                                "identifier": {"identifier": "x", "href": "x", "namespace": "x"},
                                "association_type": "crossReference",
                                "initiative_type": "campaign",
                            }
                        ],
                        "maintenance": {"maintenance_frequency": "asNeeded", "progress": "completed"},
                        "language": "eng",
                        "character_set": "utf8",
                        "extents": [
                            {
                                "identifier": "x",
                                "geographic": {
                                    "bounding_box": {
                                        "west_longitude": 1.0,
                                        "east_longitude": 1.0,
                                        "south_latitude": 1.0,
                                        "north_latitude": 1.0,
                                    }
                                },
                                "temporal": {
                                    "period": {
                                        "start": "2014-06-30",
                                        "end": "2014-06-30",
                                    }
                                },
                            }
                        ],
                        "lineage": {"statement": "x"},
                        "domain_consistency": [
                            {
                                "specification": {
                                    "title": {"value": "x", "href": "x"},
                                    "dates": {
                                        "creation": "2014-06-30",
                                        "publication": "2014-06-30",
                                        "revision": "2014-06-30",
                                        "adopted": "2014-06-30",
                                        "deprecated": "2014-06-30",
                                        "distribution": "2014-06-30",
                                        "expiry": "2014-06-30",
                                        "inForce": "2014-06-30",
                                        "lastRevision": "2014-06-30",
                                        "lastUpdate": "2014-06-30",
                                        "nextUpdate": "2014-06-30",
                                        "released": "2014-06-30",
                                        "superseded": "2014-06-30",
                                        "unavailable": "2014-06-30",
                                        "validityBegins": "2014-06-30",
                                        "validityExpires": "2014-06-30",
                                    },
                                    "edition": "x",
                                    "identifiers": [{"identifier": "x", "href": "x", "namespace": "x"}],
                                    "other_citation_details": "x",
                                    "contact": {
                                        "organisation": {"name": "x", "title": "x", "href": "x"},
                                        "individual": {"name": "x", "title": "x", "href": "x"},
                                        "phone": "x",
                                        "address": {
                                            "delivery_point": "x",
                                            "city": "x",
                                            "administrative_area": "x",
                                            "postal_code": "x",
                                            "country": "x",
                                        },
                                        "email": "x",
                                        "online_resource": {
                                            "href": "x",
                                            "protocol": "x",
                                            "title": "x",
                                            "description": "x",
                                            "function": "download",
                                        },
                                        "role": ["pointOfContact"],
                                    },
                                },
                                "explanation": "x",
                                "result": True,
                            }
                        ],
                    },
                    "distribution": [
                        {
                            "distributor": {
                                "organisation": {"name": "x", "title": "x", "href": "x"},
                                "individual": {"name": "x", "title": "x", "href": "x"},
                                "phone": "x",
                                "address": {
                                    "delivery_point": "x",
                                    "city": "x",
                                    "administrative_area": "x",
                                    "postal_code": "x",
                                    "country": "x",
                                },
                                "email": "x",
                                "online_resource": {
                                    "href": "x",
                                    "protocol": "x",
                                    "title": "x",
                                    "description": "x",
                                    "function": "download",
                                },
                                "role": ["distributor"],
                            },
                            "format": {"format": "x", "href": "x"},
                            "transfer_option": {
                                "size": {"unit": "x", "magnitude": 1.0},
                                "online_resource": {
                                    "href": "x",
                                    "protocol": "x",
                                    "title": "x",
                                    "description": "x",
                                    "function": "download",
                                },
                            },
                        }
                    ],
                },
            ),
        ],
    )
    def test_loop(self, run: str, values: dict):
        """
        Can convert a JSON serialised dict to a Record and back again.

        Tests various configurations from minimal to complete.
        """
        record = Record.loads(values)
        result = record.dumps()
        expected = values

        if run == "minimal-iso" or run == "minimal-magic":
            # add properties that will be set by default to allow for accurate comparison
            expected["metadata"]["character_set"] = "utf8"
            expected["metadata"]["language"] = "eng"
            expected["metadata"]["metadata_standard"] = {
                "name": "ISO 19115-2 Geographic Information - Metadata - Part 2: Extensions for Imagery and Gridded Data",
                "version": "ISO 19115-2:2009(E)",
            }
            expected["identification"]["character_set"] = "utf8"
            expected["identification"]["language"] = "eng"

        assert result == expected


class TestRecordSummary:
    """Test root RecordSummary element."""

    def test_init(self):
        """Can create a minimal RecordSummary element from directly assigned properties."""
        expected = "x"
        expected_hierarchy_level = HierarchyLevelCode.DATASET
        expected_date = Date(date=datetime(2014, 6, 30, tzinfo=UTC).date())

        record_summary = RecordSummary(
            hierarchy_level=expected_hierarchy_level,
            title=expected,
            abstract=expected,
            creation=expected_date,
        )

        assert record_summary.hierarchy_level == expected_hierarchy_level
        assert record_summary.title == expected
        assert record_summary.abstract == expected
        assert record_summary.creation == expected_date

        assert record_summary.edition is None
        assert record_summary.purpose is None
        assert record_summary.publication is None
        assert record_summary.revision is None
        assert record_summary.graphic_overview_href is None

    def test_complete(self):
        """Can create a RecordSummary element with all optional properties directly assigned."""
        expected = "x"
        expected_hierarchy_level = HierarchyLevelCode.DATASET
        expected_date = Date(date=datetime(2014, 6, 30, tzinfo=UTC).date())

        record_summary = RecordSummary(
            hierarchy_level=expected_hierarchy_level,
            title=expected,
            abstract=expected,
            creation=expected_date,
            edition=expected,
            purpose=expected,
            publication=expected_date,
            revision=expected_date,
            graphic_overview_href=expected,
        )

        assert record_summary.edition is expected
        assert record_summary.purpose is expected
        assert record_summary.publication is expected_date
        assert record_summary.revision is expected_date
        assert record_summary.graphic_overview_href is expected

    def test_loads(self):
        """Can create a RecordSummary from a Record."""
        expected = "x"
        expected_hierarchy_level = HierarchyLevelCode.DATASET
        expected_time = datetime(2014, 6, 30, 14, 30, 45, tzinfo=UTC)
        record = Record(
            hierarchy_level=expected_hierarchy_level,
            metadata=Metadata(
                contacts=Contacts(
                    [Contact(organisation=ContactIdentity(name="x"), role=[ContactRoleCode.POINT_OF_CONTACT])]
                ),
                date_stamp=datetime(2014, 6, 30, tzinfo=UTC).date(),
            ),
            identification=Identification(
                title=expected,
                abstract=expected,
                dates=Dates(
                    creation=Date(date=expected_time.date()),
                    revision=Date(date=expected_time),
                    publication=Date(date=expected_time),
                ),
                edition=expected,
                purpose=expected,
                graphic_overviews=GraphicOverviews([GraphicOverview(identifier="x", href=expected, mime_type="x")]),
            ),
        )

        record_summary = RecordSummary.loads(record)

        assert isinstance(record_summary, RecordSummary)
        assert record_summary.hierarchy_level == expected_hierarchy_level
        assert record_summary.title == expected
        assert record_summary.abstract == expected
        assert record_summary.creation == Date(date=expected_time.date())
        assert record_summary.edition == expected
        assert record_summary.purpose == expected
        assert record_summary.publication == Date(date=expected_time)
        assert record_summary.revision == Date(date=expected_time)
        assert record_summary.graphic_overview_href is expected

    @pytest.mark.parametrize(("purpose", "expected"), [("x", "x"), (None, "y")])
    def test_purpose_abstract(self, purpose: str | None, expected: str):
        """Can get either purpose or abstract depending on which values are set."""
        abstract = "y"

        record_summary = RecordSummary(
            hierarchy_level=HierarchyLevelCode.DATASET,
            title="x",
            abstract=abstract,
            creation=Date(date=datetime(2014, 6, 30, tzinfo=UTC).date()),
            purpose=purpose,
        )

        assert record_summary.purpose_abstract == expected

    revision_date = Date(date=datetime(2015, 7, 20, tzinfo=UTC).date())

    @pytest.mark.parametrize(
        ("revision", "expected"),
        [(revision_date, revision_date), (None, Date(date=datetime(2014, 6, 30, tzinfo=UTC).date()))],
    )
    def test_revision_creation(self, revision: Date | None, expected: Date):
        """Can get either revision or creation date depending on which values are set."""
        record_summary = RecordSummary(
            hierarchy_level=HierarchyLevelCode.DATASET,
            title="x",
            abstract="x",
            creation=Date(date=datetime(2014, 6, 30, tzinfo=UTC).date()),
            revision=revision,
        )

        assert record_summary.revision_creation == expected
