from copy import copy
from datetime import datetime, timezone

import pytest
from cattrs import ClassValidationError
from freezegun.api import FrozenDateTimeFactory

from assets_tracking_service.models.label import LabelRelation, Label, Labels
from tests.conftest import LabelsPlain

creation_time = datetime(2012, 6, 10, 14, 30, 20, tzinfo=timezone.utc)


class TestLabel:
    """Test data class."""

    def test_init_minimal(
        self, freezer: FrozenDateTimeFactory, fx_label_rel: LabelRelation, fx_label_scheme: str, fx_label_value: str
    ):
        """Creates a Label."""
        freezer.move_to(creation_time)

        label = Label(rel=fx_label_rel, scheme=fx_label_scheme, value=fx_label_value)

        assert label.rel == fx_label_rel
        assert label.scheme == fx_label_scheme
        assert label.value == fx_label_value
        assert label.creation == int(creation_time.timestamp())
        assert label.created == creation_time

    def test_init_full(
        self,
        fx_label_rel: LabelRelation,
        fx_label_scheme: str,
        fx_label_scheme_uri: str,
        fx_label_value: str,
        fx_label_value_uri: str,
    ):
        """Creates a complete Label."""
        label = Label(
            rel=fx_label_rel,
            scheme=fx_label_scheme,
            scheme_uri=fx_label_scheme_uri,
            value=fx_label_value,
            value_uri=fx_label_value_uri,
            expiration=None,
        )

        # rel, scheme, value, creation, created already tested
        assert label.scheme_uri == fx_label_scheme_uri
        assert label.value_uri == fx_label_value_uri

    def test_init_expired(
        self, fx_label_rel: LabelRelation, fx_label_scheme: str, fx_label_value: str, fx_label_expiry: int
    ):
        """Creates an expired Label."""
        label = Label(rel=fx_label_rel, scheme=fx_label_scheme, value=fx_label_value, expiration=fx_label_expiry)

        assert label.expiration == fx_label_expiry
        assert label.expired == datetime.fromtimestamp(fx_label_expiry, tz=timezone.utc)
        assert label.is_expired is True

    # noinspection PyTypeChecker
    def test_invalid_rel(self, fx_label_scheme: str, fx_label_value: str):
        """Invalid relation triggers error."""
        rel = "invalid"

        with pytest.raises(ValueError, match="Invalid label relation"):
            Label(rel=rel, scheme=fx_label_scheme, value=fx_label_value)

    # noinspection PyArgumentList
    def test_missing_empty_scheme(self, fx_label_rel: LabelRelation, fx_label_value: str):
        """Missing scheme triggers error."""
        with pytest.raises(TypeError, match="missing 1 required keyword-only argument"):
            Label(rel=fx_label_rel, value=fx_label_value)

        with pytest.raises(ValueError, match="Invalid label scheme"):
            Label(rel=fx_label_rel, scheme="", value=fx_label_value)

    @pytest.mark.parametrize("value", [0, 0.0])
    def test_value_valid(self, fx_label_rel: LabelRelation, fx_label_scheme: str, value: int | float):
        """Missing value triggers error."""
        Label(rel=fx_label_rel, scheme=fx_label_scheme, value=value)

    @pytest.mark.parametrize("value", ["", None])
    def test_value_invalid(self, fx_label_rel: LabelRelation, fx_label_scheme: str, value: str | None):
        """Missing value triggers error."""
        with pytest.raises(ValueError, match="Invalid label value"):
            Label(rel=fx_label_rel, scheme=fx_label_scheme, value=value)

    # noinspection PyArgumentList
    def test_missing_value_type(self, fx_label_rel: LabelRelation, fx_label_scheme: str):
        """Missing value triggers error."""
        with pytest.raises(TypeError, match="missing 1 required keyword-only argument"):
            Label(rel=fx_label_rel, scheme=fx_label_scheme)

    def test_empty_scheme_uri(
        self, fx_label_rel: LabelRelation, fx_label_scheme: str, fx_label_value: str, fx_label_value_uri: str
    ):
        """Empty scheme URI triggers error."""

        with pytest.raises(ValueError, match="Invalid label scheme URI"):
            Label(
                rel=fx_label_rel,
                scheme=fx_label_scheme,
                scheme_uri="",
                value=fx_label_value,
                value_uri=fx_label_value_uri,
            )

    def test_empty_value_uri(
        self, fx_label_rel: LabelRelation, fx_label_scheme: str, fx_label_scheme_uri: str, fx_label_value: str
    ):
        """Empty value URI triggers error."""

        with pytest.raises(ValueError, match="Invalid label value URI"):
            Label(
                rel=fx_label_rel,
                scheme=fx_label_scheme,
                scheme_uri=fx_label_scheme_uri,
                value=fx_label_value,
                value_uri="",
            )

    def test_invalid_expiry(self, fx_label_rel: LabelRelation, fx_label_scheme: str, fx_label_value: str):
        """Invalid expiry triggers error."""
        with pytest.raises(ValueError, match="Invalid label expiration"):
            Label(rel=fx_label_rel, scheme=fx_label_scheme, value=fx_label_value, expiration=1_000_000_000_000)

    @pytest.mark.parametrize(
        "expiration,result",
        [
            (None, False),
            (int(datetime(2100, 4, 24, 14, 30, 0, tzinfo=timezone.utc).timestamp()), False),
            (int(datetime(2014, 4, 24, 14, 30, 0, tzinfo=timezone.utc).timestamp()), True),
        ],
    )
    def test_is_expired(
        self,
        fx_label_rel: LabelRelation,
        fx_label_scheme: str,
        fx_label_value: str,
        expiration: int | None,
        result: bool,
    ):
        """Determines Label expiry."""
        label = Label(rel=fx_label_rel, scheme=fx_label_scheme, value=fx_label_value, expiration=expiration)

        assert label.is_expired is result

    def test_eq(
        self, freezer: FrozenDateTimeFactory, fx_label_rel: LabelRelation, fx_label_scheme: str, fx_label_value: str
    ):
        """Equality check."""
        freezer.move_to(creation_time)

        label1 = Label(rel=fx_label_rel, scheme=fx_label_scheme, value=fx_label_value)
        label2 = Label(rel=fx_label_rel, scheme=fx_label_scheme, value=fx_label_value)

        assert label1 == label2


class TestLabels:
    """Test collection class."""

    def test_init_empty(self):
        """Creates an empty set of Labels."""
        labels = Labels()

        assert len(labels) == 0
        assert list(labels) == []
        assert isinstance(labels, list)

    def test_init_single(self, fx_label_minimal: Label):
        """Creates a set of Labels with a single item."""
        labels = Labels([fx_label_minimal])

        assert len(labels) == 1
        assert list(labels) == [fx_label_minimal]
        assert labels == list(labels)
        assert labels[0] == fx_label_minimal

    def test_repr(self, fx_labels_one: Labels):
        """String representation of a Labels set."""
        assert repr(fx_labels_one) == f"Labels[v1]([{repr(fx_labels_one[0])}])"

    def test_active(self, fx_labels_multiple: Labels, fx_label_full: Label, fx_label_expired: Label):
        """Active (non-expired) labels."""
        active_labels = fx_labels_multiple.active

        assert len(active_labels) == 1
        assert fx_label_full in active_labels
        assert fx_label_expired not in active_labels

    def test_expired(self, fx_labels_multiple: Labels, fx_label_full: Label, fx_label_expired: Label):
        """Expired (non-active) labels."""
        expired_labels = fx_labels_multiple.expired

        assert len(expired_labels) == 1
        assert fx_label_full not in expired_labels
        assert fx_label_expired in expired_labels

    def test_structure(self, fx_label_full_plain: LabelsPlain, fx_labels_one: Labels):
        """Loads from plain objects."""
        labels = Labels.structure(data=fx_label_full_plain)

        assert labels == fx_labels_one

    @pytest.mark.cov
    def test_structure_value_types(self, fx_label_full_plain: LabelsPlain):
        test_str = "test"
        test_int = 42
        test_float = 3.14

        data: LabelsPlain = {
            "version": "1",
            "values": [
                copy(fx_label_full_plain["values"][0]),
                copy(fx_label_full_plain["values"][0]),
                copy(fx_label_full_plain["values"][0]),
            ],
        }
        # str
        data["values"][0]["scheme"] = "test_type_str"
        data["values"][0]["value"] = test_str
        # int
        data["values"][1]["scheme"] = "test_type_int"
        data["values"][1]["value"] = test_int
        # float
        data["values"][2]["scheme"] = "test_type_float"
        data["values"][2]["value"] = test_float

        labels = Labels.structure(data=data)

        assert labels[0].value == test_str
        assert labels[1].value == test_int
        assert labels[2].value == test_float

    @pytest.mark.cov
    def test_structure_value_types_invalid(self, fx_label_full_plain: LabelsPlain):
        data: LabelsPlain = {"version": "1", "values": [copy(fx_label_full_plain["values"][0])]}
        data["values"][0]["scheme"] = "test_type_list"
        # noinspection PyTypeChecker
        data["values"][0]["value"] = []

        with pytest.raises(ClassValidationError):
            Labels.structure(data=data)

    def test_unstructure(self, fx_labels_one: Labels, fx_label_full_plain: LabelsPlain):
        """Returns as plain objects."""
        data = fx_labels_one.unstructure()

        assert data == fx_label_full_plain

    def test_filter_by_schema(self, fx_labels_one: Labels):
        """Filter labels based on schema."""
        filtered = fx_labels_one.filter_by_scheme(scheme="skos:prefLabel")

        assert filtered.value == fx_labels_one[0].value

    def test_filter_by_schema_none(self, fx_labels_one: Labels):
        with pytest.raises(ValueError, match="No label with scheme"):
            fx_labels_one.filter_by_scheme(scheme="unknown")

    def test_eq(self, fx_label_minimal: Label, fx_label_expired):
        """Equality check."""
        assert Labels([fx_label_minimal, fx_label_expired]) == Labels([fx_label_expired, fx_label_minimal])
