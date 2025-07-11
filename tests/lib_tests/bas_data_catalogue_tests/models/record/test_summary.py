from datetime import UTC, datetime

import pytest

from assets_tracking_service.lib.bas_data_catalogue.models.record import HierarchyLevelCode, Record
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.common import Date, Identifier
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.identification import (
    Aggregation,
    Aggregations,
    Constraint,
    Constraints,
    GraphicOverview,
    GraphicOverviews,
)
from assets_tracking_service.lib.bas_data_catalogue.models.record.enums import (
    AggregationAssociationCode,
    ConstraintRestrictionCode,
    ConstraintTypeCode,
)
from assets_tracking_service.lib.bas_data_catalogue.models.record.summary import RecordSummary


class TestRecordSummary:
    """Test root RecordSummary element."""

    def test_init(self):
        """Can create a minimal RecordSummary element from directly assigned properties."""
        expected = "x"
        expected_hierarchy_level = HierarchyLevelCode.DATASET
        expected_date = Date(date=datetime(2014, 6, 30, tzinfo=UTC).date())

        record_summary = RecordSummary(
            hierarchy_level=expected_hierarchy_level,
            date_stamp=expected_date.date,
            title=expected,
            creation=expected_date,
        )

        assert record_summary.hierarchy_level == expected_hierarchy_level
        assert record_summary.date_stamp == expected_date.date
        assert record_summary.title == expected
        assert record_summary.creation == expected_date

        assert record_summary.edition is None
        assert record_summary.purpose is None
        assert record_summary.publication is None
        assert record_summary.revision is None
        assert isinstance(record_summary.graphic_overviews, GraphicOverviews)
        assert isinstance(record_summary.constraints, Constraints)
        assert isinstance(record_summary.aggregations, Aggregations)
        assert len(record_summary.graphic_overviews) == 0
        assert len(record_summary.constraints) == 0
        assert len(record_summary.aggregations) == 0

    def test_complete(self):
        """Can create a RecordSummary element with all optional properties directly assigned."""
        expected = "x"
        expected_hierarchy_level = HierarchyLevelCode.DATASET
        expected_date = Date(date=datetime(2014, 6, 30, tzinfo=UTC).date())
        expected_graphic = GraphicOverview(identifier="x", href="x", mime_type="x")
        expected_constraint = Constraint(
            type=ConstraintTypeCode.ACCESS, restriction_code=ConstraintRestrictionCode.UNRESTRICTED
        )
        expected_aggregation = Aggregation(
            identifier=Identifier(identifier="x", namespace="x"),
            association_type=AggregationAssociationCode.CROSS_REFERENCE,
        )

        record_summary = RecordSummary(
            hierarchy_level=expected_hierarchy_level,
            date_stamp=expected_date.date,
            title=expected,
            creation=expected_date,
            edition=expected,
            purpose=expected,
            publication=expected_date,
            revision=expected_date,
            graphic_overviews=GraphicOverviews([expected_graphic]),
            constraints=Constraints([expected_constraint]),
            aggregations=Aggregations([expected_aggregation]),
        )

        assert record_summary.edition is expected
        assert record_summary.purpose is expected
        assert record_summary.publication is expected_date
        assert record_summary.revision is expected_date
        assert record_summary.graphic_overviews[0] == expected_graphic
        assert record_summary.constraints[0] == expected_constraint
        assert record_summary.aggregations[0] == expected_aggregation

    def test_loads_json_config(self):
        """Can create a RecordSummary from a dict loaded from JSON."""
        expected = {
            "file_identifier": "59be7b09-4024-48e2-b7b3-6a0799196400",
            "hierarchy_level": "dataset",
            "date_stamp": "2025-05-18",
            "title": "x",
            "purpose": "x",
            "edition": "x",
            "creation": "2014",
            "revision": "2014-06-30",
            "publication": "2014-06-30T14:30:45+00:00",
            "graphic_overviews": [{"identifier": "x", "href": "x", "mime_type": "x"}],
            "constraints": [{"type": "access", "restriction_code": "unrestricted"}],
            "aggregations": [
                {"identifier": {"identifier": "x", "href": "x", "namespace": "x"}, "association_type": "crossReference"}
            ],
        }

        record_summary = RecordSummary.loads(expected)

        assert isinstance(record_summary, RecordSummary)
        assert record_summary.hierarchy_level.value == expected["hierarchy_level"]
        assert record_summary.title == "x"
        assert record_summary.creation.date.year == 2014
        assert record_summary.edition == "x"
        assert record_summary.purpose == "x"
        assert record_summary.publication.date.year == 2014
        assert record_summary.revision.date.year == 2014
        assert len(record_summary.graphic_overviews) > 0
        assert len(record_summary.constraints) > 0
        assert len(record_summary.aggregations) > 0

    def test_loads_record(self, fx_lib_record_minimal_iso: Record):
        """Can create a RecordSummary from a Record."""
        expected = "x"
        expected_hierarchy_level = HierarchyLevelCode.DATASET
        expected_time = datetime(2014, 6, 30, 14, 30, 45, tzinfo=UTC)
        expected_graphic = GraphicOverview(identifier="x", href="x", mime_type="x")
        expected_constraint = Constraint(
            type=ConstraintTypeCode.ACCESS, restriction_code=ConstraintRestrictionCode.UNRESTRICTED
        )
        expected_aggregation = Aggregation(
            identifier=Identifier(identifier="x", namespace="x"),
            association_type=AggregationAssociationCode.CROSS_REFERENCE,
        )

        fx_lib_record_minimal_iso.identification.edition = expected
        fx_lib_record_minimal_iso.identification.purpose = expected
        fx_lib_record_minimal_iso.identification.dates.publication = Date(date=expected_time)
        fx_lib_record_minimal_iso.identification.dates.revision = Date(date=expected_time)
        fx_lib_record_minimal_iso.identification.graphic_overviews = GraphicOverviews([expected_graphic])
        fx_lib_record_minimal_iso.identification.constraints = Constraints([expected_constraint])
        fx_lib_record_minimal_iso.identification.aggregations = Aggregations([expected_aggregation])

        record_summary = RecordSummary.loads(fx_lib_record_minimal_iso)

        assert isinstance(record_summary, RecordSummary)
        assert record_summary.hierarchy_level == expected_hierarchy_level
        assert record_summary.title == expected
        assert record_summary.creation == Date(date=expected_time.date())
        assert record_summary.edition == expected
        assert record_summary.purpose == expected
        assert record_summary.publication == Date(date=expected_time)
        assert record_summary.revision == Date(date=expected_time)
        assert record_summary.graphic_overviews[0] == expected_graphic
        assert record_summary.constraints[0] == expected_constraint
        assert record_summary.aggregations[0] == expected_aggregation

    @pytest.mark.parametrize(
        ("revision", "expected"),
        [
            (Date(date=datetime(2015, 7, 20, tzinfo=UTC).date()), Date(date=datetime(2015, 7, 20, tzinfo=UTC).date())),
            (None, Date(date=datetime(2014, 6, 30, tzinfo=UTC).date())),
        ],
    )
    def test_revision_creation(self, revision: Date | None, expected: Date):
        """Can get either revision or creation date depending on which values are set."""
        date = Date(date=datetime(2014, 6, 30, tzinfo=UTC).date())

        record_summary = RecordSummary(
            hierarchy_level=HierarchyLevelCode.DATASET,
            title="x",
            date_stamp=date.date,
            creation=date,
            revision=revision,
        )

        assert record_summary.revision_creation == expected
