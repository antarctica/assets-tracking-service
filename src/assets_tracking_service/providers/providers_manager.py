import logging
from datetime import UTC, datetime

from psycopg.sql import SQL
from psycopg.types.json import Jsonb

from assets_tracking_service.config import Config
from assets_tracking_service.db import DatabaseClient
from assets_tracking_service.models.asset import AssetNew, AssetsClient
from assets_tracking_service.models.label import Label, LabelRelation
from assets_tracking_service.models.position import PositionNew, PositionsClient
from assets_tracking_service.providers.aircraft_tracking import AircraftTrackingProvider
from assets_tracking_service.providers.base_provider import Provider
from assets_tracking_service.providers.geotab import GeotabProvider
from assets_tracking_service.providers.rvdas import RvdasProvider


class ProvidersManager:
    """Create instances for enabled providers."""

    def __init__(self, config: Config, db: DatabaseClient, logger: logging.Logger) -> None:
        self._config = config
        self._logger = logger
        self._db = db

        self._assets = AssetsClient(db_client=self._db)
        self._positions = PositionsClient(db_client=self._db)
        self._providers: list[Provider] = self._make_providers(self._config.ENABLED_PROVIDERS)

    def _make_providers(self, provider_names: list[str]) -> list[Provider]:
        """Create instances for enabled providers."""
        self._logger.info("Creating providers...")
        providers = []

        if "geotab" in provider_names:
            self._logger.info("Creating Geotab provider...")
            try:
                providers.append(GeotabProvider(config=self._config, logger=self._logger))
                self._logger.info("Created Geotab provider.")
            except RuntimeError:
                self._logger.exception("Failed to create Geotab provider.")
                self._logger.info("Geotab provider will be skipped.")

        if "aircraft_tracking" in provider_names:
            self._logger.info("Creating Aircraft Tracking provider...")
            try:
                providers.append(AircraftTrackingProvider(config=self._config, logger=self._logger))
                self._logger.info("Created Aircraft Tracking provider.")
            except RuntimeError:
                self._logger.exception("Failed to create Aircraft Tracking provider.")
                self._logger.info("Aircraft Tracking provider will be skipped.")

        if "rvdas" in provider_names:
            self._logger.info("Creating RVDAS provider...")
            try:
                providers.append(RvdasProvider(config=self._config, logger=self._logger))
                self._logger.info("Created RVDAS provider.")
            except RuntimeError:
                self._logger.exception("Failed to create RVDAS provider.")
                self._logger.info("Rvdas provider will be skipped.")

        self._logger.info("Providers created.")
        return providers

    def _filter_entities(
        self, db_values: list[dict[str, str]], indexed_fetched_entities: dict[str, AssetNew | PositionNew]
    ) -> list[AssetNew | PositionNew]:
        """
        Find new assets from collection returned by a provider.

        Takes:
        - assets fetched from a provider indexed by their distinguishing label value (e.g. serial number)
        - assets fetched from the database associated with the provider

        Finds the intersection of both lists based on the distinguishing property to give new (unsaved) assets.
        """
        existing_values = [row["dist_label_value"] for row in db_values]
        self._logger.debug("Existing dist IDs: [%s].", ", ".join(existing_values))

        new_values = [value for value in indexed_fetched_entities if value not in existing_values]
        _new_entities = [indexed_fetched_entities[value] for value in new_values]
        self._logger.debug("New dist IDs: [%s].", ", ".join(new_values))

        return _new_entities

    def fetch_active_assets(self) -> None:
        """
        Fetch and persist active assets from providers.

        Steps:
        - index fetched assets by their distinguishing label value (e.g. serial number)
        - fetch assets from the database associated with the provider
        - compare data to find new assets
        - persist new assets in the database
        - for all fetched assets, update the 'ats:last_fetched' label
        """
        self._logger.info("Fetching active assets from providers...")

        for provider in self._providers:
            self._logger.info("Fetching active assets from '%s' provider...", provider.name)

            dist_label_scheme = provider.distinguishing_asset_label_scheme
            self._logger.debug("Distinguishing asset label scheme for provider: '%s'", dist_label_scheme)

            fetched_assets_by_dist_id = {
                asset.labels.filter_by_scheme(dist_label_scheme).value: asset
                for asset in provider.fetch_active_assets()
            }
            self._logger.info("Fetched %d assets from '%s' provider.", len(fetched_assets_by_dist_id), provider.name)
            self._logger.debug("Fetched asset dist. labels: [%s].", ", ".join(fetched_assets_by_dist_id.keys()))

            results = self._db.get_query_result(
                query=SQL("""
                    WITH label_elements AS (
                        SELECT jsonb_array_elements(labels->'values') AS label
                        FROM public.asset
                    )
                    SELECT label->>'value' AS dist_label_value
                    FROM label_elements
                    WHERE label @> %s;
                """),
                params=(Jsonb({"scheme": provider.distinguishing_asset_label_scheme}),),
                as_dict=True,
            )
            _new_assets = self._filter_entities(db_values=results, indexed_fetched_entities=fetched_assets_by_dist_id)
            self._logger.info("Persisting %d new assets from '%s' provider.", len(_new_assets), provider.name)
            for asset in _new_assets:
                asset.labels.append(Label(rel=LabelRelation.PROVIDER, scheme="ats:last_fetched", value=0))
                self._assets.add(asset)

            self._logger.info("Upserting 'ats:last_fetched' label for fetched assets.")
            self._db.execute(
                query=SQL("""
                    UPDATE asset
                    SET labels = jsonb_set(
                        labels,
                        '{values}',
                        (SELECT
                            jsonb_agg(
                                CASE
                                    WHEN value->>'scheme' = 'ats:last_fetched' THEN jsonb_set(value, '{value}', %s)
                                    ELSE value
                                END
                            )
                         FROM jsonb_array_elements(labels->'values') as value)
                    )
                    WHERE id IN (
                        SELECT
                            id
                        FROM public.asset
                        WHERE EXISTS (
                            SELECT 1
                            FROM jsonb_array_elements(labels->'values') AS label
                            WHERE label @> %s
                            AND (label->>'value')::text = ANY(%s)
                        )
                    );
                """),
                params=(
                    Jsonb(int(datetime.now(tz=UTC).timestamp())),
                    Jsonb({"scheme": provider.distinguishing_asset_label_scheme}),
                    [list(fetched_assets_by_dist_id.keys())],
                ),
            )

        self._logger.info("Fetched active assets from providers.")

    def fetch_latest_positions(self) -> None:
        """
        Fetch and persist latest positions from providers.

        Steps:
        - index fetched positions by their distinguishing label value (e.g. log number)
        - fetch asset positions from the database associated with the provider
        - compare data to find new positions
        - persist new positions in the database
        """
        self._logger.info("Fetching latest positions from providers...")

        for provider in self._providers:
            self._logger.info("Fetching latest positions for assets from '%s' provider...", provider.name)

            dist_label_scheme = provider.distinguishing_position_label_scheme
            self._logger.debug("Distinguishing position label scheme for provider: '%s'", dist_label_scheme)

            self._logger.debug("Fetching provider assets to associate with positions...")
            provider_asset_label = provider.provider_labels.filter_by_scheme("ats:provider_id")
            provider_assets = self._assets.list_filtered_by_label(label=provider_asset_label)
            self._logger.debug("Fetched %d provider assets.", len(provider_assets))

            fetched_positions_by_dist_id = {
                position.labels.filter_by_scheme(dist_label_scheme).value: position
                for position in provider.fetch_latest_positions(assets=provider_assets)
            }
            self._logger.info(
                "Fetched %d positions from '%s' provider.", len(fetched_positions_by_dist_id), provider.name
            )
            self._logger.debug("Fetched position dist. labels: [%s].", ", ".join(fetched_positions_by_dist_id.keys()))

            results = self._db.get_query_result(
                query=SQL("""
                    WITH label_elements AS (
                        SELECT jsonb_array_elements(labels->'values') AS label
                        FROM public.position
                    )
                    SELECT label->>'value' AS dist_label_value
                    FROM label_elements
                    WHERE label @> %s;
                """),
                params=(Jsonb({"scheme": provider.distinguishing_position_label_scheme}),),
                as_dict=True,
            )

            _new_positions = self._filter_entities(
                db_values=results, indexed_fetched_entities=fetched_positions_by_dist_id
            )
            self._logger.info("Persisting %d new positions from '%s' provider.", len(_new_positions), provider.name)
            for position in _new_positions:
                self._positions.add(position)

            self._logger.info("Fetched assets from '%s' provider.", provider.name)

        self._logger.info("Fetched latest positions from providers.")
