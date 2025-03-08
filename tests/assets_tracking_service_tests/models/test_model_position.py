from datetime import datetime
from uuid import UUID
from zoneinfo import ZoneInfo

import pytest
from psycopg.sql import SQL
from shapely import Point
from ulid import ULID

from assets_tracking_service.models.asset import Asset
from assets_tracking_service.models.label import Labels
from assets_tracking_service.models.position import Position, PositionNew, PositionsClient


class TestPositionNew:
    """Test data class in initial state."""

    def test_init(self, fx_asset: Asset, fx_position_time: datetime, fx_position_geom_3d: Point):
        """Creates a PositionNew."""
        position = PositionNew(asset_id=fx_asset.id, time=fx_position_time, geom=fx_position_geom_3d, labels=Labels([]))

        assert position.asset_id == fx_asset.id
        assert position.time == fx_position_time
        assert position.geom == fx_position_geom_3d
        assert len(position.labels) == 0

    def test_no_timezone(self, fx_asset: Asset, fx_position_geom_3d: Point):
        """Invalid timezone triggers error."""
        time = datetime.now()  # noqa: DTZ005

        with pytest.raises(ValueError, match=r"Invalid timezone: \[None\]. It must be UTC."):
            PositionNew(asset_id=fx_asset.id, time=time, geom=fx_position_geom_3d, labels=Labels([]))

    def test_invalid_timezone(self, fx_asset: Asset, fx_position_geom_3d: Point):
        """Invalid timezone triggers error."""
        time = datetime.now(tz=ZoneInfo("America/Lima"))

        with pytest.raises(ValueError, match=r"Invalid timezone: \[America/Lima\]. It must be UTC."):
            PositionNew(asset_id=fx_asset.id, time=time, geom=fx_position_geom_3d, labels=Labels([]))

    def test_invalid_position_lon(self, fx_asset: Asset, fx_position_time: datetime):
        """Invalid longitude triggers error."""
        geom = Point(200, 0)

        with pytest.raises(ValueError, match=r"Invalid longitude value: \[200.0\]. It must be between -180 and 180."):
            PositionNew(asset_id=fx_asset.id, time=fx_position_time, geom=geom, labels=Labels([]))

    def test_invalid_position_lat(self, fx_asset: Asset, fx_position_time: datetime):
        """Invalid latitude triggers error."""
        geom = Point(0, 100)

        with pytest.raises(ValueError, match=r"Invalid latitude value: \[100.0\]. It must be between -90 and 90."):
            PositionNew(asset_id=fx_asset.id, time=fx_position_time, geom=geom, labels=Labels([]))

    def test_invalid_velocity(self, fx_asset: Asset, fx_position_time: datetime, fx_position_geom_3d: Point):
        """Invalid velocity triggers error."""
        with pytest.raises(ValueError, match=r"Invalid velocity value"):
            PositionNew(
                asset_id=fx_asset.id, time=fx_position_time, geom=fx_position_geom_3d, velocity=-1, labels=Labels([])
            )

    def test_invalid_heading(self, fx_asset: Asset, fx_position_time: datetime, fx_position_geom_3d: Point):
        """Invalid heading triggers error."""
        with pytest.raises(ValueError, match=r"Invalid heading value"):
            PositionNew(
                asset_id=fx_asset.id, time=fx_position_time, geom=fx_position_geom_3d, heading=-1, labels=Labels([])
            )

        with pytest.raises(ValueError, match=r"Invalid heading value"):
            PositionNew(
                asset_id=fx_asset.id, time=fx_position_time, geom=fx_position_geom_3d, heading=361, labels=Labels([])
            )

    def test_invalid_labels(self, fx_asset: Asset, fx_position_time: datetime, fx_position_geom_3d: Point):
        """Non-Labels object triggers error."""
        with pytest.raises(TypeError, match="Invalid labels: It must be a Labels object."):
            # noinspection PyTypeChecker
            PositionNew(asset_id=fx_asset.id, time=fx_position_time, geom=fx_position_geom_3d, labels="invalid")

    def test_geom_dimensions_2d(self, fx_position_new_minimal_2d: PositionNew):
        """Position with 2D geometry."""
        assert fx_position_new_minimal_2d.geom_dimensions == 2

    def test_geom_dimensions_3d(self, fx_position_new_minimal: PositionNew):
        """Position with 3D geometry."""
        assert fx_position_new_minimal.geom_dimensions == 3

    def test_to_db_dict_minimal_3d(self, fx_position_new_minimal: PositionNew):
        """Converts Position with 3D geometry to a database dict."""
        expected = {
            "asset_id": UUID(bytes=fx_position_new_minimal.asset_id.bytes),
            "geom": "POINT Z (0 0 0)",
            "geom_dimensions": 3,
            "heading": None,
            "time_utc": fx_position_new_minimal.time,
            "velocity_ms": None,
        }
        expected_labels = {"version": "1", "values": []}

        result = fx_position_new_minimal.to_db_dict()
        # Jsonb is not hashable, so we need to compare the values separately
        labels = result.pop("labels")

        assert result == expected
        assert labels.obj == expected_labels

    def test_to_db_dict_minimal_2d(self, fx_position_new_minimal_2d: PositionNew):
        """Converts Position with 2D geometry to a database dict."""
        expected = {
            "asset_id": UUID(bytes=fx_position_new_minimal_2d.asset_id.bytes),
            "geom": "POINT Z (0 0 0)",
            "geom_dimensions": 2,
            "heading": None,
            "time_utc": fx_position_new_minimal_2d.time,
            "velocity_ms": None,
        }
        expected_labels = {"version": "1", "values": []}

        result = fx_position_new_minimal_2d.to_db_dict()
        # Jsonb is not hashable, so we need to compare the values separately
        labels = result.pop("labels")

        assert result == expected
        assert labels.obj == expected_labels


class TestPosition:
    """Test data class in existing state."""

    def test_init(
        self,
        fx_position_id: ULID,
        fx_asset: Asset,
        fx_position_time: datetime,
        fx_position_geom_3d: Point,
        fx_position_minimal: Position,
    ):
        """Creates a Position."""
        position = Position(
            id=fx_position_id, asset_id=fx_asset.id, time=fx_position_time, geom=fx_position_geom_3d, labels=Labels([])
        )

        assert position == fx_position_minimal

    def test_repr(self, fx_position_minimal: Position):
        """String representation of a Position."""
        # noinspection SpellCheckingInspection
        assert (
            repr(fx_position_minimal) == "Position(id=<ULID('01HYN10Z7GJKSFXSK5VQ5XWHJJ')>, "
            "time=datetime.datetime(2014, 4, 24, 14, 30, tzinfo=datetime.timezone.utc)), geom=<POINT Z (0 0 0)>"
        )

    def test_from_db_dict_3d(
        self,
        fx_position_id: ULID,
        fx_asset: Asset,
        fx_position_time: datetime,
        fx_position_geom_3d: Point,
        fx_position_minimal: Position,
    ):
        """Makes Position from a database dict with 3D geometry."""
        data = {
            "id": str(fx_position_id),
            "asset_id": str(fx_asset.id),
            "time_utc": fx_position_time,
            "geom": fx_position_geom_3d.wkt,
            "geom_dimensions": 3,
            "velocity_ms": None,
            "heading": None,
            "labels": {"version": "1", "values": []},
        }

        position = Position.from_db_dict(data)

        assert position == fx_position_minimal

    def test_from_db_dict_2d(
        self,
        fx_position_id: ULID,
        fx_asset: Asset,
        fx_position_time: datetime,
        fx_position_geom_3d: Point,
        fx_position_minimal_2d: Position,
    ):
        """Makes Position from a database dict with 3D geometry that should be interpreted as 2D."""
        data = {
            "id": str(fx_position_id),
            "asset_id": str(fx_asset.id),
            "time_utc": fx_position_time,
            "geom": fx_position_geom_3d.wkt,
            "geom_dimensions": 2,
            "velocity_ms": None,
            "heading": None,
            "labels": {"version": "1", "values": []},
        }

        position = Position.from_db_dict(data)

        assert position == fx_position_minimal_2d


class TestPositionsClient:
    """
    Unit tests for a data/resource client.

    Unit tests with mocks for PositionsClient are skipped, as they are largely wrappers around the database, and so
    would add very little value.
    """

    pass


# noinspection SqlResolve
class TestPositionsClientIntegration:
    """Integration tests for a data/resource client."""

    def test_positions_client_add(
        self, fx_positions_client_empty: PositionsClient, fx_position_new_minimal: PositionNew
    ):
        """Test storing a Position."""
        fx_positions_client_empty.add(position=fx_position_new_minimal)

        # verify table isn't empty
        result = fx_positions_client_empty._db.get_query_result(SQL("""SELECT * FROM public.position;"""))
        assert len(result) > 0
