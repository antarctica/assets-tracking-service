import json

import pytest

from assets_tracking_service.lib.bas_data_catalogue.models.item import (
    AccessType,
    Constraint,
    ConstraintAmbiguityError,
    ConstraintNotFoundError,
    Graphic,
    GraphicLabelAmbiguityError,
    GraphicLabelNotFoundError,
    Identifier,
    IdentifierNamespaceAmbiguityError,
    IdentifierNamespaceNotFoundError,
    ItemBase,
    Licence,
)
from assets_tracking_service.lib.bas_data_catalogue.models.record import (
    Record,
)
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.common import Identifier as RIdentifier
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.data_quality import DataQuality, Lineage
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.identification import (
    Constraint as RConstraint,
)
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.identification import GraphicOverview
from assets_tracking_service.lib.bas_data_catalogue.models.record.enums import (
    ConstraintRestrictionCode,
    ConstraintTypeCode,
)


class TestItemBase:
    """Test base item representation."""

    def test_init(self, fx_lib_record_minimal_iso: Record):
        """Creates an ItemBase."""
        item = ItemBase(fx_lib_record_minimal_iso)

        assert item._record == fx_lib_record_minimal_iso

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("", []),
            ("invalid", []),
            (
                f"#{json.dumps([{'scheme': 'x', 'schemeVersion': 'x'}])}",
                [],
            ),
            (
                f"#{json.dumps([{'scheme': 'ms_graph', 'schemeVersion': '1', 'directoryId': 'x', 'objectId': 'x'}])}",
                [],
            ),
            (
                f"#{json.dumps([{'scheme': 'ms_graph', 'schemeVersion': '1', 'directoryId': 'b311db95-32ad-438f-a101-7ba061712a4e', 'objectId': '6fa3b48c-393c-455f-b787-c006f839b51f'}])}",
                [AccessType.BAS_ALL],
            ),
        ],
    )
    def test_parse_permissions(self, fx_lib_record_minimal_iso: Record, value: str, expected: list[AccessType]):
        """Can parse permissions string."""
        item = ItemBase(fx_lib_record_minimal_iso)

        result = item._parse_permissions(value)

        assert result == expected

    def test_resource_id(self, fx_lib_record_minimal_iso: Record):
        """Get resource/file identifier."""
        expected = "x"
        item = ItemBase(fx_lib_record_minimal_iso)
        item._record.file_identifier = expected

        assert item.resource_id == expected

    def test_title_raw(self, fx_lib_record_minimal_iso: Record):
        """Raw title."""
        item = ItemBase(fx_lib_record_minimal_iso)

        assert item.title_raw == "x"

    def test_title_md(self, fx_lib_record_minimal_iso: Record):
        """Title with Markdown formatting."""
        item = ItemBase(fx_lib_record_minimal_iso)

        assert item.title_md == "# x"

    @pytest.mark.parametrize(("value", "expected"), [("x", "x"), ("_x_", "x")])
    def test_title_plain(self, fx_lib_record_minimal_iso: Record, value: str, expected: str):
        """Title without Markdown formatting."""
        fx_lib_record_minimal_iso.identification.title = value
        item = ItemBase(fx_lib_record_minimal_iso)

        assert item.title_plain == expected

    @pytest.mark.parametrize("expected", ["x", None])
    def test_summary_raw(self, fx_lib_record_minimal_iso: Record, expected: str | None):
        """Optional raw Summary (purpose)."""
        fx_lib_record_minimal_iso.identification.purpose = expected
        item = ItemBase(fx_lib_record_minimal_iso)

        assert item.summary_raw == expected

    @pytest.mark.parametrize("expected", ["_x_", None])
    def test_summary_md(self, fx_lib_record_minimal_iso: Record, expected: str | None):
        """Optional summary (purpose) with Markdown formatting."""
        fx_lib_record_minimal_iso.identification.purpose = expected
        item = ItemBase(fx_lib_record_minimal_iso)

        assert item.summary_md == expected

    @pytest.mark.parametrize(("value", "expected"), [("x", "x"), ("_x_", "x")])
    def test_summary_plain(self, fx_lib_record_minimal_iso: Record, value: str, expected: str):
        """Optional summary (purpose) without Markdown formatting."""
        fx_lib_record_minimal_iso.identification.purpose = value
        item = ItemBase(fx_lib_record_minimal_iso)

        assert item.summary_plain == expected

    def test_abstract_raw(self, fx_lib_record_minimal_iso: Record):
        """Raw Abstract."""
        expected = "x"
        fx_lib_record_minimal_iso.identification.abstract = expected
        item = ItemBase(fx_lib_record_minimal_iso)

        assert item.abstract_raw == expected

    def test_abstract_md(self, fx_lib_record_minimal_iso: Record):
        """Abstract with Markdown formatting if present."""
        expected = "x"
        fx_lib_record_minimal_iso.identification.abstract = expected
        item = ItemBase(fx_lib_record_minimal_iso)

        assert item.abstract_md == expected

    def test_abstract_html(self, fx_lib_record_minimal_iso: Record):
        """Abstract with Markdown formatting, if present, encoded as HTML."""
        value = "_x_"
        expected = "<p><em>x</em></p>"
        fx_lib_record_minimal_iso.identification.abstract = value
        item = ItemBase(fx_lib_record_minimal_iso)

        assert item.abstract_html == expected

    @pytest.mark.parametrize("expected", ["x", None])
    def test_lineage_raw(self, fx_lib_record_minimal_iso: Record, expected: str | None):
        """Raw lineage statement."""
        if expected is not None:
            fx_lib_record_minimal_iso.data_quality = DataQuality(lineage=Lineage(statement=expected))
        item = ItemBase(fx_lib_record_minimal_iso)

        assert item.lineage_raw == expected

    @pytest.mark.parametrize("expected", ["_x_", None])
    def test_lineage_md(self, fx_lib_record_minimal_iso: Record, expected: str | None):
        """Lineage statement with Markdown formatting if present."""
        if expected is not None:
            fx_lib_record_minimal_iso.data_quality = DataQuality(lineage=Lineage(statement=expected))
        item = ItemBase(fx_lib_record_minimal_iso)

        assert item.lineage_md == expected

    @pytest.mark.parametrize(("value", "expected"), [("x", "<p>x</p>"), ("_x_", "<p><em>x</em></p>"), (None, None)])
    def test_lineage_html(self, fx_lib_record_minimal_iso: Record, value: str | None, expected: str | None):
        """Lineage statement with Markdown formatting, if present, encoded as HTML."""
        if expected is not None:
            fx_lib_record_minimal_iso.data_quality = DataQuality(lineage=Lineage(statement=expected))
        item = ItemBase(fx_lib_record_minimal_iso)

        assert item.lineage_html == expected

    @pytest.mark.parametrize("expected", ["x", None])
    def test_citation_raw(self, fx_lib_record_minimal_iso: Record, expected: str | None):
        """Raw citation."""
        fx_lib_record_minimal_iso.identification.other_citation_details = expected
        item = ItemBase(fx_lib_record_minimal_iso)

        assert item.citation_raw == expected

    @pytest.mark.parametrize("expected", ["_x_", None])
    def test_citation_md(self, fx_lib_record_minimal_iso: Record, expected: str | None):
        """Citation with Markdown formatting if present."""
        fx_lib_record_minimal_iso.identification.other_citation_details = expected
        item = ItemBase(fx_lib_record_minimal_iso)

        assert item.citation_md == expected

    @pytest.mark.parametrize(("value", "expected"), [("x", "<p>x</p>"), ("_x_", "<p><em>x</em></p>"), (None, None)])
    def test_citation_html(self, fx_lib_record_minimal_iso: Record, value: str | None, expected: str | None):
        """
        Citation with Markdown formatting, if present, encoded as HTML.

        Parameters used to test handling of optional value.
        """
        fx_lib_record_minimal_iso.identification.other_citation_details = value
        item = ItemBase(fx_lib_record_minimal_iso)

        if value is None:
            assert item.citation_html is None
        if value is not None:
            assert item.citation_html.startswith("<p>")
            assert item.citation_html.endswith("</p>")
        if value == "_Markdown_":
            assert "<em>Markdown</em>" in item.citation_html

    @pytest.mark.parametrize(
        ("values", "expected"),
        [
            (
                [GraphicOverview(identifier="x", description="x", href="x", mime_type="x")],
                Graphic(GraphicOverview(identifier="x", description="x", href="x", mime_type="x")),
            ),
            (None, []),
        ],
    )
    def test_graphic_overviews(
        self, fx_lib_record_minimal_iso: Record, values: list[GraphicOverview] | None, expected: list[Graphic]
    ):
        """List of any graphic overviews."""
        if values is not None:
            fx_lib_record_minimal_iso.identification.graphic_overviews = values
        item = ItemBase(fx_lib_record_minimal_iso)

        result = item.graphic_overviews
        if values is not None:
            assert len(result) > 0
            assert result[0].label == values[0].identifier
            assert result[0].description == values[0].description
            assert result[0].src == values[0].href
            assert result[0].media_type == values[0].mime_type
        else:
            assert len(result) == 0
        assert all(isinstance(item, Graphic) for item in result)

    def test_get_graphic_overview(self, fx_lib_record_minimal_iso: Record):
        """Can get a specific graphic overview by label."""
        value = GraphicOverview(identifier="x", description="x", href="x", mime_type="x")
        fx_lib_record_minimal_iso.identification.graphic_overviews = [value]
        expected = Graphic(value)
        item = ItemBase(fx_lib_record_minimal_iso)

        result = item.get_graphic_overview(label=expected.label)
        assert result == expected

    def test_get_graphic_overview_unknown(self, fx_lib_record_minimal_iso: Record):
        """Can't get a graphic overview for unknown label/identifier."""
        value = GraphicOverview(identifier="x", description="x", href="x", mime_type="x")
        fx_lib_record_minimal_iso.identification.graphic_overviews = [value]
        item = ItemBase(fx_lib_record_minimal_iso)

        with pytest.raises(GraphicLabelNotFoundError):
            item.get_graphic_overview(label="invalid")

    def test_get_graphic_overview_ambiguous(self, fx_lib_record_minimal_iso: Record):
        """Can't get a graphic overview where label/identifier matches multiple options."""
        value = GraphicOverview(identifier="x", description="x", href="x", mime_type="x")
        fx_lib_record_minimal_iso.identification.graphic_overviews = [value, value]
        item = ItemBase(fx_lib_record_minimal_iso)

        with pytest.raises(GraphicLabelAmbiguityError):
            item.get_graphic_overview(label=value.identifier)

    @pytest.mark.parametrize(
        ("values", "expected"),
        [
            (
                [RConstraint(type=ConstraintTypeCode.ACCESS)],
                Constraint(RConstraint(type=ConstraintTypeCode.ACCESS)),
            ),
            (None, []),
        ],
    )
    def test_constraints(
        self, fx_lib_record_minimal_iso: Record, values: list[RConstraint] | None, expected: list[Constraint]
    ):
        """Can list any constraints."""
        if values is not None:
            fx_lib_record_minimal_iso.identification.constraints = values
        item = ItemBase(fx_lib_record_minimal_iso)

        result = item.constraints
        if values is not None:
            assert len(result) > 0
        else:
            assert len(result) == 0
        assert all(isinstance(item, Constraint) for item in result)

    @pytest.mark.parametrize(
        "values",
        [
            [RConstraint(type=ConstraintTypeCode.ACCESS)],
            [
                RConstraint(type=ConstraintTypeCode.USAGE, restriction_code=ConstraintRestrictionCode.LICENSE),
            ],
        ],
    )
    def test_get_constraint(self, fx_lib_record_minimal_iso: Record, values: list[Constraint]):
        """Can get a specific constraint by type and optionally code."""
        expected = Constraint(values[0])
        fx_lib_record_minimal_iso.identification.constraints = values
        item = ItemBase(fx_lib_record_minimal_iso)

        result = item.get_constraint(type_=expected.type, code=expected.restriction_code)
        assert result == expected

    @pytest.mark.parametrize(
        ("type_", "code"),
        [
            (ConstraintTypeCode.ACCESS, None),
            (ConstraintTypeCode.USAGE, ConstraintRestrictionCode.LICENSE),
        ],
    )
    def test_get_constraint_unknown(
        self, fx_lib_record_minimal_iso: Record, type_: ConstraintTypeCode, code: ConstraintRestrictionCode | None
    ):
        """
        Can't get a constraint for unknown type and optionally code.

        Normally we'd look for an invalid value but constraint types and codes are enums so will already error.
        """
        fx_lib_record_minimal_iso.identification.constraints = [RConstraint(type=ConstraintTypeCode.USAGE)]
        item = ItemBase(fx_lib_record_minimal_iso)

        with pytest.raises(ConstraintNotFoundError):
            item.get_constraint(type_=type_, code=code)

    @pytest.mark.parametrize(
        ("type_", "code"),
        [
            (ConstraintTypeCode.ACCESS, None),
            (ConstraintTypeCode.USAGE, ConstraintRestrictionCode.LICENSE),
        ],
    )
    def test_get_constraint_ambiguous(
        self, fx_lib_record_minimal_iso: Record, type_: ConstraintTypeCode, code: ConstraintRestrictionCode | None
    ):
        """Can't get a constraint where type and optionally code match multiple options."""
        fx_lib_record_minimal_iso.identification.constraints = [
            RConstraint(type=ConstraintTypeCode.ACCESS),
            RConstraint(type=ConstraintTypeCode.ACCESS),
            RConstraint(type=ConstraintTypeCode.USAGE, restriction_code=ConstraintRestrictionCode.LICENSE),
            RConstraint(type=ConstraintTypeCode.USAGE, restriction_code=ConstraintRestrictionCode.LICENSE),
        ]
        item = ItemBase(fx_lib_record_minimal_iso)

        with pytest.raises(ConstraintAmbiguityError):
            item.get_constraint(type_=type_, code=code)

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (Constraint(RConstraint(type=ConstraintTypeCode.ACCESS)), AccessType.NONE),
            (
                Constraint(
                    RConstraint(type=ConstraintTypeCode.ACCESS, restriction_code=ConstraintRestrictionCode.UNRESTRICTED)
                ),
                AccessType.PUBLIC,
            ),
            (
                Constraint(
                    RConstraint(
                        type=ConstraintTypeCode.ACCESS,
                        restriction_code=ConstraintRestrictionCode.RESTRICTED,
                        href='%5B{"scheme"%3A"ms_graph"%2C"schemeVersion"%3A"1"%2C"directoryId"%3A"b311db95-32ad-438f-a101-7ba061712a4e"%2C"objectId"%3A"6fa3b48c-393c-455f-b787-c006f839b51f"}%5D',
                    )
                ),
                AccessType.BAS_ALL,
            ),
            (None, AccessType.NONE),
        ],
    )
    def test_access(self, fx_lib_record_minimal_iso: Record, value: Constraint | None, expected: AccessType):
        """Can get optional access constraint and any associated permissions."""
        if value is not None:
            fx_lib_record_minimal_iso.identification.constraints = [value]
        item = ItemBase(fx_lib_record_minimal_iso)

        assert item.access == expected

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (
                Constraint(
                    RConstraint(
                        type=ConstraintTypeCode.USAGE,
                        restriction_code=ConstraintRestrictionCode.LICENSE,
                        href="x",
                        statement="x",
                    )
                ),
                Licence(href="x", statement="x"),
            ),
            (None, None),
        ],
    )
    def test_licence(self, fx_lib_record_minimal_iso: Record, value: Constraint | None, expected: Licence | None):
        """Can get optional licence usage constraint."""
        if value is not None:
            fx_lib_record_minimal_iso.identification.constraints = [value]
        item = ItemBase(fx_lib_record_minimal_iso)

        if expected is not None:
            assert isinstance(item.licence, Licence)
            assert item.licence.href == expected.href
            assert item.licence.statement == expected.statement
        else:
            assert item.licence is None

    @pytest.mark.parametrize(
        ("values", "expected"),
        [
            (
                [RIdentifier(identifier="x", href="x", namespace="x")],
                Identifier(RIdentifier(identifier="x", href="x", namespace="x")),
            ),
            (None, []),
        ],
    )
    def test_identifiers(
        self, fx_lib_record_minimal_iso: Record, values: list[RIdentifier] | None, expected: list[Identifier]
    ):
        """List of any identifiers."""
        if values is not None:
            fx_lib_record_minimal_iso.identification.identifiers = values
        item = ItemBase(fx_lib_record_minimal_iso)

        result = item.identifiers
        if values is not None:
            assert len(result) > 0
        else:
            assert len(result) == 0
        assert all(isinstance(item, Identifier) for item in result)

    def test_get_identifier(self, fx_lib_record_minimal_iso: Record):
        """Can get a specific identifier overview by namespace."""
        values = [RIdentifier(identifier="x", href="x", namespace="x")]
        expected = Identifier(values[0])
        fx_lib_record_minimal_iso.identification.identifiers = values
        item = ItemBase(fx_lib_record_minimal_iso)

        result = item.get_identifier(namespace=expected.namespace)
        assert result == expected

    def test_get_identifier_unknown(self, fx_lib_record_minimal_iso: Record):
        """Can't get an identifier for unknown namespace."""
        fx_lib_record_minimal_iso.identification.identifiers = [RIdentifier(identifier="x", href="x", namespace="x")]
        item = ItemBase(fx_lib_record_minimal_iso)

        with pytest.raises(IdentifierNamespaceNotFoundError):
            item.get_identifier(namespace="invalid")

    def test_get_identifier_ambiguous(self, fx_lib_record_minimal_iso: Record):
        """Can't get an identifier where namespace matches multiple options."""
        value = RIdentifier(identifier="x", href="x", namespace="x")
        fx_lib_record_minimal_iso.identification.identifiers = [value, value]
        item = ItemBase(fx_lib_record_minimal_iso)

        with pytest.raises(IdentifierNamespaceAmbiguityError):
            item.get_identifier(namespace=value.namespace)
