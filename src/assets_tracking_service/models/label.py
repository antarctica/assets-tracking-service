from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import TypedDict, Literal, Union

import cattrs


class LabelRelation(Enum):
    """
    Label relation enumeration.

    I.e. How does a label relate to the object or the provider of an object etc.
    """

    SELF = "self"
    PROVIDER = "provider"


@dataclass(kw_only=True, frozen=True)
class Label:
    rel: LabelRelation
    scheme: str
    scheme_uri: str | None = None
    value: Union[str | int | float]
    value_uri: str | None = None
    creation: int = field(default_factory=lambda: int(datetime.now(timezone.utc).timestamp()))
    expiration: int | None = None

    def __post_init__(self):
        """Validate fields."""
        if not isinstance(self.rel, LabelRelation):
            raise ValueError(f"Invalid label relation: [{self.rel}]. It must be a LabelRelation enum member.")

        if not self.scheme:
            raise ValueError(f"Invalid label scheme: [{self.scheme}]. It must not be missing or empty.")

        if self.scheme_uri == "":
            raise ValueError(
                f"Invalid label scheme URI: [{self.scheme_uri}]. "
                f"It must not be an empty string (use `None` if not applicable)."
            )

        if self.value is None or self.value == "":
            raise ValueError(
                f"Invalid label value: [{self.value}] for scheme: '{self.scheme}'. It must not be missing or empty."
            )

        if self.value_uri == "":
            raise ValueError(
                f"Invalid label value URI: [{self.value_uri}]. "
                f"It must not be an empty string (use `None` if not applicable)."
            )

        if self.expiration is not None:
            try:
                datetime.fromtimestamp(self.expiration, tz=timezone.utc)
            except ValueError:
                raise ValueError(f"Invalid label expiration: [{self.expiration}]. It must be a valid timestamp.")

    @property
    def created(self) -> datetime:
        """Label creation."""
        return datetime.fromtimestamp(self.creation, tz=timezone.utc)

    @property
    def expired(self) -> datetime | None:
        """Label expiration"""
        if self.expiration is None:
            return None

        return datetime.fromtimestamp(self.expiration, tz=timezone.utc)

    @property
    def is_expired(self) -> bool:
        """Has label expired?"""
        if self.expired is None:
            return False

        return datetime.now(timezone.utc) >= self.expired


class Labels(list[Label]):
    """Collection of Labels."""

    version = "1"

    def __repr__(self) -> str:
        return f"Labels[v1]({super().__repr__()})"

    def __eq__(self, other):
        return set(self) == set(other)

    @property
    def active(self) -> list[Label]:
        """Non-expired labels."""
        return [label for label in self if not label.expired]

    @property
    def expired(self) -> list[Label]:
        """Expired labels."""
        return [label for label in self if label.expired]

    class LabelsPlain(TypedDict):
        version: Literal["1"]
        values: list[dict[str, str | int | float]]

    @staticmethod
    def _structure_str_int_float(value, _):
        if isinstance(value, str):
            return value
        elif isinstance(value, int):
            return value
        elif isinstance(value, float):
            return value
        else:
            raise TypeError("Label value is not of a supported type.")

    @classmethod
    def structure(cls, data: LabelsPlain) -> "Labels":
        """
        Convert from plain objects.

        Returns a new class instance with parsed data.
        """
        converter = cattrs.Converter()
        converter.register_structure_hook(Union[str, int, float], cls._structure_str_int_float)  # for Label.value
        converter.register_structure_hook(
            cls, lambda d, t: cls([converter.structure(label, Label) for label in d["values"]])
        )

        _labels = converter.structure(data, Labels)
        return cls(_labels)

    def unstructure(self) -> LabelsPlain:
        """Convert to plain objects."""
        converter = cattrs.Converter()
        converter.register_unstructure_hook(
            Labels, lambda d: {"version": self.version, "values": [converter.unstructure(label) for label in d]}
        )

        return converter.unstructure(self)

    def filter_by_scheme(self, scheme: str) -> Label:
        """Filter labels by scheme."""
        for label in self:
            if label.scheme == scheme:
                return label

        raise ValueError(f"No label with scheme: [{scheme}].")
