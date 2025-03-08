from dataclasses import dataclass
from typing import TypeVar

import cattrs
from psycopg.sql import SQL
from psycopg.types.json import Jsonb
from ulid import ULID
from ulid import parse as ulid_parse

from assets_tracking_service.db import DatabaseClient
from assets_tracking_service.models.label import Label, Labels

T = TypeVar("T", bound="Asset")


@dataclass(kw_only=True)
class AssetNew:
    """
    An asset in its initial state.

    Represents the Asset entity from the data model before it's been saved to the database (i.e. before it has an ID).
    """

    labels: Labels

    def __post_init__(self) -> None:
        """Validate fields."""
        if not self.labels:
            msg = "Invalid labels: It must not be empty."
            raise ValueError(msg)

        if not isinstance(self.labels, Labels):
            msg = "Invalid labels: It must be a Labels object."
            raise TypeError(msg)

        # Check labels include at least/most an item with 'skos:prefLabel' scheme.
        if [label.scheme for label in self.labels].count("skos:prefLabel") != 1:
            msg = "Invalid labels: It must include at least and at most one skos:prefLabel item."
            raise ValueError(msg)

    def to_db_dict(self) -> dict:
        """Convert to a dictionary suitable for database insertion."""
        converter = cattrs.Converter()
        converter.register_unstructure_hook(Labels, lambda d: Jsonb(self.labels.unstructure()))

        return converter.unstructure(self)


@dataclass(kw_only=True)
class Asset(AssetNew):
    """
    An asset in its saved state.

    Represents the Asset entity from data model before after being saved to the database (i.e. has an ID).

    Extends AssetNew with additional information.
    """

    id: ULID

    def to_db_dict(self) -> dict:
        """Convert to a dictionary suitable for database insertion."""
        data = super().to_db_dict()
        del data["id"]

        return data

    @classmethod
    def from_db_dict(cls: type[T], data: dict) -> "Asset":
        """Convert from a dictionary retrieved from the database."""
        converter = cattrs.Converter()
        converter.register_structure_hook(ULID, lambda d, t: ulid_parse(d))
        converter.register_structure_hook(Labels, lambda d, t: Labels.structure(d))

        return converter.structure(data, cls)

    @property
    def pref_label_value(self) -> str:
        """Asset 'name' (skos:prefLabel)."""
        return self.labels.filter_by_scheme("skos:prefLabel").value


class AssetsClient:
    """Client for managing Assets."""

    _schema = "public"
    _table_view = "asset"

    def __init__(self, db_client: DatabaseClient) -> None:
        self._db = db_client

    def add(self, asset: AssetNew) -> None:
        """Persist a new Asset in the database."""
        self._db.insert_dict(schema=self._schema, table_view=self._table_view, data=asset.to_db_dict())

    def list_filtered_by_label(self, label: Label) -> list[Asset]:
        """
        Filter Assets labels by a Label.

        I.e. to find one or more assets based on a specific label.

        If specified, scheme and value URIs will be used to filter. Creation and expiration times are always ignored.
        """
        _label = {"rel": label.rel.value, "scheme": label.scheme, "value": label.value}
        if label.scheme_uri:
            _label["scheme_uri"] = label.scheme_uri
        if label.value_uri:
            _label["value_uri"] = label.value_uri

        results = self._db.get_query_result(
            query=SQL("""
                SELECT
                    uuid_to_ulid(id) AS id,
                    labels
                FROM public.asset
                WHERE EXISTS (
                    SELECT 1
                    FROM jsonb_array_elements(labels->'values') AS label
                    WHERE label @> %s
                );
            """),
            params=(Jsonb(_label),),
            as_dict=True,
        )
        return [Asset.from_db_dict(row) for row in results]

    def list(self) -> list[Asset]:
        """Retrieve all Assets from the database."""
        results = self._db.get_query_result(
            query=SQL("""
                SELECT
                    uuid_to_ulid(id) AS id,
                    labels
                FROM
                    public.asset;
            """),
            as_dict=True,
        )
        return [Asset.from_db_dict(row) for row in results]
