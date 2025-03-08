from datetime import UTC, date, datetime

import cattrs
import pytest

from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.common import (
    Date,
    Dates,
    Identifier,
    clean_dict,
)
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.identification import (
    Aggregation,
    BoundingBox,
    Constraint,
    Extent,
    ExtentGeographic,
    ExtentTemporal,
    GraphicOverview,
    Identification,
    Maintenance,
    TemporalPeriod,
)
from assets_tracking_service.lib.bas_data_catalogue.models.record.enums import (
    AggregationAssociationCode,
    AggregationInitiativeCode,
    ConstraintRestrictionCode,
    ConstraintTypeCode,
    ContactRoleCode,
    MaintenanceFrequencyCode,
    ProgressCode,
)

MIN_IDENTIFICATION = {
    "title": "x",
    "abstract": "x",
    "dates": Dates(creation=Date(date=datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC))),
}


class TestAggregation:
    """Test Aggregation element."""

    @pytest.mark.parametrize(
        "values",
        [
            {
                "identifier": Identifier(identifier="x", href="x", namespace="x"),
                "association_type": AggregationAssociationCode.CROSS_REFERENCE,
            },
            {
                "identifier": Identifier(identifier="x", href="x", namespace="x"),
                "association_type": AggregationAssociationCode.CROSS_REFERENCE,
                "initiative_type": AggregationInitiativeCode.CAMPAIGN,
            },
        ],
    )
    def test_init(self, values: dict):
        """Can create an Aggregation element from directly assigned properties."""
        aggregation = Aggregation(**values)

        assert aggregation.identifier == values["identifier"]
        assert aggregation.association_type == values["association_type"]

        if "initiative_type" in values:
            assert aggregation.initiative_type == values["initiative_type"]
        else:
            assert aggregation.initiative_type is None


class TestBoundingBox:
    """Test BoundingBox element."""

    def test_init(self):
        """Can create a BoundingBox element from directly assigned properties."""
        values = {
            "west_longitude": 1.0,
            "east_longitude": 2.0,
            "south_latitude": 3.0,
            "north_latitude": 4.0,
        }
        bbox = BoundingBox(**values)

        assert bbox.west_longitude == values["west_longitude"]
        assert bbox.east_longitude == values["east_longitude"]
        assert bbox.south_latitude == values["south_latitude"]
        assert bbox.north_latitude == values["north_latitude"]


class TestConstraint:
    """Test Constraint element."""

    @pytest.mark.parametrize(
        "values",
        [
            {"type": ConstraintTypeCode.ACCESS},
            {
                "type": ConstraintTypeCode.USAGE,
                "restriction_code": ConstraintRestrictionCode.UNRESTRICTED,
                "statement": "x",
                "href": "x",
            },
        ],
    )
    def test_init(self, values: dict):
        """Can create a Constraint element from directly assigned properties."""
        constraint = Constraint(**values)

        assert constraint.type == values["type"]

        if "restriction_code" in values:
            assert constraint.restriction_code == values["restriction_code"]
        else:
            assert constraint.restriction_code is None

        if "statement" in values:
            assert constraint.statement == values["statement"]
        else:
            assert constraint.statement is None

        if "href" in values:
            assert constraint.href == values["href"]
        else:
            assert constraint.href is None


class TestExtentGeographic:
    """Test ExtentGeographic element."""

    def test_init(self):
        """Can create an ExtentGeographic element from directly assigned properties."""
        values = {
            "bounding_box": BoundingBox(west_longitude=1.0, east_longitude=2.0, south_latitude=3.0, north_latitude=4.0)
        }
        geographic = ExtentGeographic(**values)

        assert geographic.bounding_box == values["bounding_box"]


class TestExtentTemporal:
    """Test ExtentTemporal element."""

    @pytest.mark.parametrize(
        "values",
        [
            {"period": TemporalPeriod(start=Date(date=date(2014, 6, 30)), end=Date(date=date(2014, 6, 30)))},
            {},
        ],
    )
    def test_init(self, values: dict):
        """Can create an ExtentGeographic element from directly assigned properties."""
        temporal = ExtentTemporal(**values)

        if "period" in values:
            assert temporal.period == values["period"]
        else:
            assert temporal.period == TemporalPeriod()


class TestExtent:
    """Test Extent element."""

    @pytest.mark.parametrize(
        "values",
        [
            {
                "identifier": "x",
                "geographic": ExtentGeographic(
                    bounding_box=BoundingBox(
                        west_longitude=1.0, east_longitude=2.0, south_latitude=3.0, north_latitude=4.0
                    )
                ),
            },
            {
                "identifier": "x",
                "geographic": ExtentGeographic(
                    bounding_box=BoundingBox(
                        west_longitude=1.0, east_longitude=2.0, south_latitude=3.0, north_latitude=4.0
                    )
                ),
                "temporal": ExtentTemporal(
                    period=TemporalPeriod(start=Date(date=date(2014, 6, 30)), end=Date(date=date(2014, 6, 30)))
                ),
            },
        ],
    )
    def test_init(self, values: dict):
        """Can create an Extent element from directly assigned properties."""
        extent = Extent(**values)

        assert extent.identifier == values["identifier"]
        assert extent.geographic == values["geographic"]

        if "temporal" in values:
            assert extent.temporal == values["temporal"]
        else:
            assert extent.temporal is None


class TestGraphicOverview:
    """Test GraphicOverview element."""

    @pytest.mark.parametrize(
        "values",
        [
            {"identifier": "x", "href": "x", "mime_type": "x"},
            {"identifier": "x", "href": "x", "mime_type": "x", "description": "x"},
        ],
    )
    def test_init(self, values: dict):
        """Can create a GraphicOverview element from directly assigned properties."""
        expected = "x"
        graphic_overview = GraphicOverview(**values)

        assert graphic_overview.identifier == expected
        assert graphic_overview.href == expected
        assert graphic_overview.mime_type == expected
        if "description" in values:
            assert graphic_overview.description == expected


class TestMaintenance:
    """Test Maintenance element."""

    @pytest.mark.parametrize(
        "values",
        [
            {"maintenance_frequency": MaintenanceFrequencyCode.AS_NEEDED, "progress": ProgressCode.ON_GOING},
            {"maintenance_frequency": MaintenanceFrequencyCode.AS_NEEDED},
            {"progress": ProgressCode.ON_GOING},
            {},
        ],
    )
    def test_init(self, values: dict):
        """Can create a Maintenance element from directly assigned properties."""
        maintenance = Maintenance(**values)

        if "maintenance_frequency" in values:
            assert maintenance.maintenance_frequency == values["maintenance_frequency"]
        else:
            assert maintenance.maintenance_frequency is None

        if "progress" in values:
            assert maintenance.progress == values["progress"]
        else:
            assert maintenance.progress is None


class TestTemporalPeriod:
    """Test TemporalPeriod element."""

    @pytest.mark.parametrize(
        "values",
        [
            {"start": Date(date=date(2014, 6, 30)), "end": Date(date=date(2014, 6, 30))},
            {"start": Date(date=date(2014, 6, 30))},
            {"end": Date(date=date(2014, 6, 30))},
            {},
        ],
    )
    def test_init(self, values: dict):
        """Can create a TemporalPeriod element from directly assigned properties."""
        period = TemporalPeriod(**values)

        if "start" in values:
            assert period.start == values["start"]
        else:
            assert period.start is None

        if "end" in values:
            assert period.end == values["end"]
        else:
            assert period.end is None


class TestIdentification:
    """Test Identification element."""

    @pytest.mark.parametrize(
        "values",
        [
            {**MIN_IDENTIFICATION},
            {**MIN_IDENTIFICATION, "purpose": "x"},
            {
                **MIN_IDENTIFICATION,
                "graphic_overviews": [GraphicOverview(identifier="x", href="x", mime_type="x")],
            },
            {
                **MIN_IDENTIFICATION,
                "constraints": [Constraint(type=ConstraintTypeCode.ACCESS)],
            },
            {
                **MIN_IDENTIFICATION,
                "aggregations": [
                    Aggregation(
                        identifier=Identifier(identifier="x", href="x", namespace="x"),
                        association_type=AggregationAssociationCode.CROSS_REFERENCE,
                    )
                ],
            },
            {
                **MIN_IDENTIFICATION,
                "maintenance": Maintenance(maintenance_frequency=MaintenanceFrequencyCode.AS_NEEDED),
            },
            {
                **MIN_IDENTIFICATION,
                "extents": [
                    Extent(
                        identifier="x",
                        geographic=ExtentGeographic(
                            bounding_box=BoundingBox(
                                west_longitude=1.0, east_longitude=2.0, south_latitude=3.0, north_latitude=4.0
                            )
                        ),
                    )
                ],
            },
        ],
    )
    def test_init(self, values: dict):
        """
        Can create an Identification element from directly assigned properties.

        Properties from parent citation class are not re-tested here, except to verify inheritance.
        """
        expected_character = "utf8"
        expected_language = "eng"
        identification = Identification(**values)

        assert identification.title == values["title"]  # inheritance test
        assert identification.abstract == values["abstract"]
        assert identification.character_set == expected_character
        assert identification.language == expected_language

        if "purpose" in values:
            assert identification.purpose == values["purpose"]

        if (
            "graphic_overviews" in values
            and isinstance(values["graphic_overviews"], list)
            and len(values["graphic_overviews"]) > 0
        ):
            assert all(isinstance(graphic, GraphicOverview) for graphic in identification.graphic_overviews)
        else:
            assert identification.graphic_overviews == []

        if "constraints" in values and isinstance(values["constraints"], list) and len(values["constraints"]) > 0:
            assert all(isinstance(constraint, Constraint) for constraint in identification.constraints)
        else:
            assert identification.constraints == []

        if "aggregations" in values and isinstance(values["aggregations"], list) and len(values["aggregations"]) > 0:
            assert all(isinstance(aggregation, Aggregation) for aggregation in identification.aggregations)
        else:
            assert identification.aggregations == []

        if "maintenance" in values:
            assert identification.maintenance == values["maintenance"]
        else:
            assert identification.maintenance == Maintenance()

        if "extents" in values and isinstance(values["extents"], list) and len(values["extents"]) > 0:
            assert all(isinstance(extent, Extent) for extent in identification.extents)
        else:
            assert identification.extents == []

    def test_structure_cattrs(self):
        """Can use Cattrs to create an Identification instance from plain types."""
        expected_date = date(2014, 6, 30)
        expected_enums = {
            "contact_role": ContactRoleCode.POINT_OF_CONTACT,
            "constraint_type": ConstraintTypeCode.USAGE,
            "constraint_code": ConstraintRestrictionCode.LICENSE,
        }
        value = {
            "title": {"value": "x"},
            "dates": {"creation": expected_date.isoformat()},
            "abstract": "x",
            "constraints": [
                {
                    "type": expected_enums["constraint_type"].value,
                    "restriction_code": expected_enums["constraint_code"].value,
                }
            ],
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
                            "start": expected_date.isoformat(),
                            "end": expected_date.isoformat(),
                        }
                    },
                }
            ],
        }
        expected = Identification(
            title="x",
            dates=Dates(creation=Date(date=expected_date)),
            abstract="x",
            constraints=[
                Constraint(type=expected_enums["constraint_type"], restriction_code=expected_enums["constraint_code"]),
            ],
            extents=[
                Extent(
                    identifier="x",
                    geographic=ExtentGeographic(
                        bounding_box=BoundingBox(
                            west_longitude=1.0, east_longitude=1.0, south_latitude=1.0, north_latitude=1.0
                        )
                    ),
                    temporal=ExtentTemporal(
                        period=TemporalPeriod(start=Date(date=expected_date), end=Date(date=expected_date))
                    ),
                )
            ],
        )

        converter = cattrs.Converter()
        converter.register_structure_hook(Identification, lambda d, t: Identification.structure(d))
        result = converter.structure(value, Identification)

        assert result == expected

    def test_unstructure_cattrs(self):
        """Can use Cattrs to convert an Identification instance into plain types."""
        expected_date = date(2014, 6, 30)
        expected_enums = {
            "contact_role": ContactRoleCode.POINT_OF_CONTACT,
            "constraint_type": ConstraintTypeCode.USAGE,
            "constraint_code": ConstraintRestrictionCode.LICENSE,
        }
        value = Identification(
            title="x",
            dates=Dates(creation=Date(date=expected_date)),
            abstract="x",
            constraints=[
                Constraint(type=expected_enums["constraint_type"], restriction_code=expected_enums["constraint_code"]),
            ],
            extents=[
                Extent(
                    identifier="x",
                    geographic=ExtentGeographic(
                        bounding_box=BoundingBox(
                            west_longitude=1.0, east_longitude=1.0, south_latitude=1.0, north_latitude=1.0
                        )
                    ),
                    temporal=ExtentTemporal(
                        period=TemporalPeriod(start=Date(date=expected_date), end=Date(date=expected_date))
                    ),
                )
            ],
        )
        expected = {
            "title": {"value": "x"},
            "dates": {"creation": expected_date.isoformat()},
            "abstract": "x",
            "constraints": [
                {
                    "type": expected_enums["constraint_type"].value,
                    "restriction_code": expected_enums["constraint_code"].value,
                }
            ],
            "character_set": "utf8",
            "language": "eng",
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
                            "start": expected_date.isoformat(),
                            "end": expected_date.isoformat(),
                        }
                    },
                }
            ],
        }

        converter = cattrs.Converter()
        converter.register_unstructure_hook(Identification, lambda d: d.unstructure())
        result = clean_dict(converter.unstructure(value))

        assert result == expected
