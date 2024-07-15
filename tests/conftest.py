import logging
from datetime import datetime, timezone
from typing import TypedDict, Literal
from unittest.mock import PropertyMock

import pytest
from mygeotab import MyGeotabException, TimeoutException
from psycopg import Connection
from pytest_mock import MockerFixture
from pytest_postgresql import factories
from shapely import Point
from typer.testing import CliRunner
from ulid import ULID, parse as ulid_parse

from assets_tracking_service.cli import app_cli
from assets_tracking_service.config import Config
from assets_tracking_service.db import DatabaseClient
from assets_tracking_service.models.asset import AssetNew, Asset, AssetsClient
from assets_tracking_service.models.label import Labels, Label, LabelRelation
from assets_tracking_service.models.position import PositionNew, Position, PositionsClient
from assets_tracking_service.providers.aircraft_tracking import AircraftTrackingConfig, AircraftTrackingProvider
from assets_tracking_service.providers.geotab import GeotabConfig, GeotabProvider
from assets_tracking_service.providers.providers_manager import ProvidersManager
from tests.providers.example_provider import ExampleProviderConfig, ExampleProvider

# unused-imports are needed for the `factory_name` import to work
from tests.pytest_postgresql import (  # noqa: F401
    postgresql_proc_factory,
    postgresql_noproc_factory,
    factory_name as postgresql_factory_name,
)

# override `postgresql` fixture with either a local (proc) or remote (noproc) fixture depending on if in CI.
postgresql = factories.postgresql(postgresql_factory_name)


@pytest.fixture()
def fx_logger() -> logging.Logger:
    """App logger."""
    logger = logging.getLogger("app")
    logger.setLevel(logging.DEBUG)
    return logger


@pytest.fixture
def fx_config() -> Config:
    return Config()


# noinspection PyShadowingNames
@pytest.fixture()
def fx_db_client_tmp_db(postgresql: Connection) -> DatabaseClient:
    """Database client with an empty, disposable, database."""
    return DatabaseClient(conn=postgresql)


@pytest.fixture()
def fx_db_client_tmp_db_mig(fx_db_client_tmp_db: DatabaseClient) -> DatabaseClient:
    """Database client with a migrated, disposable, database."""
    fx_db_client_tmp_db.migrate_upgrade()
    fx_db_client_tmp_db.commit()
    return fx_db_client_tmp_db


@pytest.fixture()
def fx_cli() -> CliRunner:
    """CLI testing fixture."""
    return CliRunner()


# noinspection PyShadowingNames
@pytest.fixture()
def fx_cli_tmp_db(mocker: MockerFixture, postgresql: Connection) -> CliRunner:
    """CLI testing fixture using a disposable database."""
    mocker.patch("assets_tracking_service.cli.db.make_conn", return_value=postgresql)
    return CliRunner()


@pytest.fixture()
def fx_cli_tmp_db_mig(fx_cli_tmp_db: CliRunner) -> CliRunner:
    """CLI using a disposable database after running app `db migrate` command."""
    fx_cli_tmp_db.invoke(app=app_cli, args=["db", "migrate"])
    return fx_cli_tmp_db


@pytest.fixture()
def fx_label_rel() -> LabelRelation:
    """A LabelRelation for use with a Label."""
    return LabelRelation.SELF


@pytest.fixture()
def fx_label_scheme() -> str:
    """A scheme for use with a Label."""
    return "skos:prefLabel"


@pytest.fixture()
def fx_label_scheme_uri() -> str:
    """A scheme URI for use with a Label."""
    return "https://www.w3.org/2012/09/odrl/semantic/draft/doco/skos_prefLabel.html"


@pytest.fixture()
def fx_label_value() -> str:
    """A value for use with a Label."""
    return "Constance Watson"


@pytest.fixture()
def fx_label_value_uri() -> str:
    """A value URI for use with a Label."""
    return "https://sandbox.orcid.org/0000-0001-8373-6934"


@pytest.fixture()
def fx_label_value_updated() -> str:
    """An updated value for use with a Label."""
    return "Connie Watson"


@pytest.fixture()
def fx_label_expiry() -> int:
    """An expiry for use with a Label."""
    date = datetime(2014, 4, 24, 14, 30, 0, tzinfo=timezone.utc)
    return int(date.timestamp())


@pytest.fixture()
def fx_label_minimal(fx_label_rel: LabelRelation, fx_label_scheme: str, fx_label_value: str) -> Label:
    """A Label with minimal/required properties."""
    return Label(rel=fx_label_rel, scheme=fx_label_scheme, value=fx_label_value)


@pytest.fixture()
def fx_label_full(
    fx_label_rel: LabelRelation,
    fx_label_scheme: str,
    fx_label_value: str,
    fx_label_scheme_uri: str,
    fx_label_value_uri: str,
) -> Label:
    """A Label with all properties (except expiration)."""
    return Label(
        rel=fx_label_rel,
        scheme=fx_label_scheme,
        value=fx_label_value,
        scheme_uri=fx_label_scheme_uri,
        value_uri=fx_label_value_uri,
        creation=1718533247,
        expiration=None,
    )


class LabelsPlain(TypedDict):
    version: Literal["1"]
    values: list[dict[str, str | int | float]]


@pytest.fixture()
def fx_label_full_plain() -> LabelsPlain:
    """Unstructured version of label using plain types."""
    return {
        "version": "1",
        "values": [
            {
                "rel": "self",
                "scheme": "skos:prefLabel",
                "scheme_uri": "https://www.w3.org/2012/09/odrl/semantic/draft/doco/skos_prefLabel.html",
                "value": "Constance Watson",
                "value_uri": "https://sandbox.orcid.org/0000-0001-8373-6934",
                "creation": 1718533247,
                "expiration": None,
            }
        ],
    }


@pytest.fixture()
def fx_label_expired(
    fx_label_rel: LabelRelation, fx_label_scheme: str, fx_label_value: str, fx_label_expiry: int
) -> Label:
    """An expired Label."""
    return Label(rel=fx_label_rel, scheme="skos:Label", value="Connie Watson", expiration=fx_label_expiry)


@pytest.fixture()
def fx_label_updated(fx_label_rel: LabelRelation, fx_label_scheme: str, fx_label_value_updated: str) -> Label:
    """A Label with updated value property."""
    return Label(rel=fx_label_rel, scheme=fx_label_scheme, value=fx_label_value_updated)


@pytest.fixture()
def fx_labels_one(fx_label_full: Label) -> Labels:
    """A set of Labels containing one label."""
    return Labels([fx_label_full])


@pytest.fixture()
def fx_labels_multiple(fx_label_full: Label, fx_label_expired: Label) -> Labels:
    """
    A set of Labels containing multiple labels.

    Includes at most one label using the 'skos:prefLabel' scheme.
    """
    return Labels([fx_label_full, fx_label_expired])


@pytest.fixture()
def fx_asset_id() -> ULID:
    """A ULID for use with Assets."""
    # noinspection SpellCheckingInspection
    return ulid_parse("01HYQPTGE7S3P2ZX21CWJRKTNW")


@pytest.fixture()
def fx_asset_new(fx_labels_one: Labels) -> AssetNew:
    """An AssetNew."""
    return AssetNew(labels=fx_labels_one)


@pytest.fixture()
def fx_asset(fx_asset_id: ULID, fx_label_full: Label) -> Asset:
    """An Asset."""
    return Asset(id=fx_asset_id, labels=Labels([fx_label_full]))


@pytest.fixture()
def fx_assets_client_empty(fx_db_client_tmp_db_mig: DatabaseClient) -> AssetsClient:
    """Assets client using a disposable, migrated, database."""
    return AssetsClient(db_client=fx_db_client_tmp_db_mig)


@pytest.fixture()
def fx_assets_client_one(
    fx_assets_client_empty: AssetsClient, fx_asset_new: AssetNew, fx_asset_id: ULID
) -> AssetsClient:
    """Assets client setup using a disposable, migrated, database with a stored asset."""
    fx_assets_client_empty.add(asset=fx_asset_new)

    # update asset with the expected id
    # noinspection PyTypeChecker,PyProtectedMember
    fx_assets_client_empty._db.execute(
        f"UPDATE public.asset SET id = ulid_to_uuid('{fx_asset_id}') "
        f"WHERE id = (SELECT id FROM public.asset LIMIT 1);"
    )

    return fx_assets_client_empty


@pytest.fixture()
def fx_assets_client_many(fx_assets_client_one: AssetsClient) -> AssetsClient:
    """Assets client setup using a disposable, migrated, database with a set of stored assets."""
    # noinspection SpellCheckingInspection
    asset_two_id = ulid_parse("01J23PN3WES4P5PMNAWWGV41NA")
    asset_two = AssetNew(
        labels=Labels(
            [
                Label(rel=LabelRelation.SELF, scheme="skos:prefLabel", value="Raj Watson"),
            ]
        )
    )

    fx_assets_client_one.add(asset=asset_two)
    # update asset with the expected id
    # noinspection PyTypeChecker,PyProtectedMember
    fx_assets_client_one._db.execute(
        f"UPDATE public.asset SET id = ulid_to_uuid('{asset_two_id}') "
        f"WHERE id = (SELECT id FROM public.asset LIMIT 1 OFFSET 1);"
    )

    return fx_assets_client_one


@pytest.fixture()
def fx_position_id() -> ULID:
    """A ULID for use with a Position."""
    # noinspection SpellCheckingInspection
    return ulid_parse("01HYN10Z7GJKSFXSK5VQ5XWHJJ")


@pytest.fixture()
def fx_position_time() -> datetime:
    """A datetime for use with a Position."""
    return datetime(2014, 4, 24, 14, 30, 0, tzinfo=timezone.utc)


@pytest.fixture()
def fx_position_geom_2d() -> Point:
    """A 2D Point for use with a Position."""
    return Point(0, 0)


@pytest.fixture()
def fx_position_geom_3d() -> Point:
    """A 3D Point for use with a Position."""
    return Point(0, 0, 0)


@pytest.fixture()
def fx_position_new_minimal(fx_asset: Asset, fx_position_time: datetime, fx_position_geom_3d: Point) -> PositionNew:
    """A PositionNew with 3D geometry and minimal properties set."""
    return PositionNew(asset_id=fx_asset.id, time=fx_position_time, geom=fx_position_geom_3d, labels=Labels([]))


@pytest.fixture()
def fx_position_new_minimal_2d(fx_asset: Asset, fx_position_time: datetime, fx_position_geom_2d: Point) -> PositionNew:
    """A PositionNew with 2D geometry and minimal properties set."""
    return PositionNew(asset_id=fx_asset.id, time=fx_position_time, geom=fx_position_geom_2d, labels=Labels([]))


@pytest.fixture()
def fx_position_minimal(
    fx_position_id: ULID, fx_asset: Asset, fx_position_time: datetime, fx_position_geom_3d: Point
) -> Position:
    """A Position with 3D geometry and minimal properties set."""
    return Position(
        id=fx_position_id, asset_id=fx_asset.id, time=fx_position_time, geom=fx_position_geom_3d, labels=Labels([])
    )


@pytest.fixture()
def fx_position_minimal_2d(
    fx_position_id: ULID, fx_asset: Asset, fx_position_time: datetime, fx_position_geom_2d: Point
) -> Position:
    """A Position with 2D geometry and minimal properties set."""
    return Position(
        id=fx_position_id, asset_id=fx_asset.id, time=fx_position_time, geom=fx_position_geom_2d, labels=Labels([])
    )


@pytest.fixture()
def fx_positions_client_empty(fx_assets_client_one: AssetsClient) -> PositionsClient:
    """Positions client using a disposable, migrated, database."""
    # noinspection PyProtectedMember
    return PositionsClient(db_client=fx_assets_client_one._db)


@pytest.fixture()
def fx_provider_example_config() -> ExampleProviderConfig:
    return ExampleProviderConfig(username="x", password="x")


@pytest.fixture()
def fx_provider_example(
    fx_provider_example_config: ExampleProviderConfig, fx_logger: logging.Logger
) -> ExampleProvider:
    return ExampleProvider(config=fx_provider_example_config, logger=fx_logger)


@pytest.fixture()
def fx_provider_aircraft_tracking_config() -> AircraftTrackingConfig:
    return {
        "username": "x",
        "password": "x",
        "api_key": "x",
    }


@pytest.fixture()
def fx_provider_aircraft_tracking(
    fx_provider_aircraft_tracking_config: AircraftTrackingConfig, fx_logger: logging.Logger
) -> AircraftTrackingProvider:
    return AircraftTrackingProvider(config=fx_provider_aircraft_tracking_config, logger=fx_logger)


@pytest.fixture()
def fx_provider_geotab_config() -> GeotabConfig:
    return {
        "username": "x",
        "password": "x",
        "database": "x",
        "nvs_l06_group_mappings": {
            "b2795": "15",
            "b2794": "31",
            "b2796": "15",  # ideally needs to be a separate term
        },
    }


@pytest.fixture()
def fx_provider_geotab(fx_provider_geotab_config: GeotabConfig, fx_logger: logging.Logger) -> GeotabProvider:
    return GeotabProvider(config=fx_provider_geotab_config, logger=fx_logger)


@pytest.fixture()
def fx_provider_geotab_mocked(
    mocker: MockerFixture, fx_provider_geotab_config: GeotabConfig, fx_logger: logging.Logger
) -> GeotabProvider:
    mocker.patch("assets_tracking_service.providers.geotab.Geotab", return_value=mocker.MagicMock(auto_spec=True))
    return GeotabProvider(config=fx_provider_geotab_config, logger=fx_logger)


@pytest.fixture()
def fx_provider_geotab_mocked_error_mygeotab(
    mocker: MockerFixture, fx_provider_geotab_config: GeotabConfig, fx_logger: logging.Logger
):
    mock_geotab_client = mocker.MagicMock(auto_spec=True)
    mock_geotab_client.get.side_effect = MyGeotabException(
        full_error={"errors": [{"name": "Fake Error", "message": "Fake Error."}]}
    )
    mocker.patch("assets_tracking_service.providers.geotab.Geotab", return_value=mock_geotab_client)

    return GeotabProvider(config=fx_provider_geotab_config, logger=fx_logger)


@pytest.fixture()
def fx_provider_geotab_mocked_error_timeout(
    mocker: MockerFixture, fx_provider_geotab_config: GeotabConfig, fx_logger: logging.Logger
):
    mock_geotab_client = mocker.MagicMock(auto_spec=True)
    mock_geotab_client.get.side_effect = TimeoutException(server="Fake Server")
    mocker.patch("assets_tracking_service.providers.geotab.Geotab", return_value=mock_geotab_client)

    return GeotabProvider(config=fx_provider_geotab_config, logger=fx_logger)


@pytest.fixture()
def fx_providers_manager_no_providers(
    mocker: MockerFixture, fx_db_client_tmp_db_mig: DatabaseClient, fx_logger: logging.Logger
) -> ProvidersManager:
    mock_config = mocker.Mock()
    type(mock_config).enabled_providers = PropertyMock(return_value=[])

    return ProvidersManager(config=mock_config, db=fx_db_client_tmp_db_mig, logger=fx_logger)