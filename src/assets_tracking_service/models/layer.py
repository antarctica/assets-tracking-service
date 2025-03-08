import re
from dataclasses import dataclass
from datetime import UTC, datetime
from logging import Logger
from typing import TypeVar

import cattrs
from psycopg.sql import SQL, Identifier

from assets_tracking_service.db import DatabaseClient
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.identification import Extent
from assets_tracking_service.lib.bas_data_catalogue.models.record.presets.extents import (
    make_bbox_extent,
    make_temporal_extent,
)

T = TypeVar("T", bound="Layer")


@dataclass(kw_only=True)
class LayerNew:
    """
    A layer in its initial state.

    Represents the Layer meta-entity from the data model before it's been saved to the database.
    """

    slug: str
    source_view: str

    def __post_init__(self) -> None:
        """Validate fields."""
        if not re.match(r"^[a-z0-9_]+$", self.slug):
            msg = f"Invalid slug: [{self.slug}]. It must be lowercase a-z, 0-9, and underscores only."
            raise ValueError(msg)

    def to_db_dict(self) -> dict:
        """Convert to a dictionary suitable for database insertion."""
        converter = cattrs.Converter()
        return converter.unstructure(self)


@dataclass(kw_only=True)
class Layer(LayerNew):
    """
    A layer in its saved state.

    Represents the Layer meta-entity from the data model after being saved to the database.
    """

    agol_id_geojson: str | None = None
    agol_id_feature: str | None = None
    agol_id_feature_ogc: str | None = None
    data_last_refreshed: datetime | None = None
    metadata_last_refreshed: datetime | None = None
    created_at: datetime  # system column reused as read-only property

    @classmethod
    def from_db_dict(cls: type[T], data: dict) -> "Layer":
        """Convert from a dictionary retrieved from the database."""
        converter = cattrs.Converter()
        converter.register_structure_hook(datetime, lambda d, t: d.astimezone(UTC))
        return converter.structure(data, cls)

    def __repr__(self) -> str:
        """String representation."""  # noqa: D401
        parts = [f"slug={self.slug!r}"]
        if self.agol_id_feature is not None:
            parts.append(f"feature_layer={self.agol_id_feature!r}")

        return f"Layer({', '.join(parts)})"


# noinspection SqlInsertValues
class LayersClient:
    """Client for managing Layers."""

    _schema = "public"
    _table_view = "layer"

    def __init__(self, db_client: DatabaseClient, logger: Logger) -> None:
        """Create client using injected database client."""
        self._db = db_client
        self._logger = logger

    def list_slugs(self) -> list[str]:
        """Retrieve all Layer slugs."""
        results = self._db.get_query_result(query=SQL("""SELECT slug FROM public.layer;"""))
        return [row[0] for row in results]

    def get_by_slug(self, slug: str) -> Layer | None:
        """
        Retrieve a Layer by its slug.

        Slug has a DB unique constraint so we assume they'll be at most one result.
        """
        result = self._db.get_query_result(
            query=SQL("""
                SELECT slug, source_view, agol_id_geojson, agol_id_feature, agol_id_feature_ogc, data_last_refreshed, metadata_last_refreshed, created_at
                FROM public.layer
                WHERE slug = %(slug)s;
            """),
            params={"slug": slug},
            as_dict=True,
        )

        if not result:
            return None
        return Layer.from_db_dict(result[0])

    def get_extent_by_slug(self, slug: str) -> Extent:
        """
        Retrieve a bounding geographic and temporal extent for data in Layer by its slug.

        Slug has a DB unique constraint so we assume they'll be at most one result.

        Replies on the `layer.source_view` returning rows containing `geom_2d` and `time_utc` columns.

        Currently, this view is typically a post-processed version of this, encoding the data as a GeoJSON feature
        collection, which is unsuitable. By convention this GeoJSON view is named after the underlying data view (which
        is suitable) with a `_geojson` suffix. As a workaround, this method remove this to try and get suitable data.

        This is not a long-term solution and will be replaced with a more robust approach.
        """
        source_view_result = self._db.get_query_result(
            query=SQL("""SELECT source_view FROM public.layer WHERE slug = %(slug)s;"""),
            params={"slug": slug},
        )
        source_view_result = source_view_result[0][0].replace("_geojson", "")

        # noinspection SqlResolve
        result = self._db.get_query_result(
            query=SQL("""
            WITH latest_ext AS (
                SELECT
                    ST_EXTENT(geom_2d) AS bbox,
                    MIN(time_utc)::timestamptz (0) AS min_time,
                    MAX(time_utc)::timestamptz (0) AS max_time
                FROM {view}
            )
            SELECT
                ST_XMIN(bbox) AS min_x,
                ST_YMIN(bbox) AS min_y,
                ST_XMAX(bbox) AS max_x,
                ST_YMAX(bbox) AS max_y,
                min_time AS min_t,
                max_time AS max_t
            FROM latest_ext;
            """).format(view=Identifier(source_view_result))
        )
        self._logger.debug("Raw extents data: %s", result[0])

        row = result[0]
        bbox = make_bbox_extent(min_x=row[0], max_x=row[2], min_y=row[1], max_y=row[3])
        time = make_temporal_extent(start=row[4], end=row[5])
        return Extent(identifier="bounding", geographic=bbox, temporal=time)

    def get_bounding_extent(self) -> Extent:
        """Retrieve a bounding geographic and temporal extent for data across all Layers."""
        extents = [self.get_extent_by_slug(slug) for slug in self.list_slugs()]

        bboxes = [extent.geographic.bounding_box for extent in extents]
        bbox = make_bbox_extent(
            min_x=min(bbox.west_longitude for bbox in bboxes),
            max_x=max(bbox.east_longitude for bbox in bboxes),
            min_y=min(bbox.south_latitude for bbox in bboxes),
            max_y=max(bbox.north_latitude for bbox in bboxes),
        )

        times = [extent.temporal.period for extent in extents if extent.temporal is not None]
        time = make_temporal_extent(
            start=min(time.start.date for time in times),
            end=max(time.end.date for time in times),
        )

        return Extent(identifier="bounding", geographic=bbox, temporal=time)

    def get_latest_data_refresh(self) -> datetime:
        """Retrieve latest `data_last_refreshed` value, or None if null."""
        result = self._db.get_query_result(query=SQL("""SELECT MAX(data_last_refreshed) FROM public.layer;"""))
        return result[0][0]

    def set_item_id(
        self,
        slug: str,
        geojson_id: str | None = None,
        feature_id: str | None = None,
        feature_ogc_id: str | None = None,
    ) -> None:
        """Set the relevant item ID(s) for a given layer identified by a slug."""
        if geojson_id is not None:
            self._db.execute(
                query=SQL("""UPDATE public.layer SET agol_id_geojson = %(agol_id)s WHERE slug = %(slug)s;"""),
                params={"slug": slug, "agol_id": geojson_id},
            )
        if feature_id is not None:
            self._db.execute(
                query=SQL("""UPDATE public.layer SET agol_id_feature = %(agol_id)s WHERE slug = %(slug)s;"""),
                params={"slug": slug, "agol_id": feature_id},
            )
        if feature_ogc_id is not None:
            self._db.execute(
                query=SQL("""UPDATE public.layer SET agol_id_feature_ogc = %(agol_id)s WHERE slug = %(slug)s;"""),
                params={"slug": slug, "agol_id": feature_ogc_id},
            )

    def set_last_refreshed(
        self, slug: str, data_refreshed: datetime | None = None, metadata_refreshed: datetime | None = None
    ) -> None:
        """Indicate when a layer identified by a given slug was last refreshed/overwritten."""
        if data_refreshed is not None and data_refreshed.tzinfo != UTC:
            msg = f"Invalid data_refreshed timezone: [{data_refreshed.tzinfo}]. It must be UTC."
            raise ValueError(msg)
        if metadata_refreshed is not None and metadata_refreshed.tzinfo != UTC:
            msg = f"Invalid metadata_refreshed timezone: [{metadata_refreshed.tzinfo}]. It must be UTC."
            raise ValueError(msg)

        if data_refreshed is not None:
            self._db.execute(
                query=SQL("""UPDATE public.layer SET data_last_refreshed = %(refreshed)s WHERE slug = %(slug)s;"""),
                params={"slug": slug, "refreshed": data_refreshed},
            )
        if metadata_refreshed is not None:
            self._db.execute(
                query=SQL("""UPDATE public.layer SET metadata_last_refreshed = %(refreshed)s WHERE slug = %(slug)s;"""),
                params={"slug": slug, "refreshed": metadata_refreshed},
            )
