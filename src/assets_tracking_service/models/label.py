from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Literal, Self, TypedDict, TypeVar, Union

import cattrs

T = TypeVar("T", bound="Labels")


class LabelRelation(Enum):
    """
    Label relation enumeration.

    I.e. How does a label relate to the object or the provider of an object etc.
    """

    SELF = "self"
    PROVIDER = "provider"


@dataclass(kw_only=True, frozen=True)
class Label:
    """
    A Label.

    Represents the Label entity from data model.
    """

    rel: LabelRelation
    scheme: str
    scheme_uri: str | None = None
    value: str | int | float
    value_uri: str | None = None
    creation: int = field(default_factory=lambda: int(datetime.now(UTC).timestamp()))
    expiration: int | None = None

    def __post_init__(self: Self) -> None:
        """Validate fields."""
        if not isinstance(self.rel, LabelRelation):
            msg = f"Invalid label relation: [{self.rel}]. It must be a LabelRelation enum member."
            raise TypeError(msg)

        if not self.scheme:
            msg = f"Invalid label scheme: [{self.scheme}]. It must not be missing or empty."
            raise ValueError(msg)

        if self.scheme_uri == "":
            msg = f"Invalid label scheme URI: [{self.scheme_uri}]. It must not be an empty string (use `None` if not applicable)."
            raise ValueError(msg)

        if self.value is None or self.value == "":
            msg = f"Invalid label value: [{self.value}] for scheme: '{self.scheme}'. It must not be missing or empty."
            raise ValueError(msg)

        if self.value_uri == "":
            msg = f"Invalid label value URI: [{self.value_uri}]. It must not be an empty string (use `None` if not applicable)."
            raise ValueError(msg)

        if self.expiration is not None:
            try:
                datetime.fromtimestamp(self.expiration, tz=UTC)
            except ValueError as e:
                msg = f"Invalid label expiration: [{self.expiration}]. It must be a valid timestamp."
                raise ValueError(msg) from e

    @property
    def created(self: Self) -> datetime:
        """Label creation."""
        return datetime.fromtimestamp(self.creation, tz=UTC)

    @property
    def expired(self: Self) -> datetime | None:
        """Label expiration."""
        if self.expiration is None:
            return None

        return datetime.fromtimestamp(self.expiration, tz=UTC)

    @property
    def is_expired(self: Self) -> bool:
        """Has label expired?"""  # noqa: D400
        if self.expired is None:
            return False

        return datetime.now(UTC) >= self.expired


class Labels(list[Label]):
    """Collection of Labels."""

    version = "1"

    def __repr__(self: Self) -> str:
        """String representation."""  # noqa: D401
        return f"Labels[v1]({super().__repr__()})"

    def __eq__(self: Self, other: "Labels") -> bool:
        """Equality check."""
        return set(self) == set(other)

    @property
    def active(self: Self) -> list[Label]:
        """Non-expired labels."""
        return [label for label in self if not label.expired]

    @property
    def expired(self: Self) -> list[Label]:
        """Expired labels."""
        return [label for label in self if label.expired]

    class LabelsPlain(TypedDict):
        """Types for `unstructure`."""

        version: Literal["1"]
        values: list[dict[str, str | int | float]]

    @staticmethod
    def _structure_str_int_float(value: str | int | float, _) -> str | int | float:  # noqa: ANN001
        if isinstance(value, str | int | float):
            return value

        msg = "Label value is not of a supported type."
        raise TypeError(msg)

    @classmethod
    def structure(cls: type[T], data: LabelsPlain) -> "Labels":
        """
        Convert from plain objects.

        Returns a new class instance with parsed data.
        """
        converter = cattrs.Converter()
        converter.register_structure_hook(Union[str, int, float], cls._structure_str_int_float)  # noqa: UP007 for Label.value
        converter.register_structure_hook(
            cls, lambda d, t: cls([converter.structure(label, Label) for label in d["values"]])
        )

        _labels = converter.structure(data, Labels)
        return cls(_labels)

    def unstructure(self: Self) -> LabelsPlain:
        """Convert to plain objects."""
        converter = cattrs.Converter()
        converter.register_unstructure_hook(
            Labels, lambda d: {"version": self.version, "values": [converter.unstructure(label) for label in d]}
        )
        return converter.unstructure(self)

    def filter_by_scheme(self: Self, scheme: str) -> Label:
        """Filter labels by scheme."""
        for label in self:
            if label.scheme == scheme:
                return label

        msg = f"No label with scheme: [{scheme}]."
        raise ValueError(msg)
