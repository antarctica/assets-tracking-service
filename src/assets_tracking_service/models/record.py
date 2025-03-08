import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Self, TypeVar
from uuid import UUID

import cattrs
from importlib_resources import as_file as resources_as_file
from importlib_resources import files as resources_files
from psycopg.sql import SQL

from assets_tracking_service.db import DatabaseClient

T = TypeVar("T", bound="Record")


@dataclass(kw_only=True)
class RecordNew:
    """
    A Record in its initial state.

    Represents the Record meta-entity from the data model before it's been saved to the database.
    """

    slug: str
    edition: str
    title: str
    summary: str
    publication: datetime
    released: datetime
    update_frequency: str
    gitlab_issue: str | None = None

    def __post_init__(self) -> None:
        """Validate fields."""
        if not re.match(r"^[a-z0-9_]+$", self.slug):
            msg = f"Invalid slug: [{self.slug}]. It must be lowercase a-z, 0-9, and underscores only."
            raise ValueError(msg)

        if self.publication.tzinfo != UTC:
            msg = f"Invalid publication timezone: [{self.publication.tzinfo}]. It must be UTC."
            raise ValueError(msg)

        if self.released.tzinfo != UTC:
            msg = f"Invalid released timezone: [{self.released.tzinfo}]. It must be UTC."
            raise ValueError(msg)

        if self.gitlab_issue is not None and "https://gitlab.data.bas.ac.uk" not in self.gitlab_issue:
            msg = f"Invalid gitlab_issue: [{self.gitlab_issue}]. It must be a valid BAS GitLab issue URL."
            raise ValueError(msg)

        _ = self.abstract

    def to_db_dict(self: Self) -> dict:
        """Convert to a dictionary suitable for database insertion."""
        converter = cattrs.Converter()
        return converter.unstructure(self)

    def _get_resource_contents(self, file: str) -> str:
        with resources_as_file(resources_files("assets_tracking_service.resources.records")) as resources_path:
            res_path = resources_path.joinpath(self.slug).joinpath(file)
            with res_path.open() as f:
                return f.read()

    @property
    def abstract(self) -> str:
        """Read abstract contents from file."""
        return self._get_resource_contents("abstract.md")

    @property
    def lineage(self) -> str | None:
        """Read lineage from file."""
        try:
            return self._get_resource_contents("lineage.md")
        except FileNotFoundError:
            return None


@dataclass(kw_only=True)
class Record(RecordNew):
    """
    A Record in its saved state.

    Represents the Record meta-entity from the data model after being saved to the database.
    """

    id: UUID

    @classmethod
    def from_db_dict(cls: type[T], data: dict) -> "Record":
        """Convert from a dictionary retrieved from the database."""
        converter = cattrs.Converter()
        converter.register_structure_hook(UUID, lambda d, t: UUID(bytes=d.bytes))
        converter.register_structure_hook(datetime, lambda d, t: d.astimezone(UTC))
        return converter.structure(data, cls)

    def __repr__(self: Self) -> str:
        """String representation."""  # noqa: D401
        return f"Record(id={str(self.id)!r}, slug={self.slug!r})"


class RecordsClient:
    """Client for managing Records."""

    _schema = "public"
    _table_view = "record"

    def __init__(self: Self, db_client: DatabaseClient) -> None:
        """Create client using injected database client."""
        self._db = db_client

    def list_ids(self) -> list[str]:
        """Retrieve all record IDs (file identifiers)."""
        results = self._db.get_query_result(query=SQL("""SELECT id FROM public.record;"""))
        return [result[0] for result in results]

    def get_by_slug(self, slug: str) -> Record | None:
        """
        Retrieve a record by its slug.

        Slug has a DB unique constraint so we assume they'll be at most one result.
        """
        result = self._db.get_query_result(
            query=SQL("""
                SELECT id, slug, edition, title, summary, publication, released, update_frequency, gitlab_issue
                FROM public.record
                WHERE slug = %(slug)s;
            """),
            params={"slug": slug},
            as_dict=True,
        )

        if not result:
            return None
        return Record.from_db_dict(result[0])
