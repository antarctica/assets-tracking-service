from copy import copy
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal
from uuid import UUID

import cattrs
from cattrs.gen import make_dict_unstructure_fn, make_dict_structure_fn
from psycopg.types.json import Jsonb
from shapely import Point, wkt
from ulid import ULID, parse as ulid_parse

from assets_tracking_service.db import DatabaseClient
from assets_tracking_service.models.label import Labels


@dataclass(kw_only=True)
class PositionNew:
    asset_id: ULID
    time: datetime
    geom: Point
    velocity: float | None = None
    heading: float | None = None
    labels: Labels

    @property
    def geom_dimensions(self) -> Literal[2, 3]:
        """Return the number of dimensions in the geometry."""
        return 3 if self.geom.has_z else 2

    def __post_init__(self):
        """Validate fields."""
        if self.time.tzinfo is None or self.time.tzinfo != timezone.utc:
            raise ValueError(f"Invalid timezone: [{self.time.tzinfo}]. It must be UTC.")

        if not (-180 <= self.geom.x <= 180):
            raise ValueError(f"Invalid longitude value: [{self.geom.x}]. It must be between -180 and 180.")

        if not (-90 <= self.geom.y <= 90):
            raise ValueError(f"Invalid latitude value: [{self.geom.y}]. It must be between -90 and 90.")

        if self.velocity is not None and self.velocity < 0:
            raise ValueError(f"Invalid velocity value: [{self.velocity}]. It must be greater than or equal to 0.")

        if self.heading is not None and not (0 <= self.heading < 360):
            raise ValueError(f"Invalid heading value: [{self.heading}]. It must be between 0 and 360.")

        if not isinstance(self.labels, Labels):
            raise ValueError("Invalid labels: It must be a Labels object.")

    def to_db_dict(self) -> dict:
        """Convert to a dictionary suitable for database insertion."""
        geom_dimensions = copy(self.geom_dimensions)

        # DB geom must be 3D
        if geom_dimensions == 2:
            self.geom = Point(self.geom.x, self.geom.y, 0)

        converter = cattrs.Converter()
        converter.register_unstructure_hook(ULID, lambda d: UUID(bytes=d.bytes))
        converter.register_unstructure_hook(Point, lambda d: d.wkt)
        converter.register_unstructure_hook(Labels, lambda d: Jsonb(self.labels.unstructure()))
        converter.register_unstructure_hook(
            PositionNew,
            make_dict_unstructure_fn(
                PositionNew,
                converter,
                time=cattrs.override(rename="time_utc"),
                velocity=cattrs.override(rename="velocity_ms"),
            ),
        )
        data = converter.unstructure(self)

        # inject geom_dimensions property as cattrs doesn't handle properties
        # https://github.com/python-attrs/cattrs/issues/102
        # not using unstructure hook as they don't recurse so would clobber other hooks
        data["geom_dimensions"] = geom_dimensions

        # restore original geom
        if geom_dimensions == 2:
            self.geom = Point(self.geom.x, self.geom.y)

        return data


@dataclass(kw_only=True)
class Position(PositionNew):
    id: ULID

    @classmethod
    def from_db_dict(cls, data: dict) -> "Position":
        """Convert from a dictionary retrieved from the database."""
        geom_dimensions: Literal[2, 3] = data.pop("geom_dimensions")

        converter = cattrs.Converter()
        converter.register_structure_hook(ULID, lambda d, t: ulid_parse(d))
        converter.register_structure_hook(datetime, lambda d, t: d.astimezone(timezone.utc))
        converter.register_structure_hook(Point, lambda d, t: wkt.loads(d))
        converter.register_structure_hook(Labels, lambda d, t: Labels.structure(d))
        converter.register_structure_hook(
            cls,
            make_dict_structure_fn(
                cls, converter, time=cattrs.override(rename="time_utc"), velocity=cattrs.override(rename="velocity_ms")
            ),
        )
        position = converter.structure(data, cls)

        # correct geom if 2D
        if geom_dimensions == 2:
            position.geom = Point(position.geom.x, position.geom.y)

        return position

    def __repr__(self) -> str:
        return f"Position(id={repr(self.id)}, time={repr(self.time)}), geom={repr(self.geom)}"


class PositionsClient:
    """Client for managing Position objects."""

    _schema = "public"
    _table_view = "position"

    def __init__(self, db_client: DatabaseClient) -> None:
        """Create client using injected database client."""
        self._db = db_client

    def add(self, position: PositionNew) -> None:
        """Persist a new position in the database."""
        self._db.insert_dict(schema=self._schema, table_view=self._table_view, data=position.to_db_dict())
        self._db.commit()
