import logging
import sys
import time
from contextlib import suppress
from copy import deepcopy
from datetime import UTC, datetime
from http.client import HTTPConnection
from importlib.metadata import version
from pathlib import Path
from subprocess import PIPE, Popen
from tempfile import TemporaryDirectory
from typing import Literal, TypedDict
from unittest.mock import MagicMock, PropertyMock
from uuid import uuid4

import pytest
from arcgis.gis import Item, ItemTypeEnum, SharingLevel
from boto3 import client as S3Client  # noqa: N812
from moto import mock_aws
from mygeotab import MyGeotabException, TimeoutException
from psycopg import Connection
from psycopg.sql import SQL
from pytest_mock import MockerFixture
from pytest_postgresql import factories
from requests import HTTPError
from resources.lib.data_catalogue.site_exporter import SiteExporter
from shapely import Point
from typer.testing import CliRunner
from ulid import ULID
from ulid import parse as ulid_parse

from assets_tracking_service.cli import app_cli
from assets_tracking_service.config import Config
from assets_tracking_service.db import DatabaseClient, DatabaseError
from assets_tracking_service.exporters.arcgis import ArcGisExporter, ArcGisExporterLayer
from assets_tracking_service.exporters.catalogue import CollectionRecord, DataCatalogueExporter, LayerRecord
from assets_tracking_service.exporters.exporters_manager import ExportersManager
from assets_tracking_service.lib.bas_data_catalogue.exporters.base_exporter import Exporter, S3Utils
from assets_tracking_service.lib.bas_data_catalogue.exporters.html_exporter import HtmlAliasesExporter
from assets_tracking_service.lib.bas_data_catalogue.exporters.iso_exporter import IsoXmlHtmlExporter
from assets_tracking_service.lib.bas_data_catalogue.exporters.records_exporter import RecordsExporter
from assets_tracking_service.lib.bas_data_catalogue.exporters.site_exporter import (
    SiteIndexExporter,
    SiteResourcesExporter,
)
from assets_tracking_service.lib.bas_data_catalogue.models.item.catalogue import AdditionalInfoTab, ItemCatalogue
from assets_tracking_service.lib.bas_data_catalogue.models.item.catalogue.elements import Dates as ItemCatDates
from assets_tracking_service.lib.bas_data_catalogue.models.item.catalogue.elements import (
    Identifiers as ItemCatIdentifiers,
)
from assets_tracking_service.lib.bas_data_catalogue.models.record import Record as LibRecord
from assets_tracking_service.lib.bas_data_catalogue.models.record import RecordSummary
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.common import (
    Date,
    Dates,
    Identifier,
    Identifiers,
)
from assets_tracking_service.lib.bas_data_catalogue.models.record.enums import HierarchyLevelCode
from assets_tracking_service.lib.bas_esri_utils.client import ArcGisClient
from assets_tracking_service.lib.bas_esri_utils.models.item import Item as CatalogueItemArcGis
from assets_tracking_service.models.asset import Asset, AssetNew, AssetsClient
from assets_tracking_service.models.label import Label, LabelRelation, Labels
from assets_tracking_service.models.layer import Layer, LayerNew, LayersClient
from assets_tracking_service.models.position import Position, PositionNew, PositionsClient
from assets_tracking_service.models.record import Record, RecordNew, RecordsClient
from assets_tracking_service.providers.aircraft_tracking import AircraftTrackingProvider
from assets_tracking_service.providers.geotab import GeotabProvider
from assets_tracking_service.providers.providers_manager import ProvidersManager
from assets_tracking_service.providers.rvdas import RvdasProvider
from tests.pytest_pg_factories import (
    factory_name as postgresql_factory_name,
)

# unused-imports are needed for the `factory_name` import to work
from tests.pytest_pg_factories import (  # noqa: F401
    postgresql_noproc_factory,
    postgresql_proc_factory,
)
from tests.resources.examples.example_exporter import ExampleExporter
from tests.resources.examples.example_provider import ExampleProvider
from tests.resources.lib.data_catalogue.records.item_cat_collection_all import record as collection_all_supported
from tests.resources.lib.data_catalogue.records.item_cat_data import record as data_all_supported
from tests.resources.lib.data_catalogue.records.item_cat_formatting import record as formatting_supported
from tests.resources.lib.data_catalogue.records.item_cat_licence import (
    cc_record,
    ogl_record,
    ops_record,
    rights_reversed_record,
)
from tests.resources.lib.data_catalogue.records.item_cat_product_all import record as product_all_supported
from tests.resources.lib.data_catalogue.records.item_cat_product_min import record as product_min_supported
from tests.resources.lib.data_catalogue.records.item_cat_pub_map import record as product_published_map

# override `postgresql` fixture with either a local (proc) or remote (noproc) fixture depending on if in CI.
postgresql = factories.postgresql(postgresql_factory_name)


def _prepare_blank_db(db_client: DatabaseClient) -> None:
    """Prepare a blank database for running migrations."""
    with suppress(DatabaseError):
        db_client.execute(query=SQL("SET timezone TO 'UTC';"))
        # noinspection PyProtectedMember
        db_client._conn.commit()
        db_client.execute(query=SQL("CREATE USER assets_tracking_service_ro NOLOGIN;"))


def _create_fake_arcgis_item(item_id: str, item_type: ItemTypeEnum = ItemTypeEnum.GEOJSON) -> Item:
    """Create a fake ArcGIS Item."""
    item_data = {
        "title": "x",
        "name": "x",  # file-name
        "owner": "x",
        "type": item_type.value,
        "modified": datetime.now(tz=UTC).timestamp() * 1000,
        "id": item_id,
        "sharing_level": SharingLevel.PRIVATE,
    }

    mock_gis = MagicMock(auto_spec=True)
    return Item(mock_gis, item_id, item_data)


@pytest.fixture()
def fx_package_version() -> str:
    """Package version."""
    return version("assets_tracking_service")


@pytest.fixture()
def fx_logger() -> logging.Logger:
    """App logger."""
    logger = logging.getLogger("app")
    logger.setLevel(logging.DEBUG)
    return logger


@pytest.fixture()
def fx_config() -> Config:
    """App configuration."""
    return Config()


# noinspection PyShadowingNames
@pytest.fixture()
def fx_db_client_tmp_db(mocker: MockerFixture, postgresql: Connection) -> DatabaseClient:
    """
    Database client with an empty, disposable, database.

    The `db_client.close()` method is mocked as disposable DBs are tied to each connection.
    """
    client = DatabaseClient(conn=postgresql)
    mocker.patch("assets_tracking_service.db.DatabaseClient.close", return_value=None)
    _prepare_blank_db(client)

    return client


@pytest.fixture()
def fx_db_client_tmp_db_mig(fx_db_client_tmp_db: DatabaseClient) -> DatabaseClient:
    """Database client with a migrated, disposable, database."""
    fx_db_client_tmp_db.migrate_upgrade()
    return fx_db_client_tmp_db


@pytest.fixture()
def fx_db_client_tmp_db_pop(
    mocker: MockerFixture,
    fx_db_client_tmp_db_mig: DatabaseClient,
    fx_logger: logging.Logger,
    fx_provider_example: ExampleProvider,
    fx_layer_init: Layer,
) -> DatabaseClient:
    """Database client with a populated, disposable, database."""
    mock_config = mocker.Mock()
    type(mock_config).ENABLED_PROVIDERS = PropertyMock(return_value=[])

    providers = ProvidersManager(config=mock_config, db=fx_db_client_tmp_db_mig, logger=fx_logger)
    providers._providers = [fx_provider_example]
    providers.fetch_active_assets()
    providers.fetch_latest_positions()

    # Set system created_at for layer added my migration to controlled value, as field is exposed in Layer model
    fx_db_client_tmp_db_mig.execute(
        query=SQL("""UPDATE public.layer SET created_at = %(t)s WHERE pk = 1;"""),
        params={"t": fx_layer_init.created_at},
    )

    return fx_db_client_tmp_db_mig


@pytest.fixture()
def fx_db_client_tmp_db_pop_exported(
    fx_db_client_tmp_db_pop: DatabaseClient, fx_logger: logging.Logger, fx_layer_updated: Layer
) -> DatabaseClient:
    """Database client with a populated, disposable, database having run exporters."""
    dt_data = datetime(2020, 8, 8, 8, 8, 8, tzinfo=UTC)
    dt_meta = datetime(2020, 10, 10, 10, 10, 10, tzinfo=UTC)
    layers_client = LayersClient(db_client=fx_db_client_tmp_db_pop, logger=fx_logger)

    layers_client.set_item_id(
        slug=fx_layer_updated.slug,
        geojson_id=fx_layer_updated.agol_id_geojson,
        feature_id=fx_layer_updated.agol_id_feature,
        feature_ogc_id=fx_layer_updated.agol_id_feature_ogc,
    )
    layers_client.set_last_refreshed(slug=fx_layer_updated.slug, data_refreshed=dt_data, metadata_refreshed=dt_meta)

    return fx_db_client_tmp_db_pop


@pytest.fixture()
def fx_cli() -> CliRunner:
    """CLI testing fixture."""
    return CliRunner()


# noinspection PyShadowingNames
@pytest.fixture()
def fx_cli_tmp_db(mocker: MockerFixture, postgresql: Connection) -> CliRunner:
    """CLI testing fixture using a disposable database."""
    client = DatabaseClient(conn=postgresql)
    mocker.patch("assets_tracking_service.cli.db.make_conn", return_value=postgresql)
    mocker.patch("assets_tracking_service.db.DatabaseClient.close", return_value=None)
    _prepare_blank_db(client)

    return CliRunner()


@pytest.fixture()
def fx_cli_tmp_db_mig(fx_cli_tmp_db: CliRunner) -> CliRunner:
    """CLI using a disposable database after running app `db migrate` command."""
    fx_cli_tmp_db.invoke(app=app_cli, args=["db", "migrate"])
    return fx_cli_tmp_db


@pytest.fixture()
def fx_label_rel() -> LabelRelation:
    """LabelRelation for use with a Label."""
    return LabelRelation.SELF


@pytest.fixture()
def fx_label_scheme() -> str:
    """Scheme for use with a Label."""
    return "skos:prefLabel"


@pytest.fixture()
def fx_label_scheme_uri() -> str:
    """Scheme URI for use with a Label."""
    return "https://www.w3.org/2012/09/odrl/semantic/draft/doco/skos_prefLabel.html"


@pytest.fixture()
def fx_label_value() -> str:
    """Value for use with a Label."""
    return "Constance Watson"


@pytest.fixture()
def fx_label_value_uri() -> str:
    """Value URI for use with a Label."""
    return "https://sandbox.orcid.org/0000-0001-8373-6934"


@pytest.fixture()
def fx_label_value_updated() -> str:
    """Updated value for use with a Label."""  # noqa: D401
    return "Connie Watson"


@pytest.fixture()
def fx_label_expiry() -> int:
    """Expiry for use with a Label."""
    date = datetime(2014, 4, 24, 14, 30, 0, tzinfo=UTC)
    return int(date.timestamp())


@pytest.fixture()
def fx_label_minimal(fx_label_rel: LabelRelation, fx_label_scheme: str, fx_label_value: str) -> Label:
    """Label with minimal/required properties."""
    return Label(rel=fx_label_rel, scheme=fx_label_scheme, value=fx_label_value)


@pytest.fixture()
def fx_label_full(
    fx_label_rel: LabelRelation,
    fx_label_scheme: str,
    fx_label_value: str,
    fx_label_scheme_uri: str,
    fx_label_value_uri: str,
) -> Label:
    """Label with all properties (except expiration)."""
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
    """Copy of types for Labels unstructure method."""

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
    """Expired Label."""
    return Label(rel=fx_label_rel, scheme="skos:Label", value="Connie Watson", expiration=fx_label_expiry)


@pytest.fixture()
def fx_label_updated(fx_label_rel: LabelRelation, fx_label_scheme: str, fx_label_value_updated: str) -> Label:
    """Label with updated value property."""
    return Label(rel=fx_label_rel, scheme=fx_label_scheme, value=fx_label_value_updated)


@pytest.fixture()
def fx_labels_one(fx_label_full: Label) -> Labels:
    """Set of Labels containing one label."""
    return Labels([fx_label_full])


@pytest.fixture()
def fx_labels_multiple(fx_label_full: Label, fx_label_expired: Label) -> Labels:
    """
    Set of Labels containing multiple labels.

    Includes at most one label using the 'skos:prefLabel' scheme.
    """
    return Labels([fx_label_full, fx_label_expired])


@pytest.fixture()
def fx_asset_id() -> ULID:
    """ULID for use with Assets."""
    # noinspection SpellCheckingInspection
    return ulid_parse("01HYQPTGE7S3P2ZX21CWJRKTNW")


@pytest.fixture()
def fx_asset_new(fx_labels_one: Labels) -> AssetNew:
    """AssetNew."""
    return AssetNew(labels=fx_labels_one)


@pytest.fixture()
def fx_asset(fx_asset_id: ULID, fx_label_full: Label) -> Asset:
    """Asset."""
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
    # noinspection PyTypeChecker,PyProtectedMember,PyUnresolvedReferences
    fx_assets_client_empty._db.execute(
        SQL(
            f"UPDATE public.asset SET id = ulid_to_uuid('{fx_asset_id}') "  # noqa: S608
            f"WHERE id = (SELECT id FROM public.asset LIMIT 1);"
        )
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
    # noinspection PyTypeChecker,PyProtectedMember,PyUnresolvedReferences
    fx_assets_client_one._db.execute(
        f"UPDATE public.asset SET id = ulid_to_uuid('{asset_two_id}') "  # noqa: S608 - can't be exploited by users
        f"WHERE id = (SELECT id FROM public.asset LIMIT 1 OFFSET 1);"
    )

    return fx_assets_client_one


@pytest.fixture()
def fx_position_id() -> ULID:
    """ULID for use with a Position."""
    # noinspection SpellCheckingInspection
    return ulid_parse("01HYN10Z7GJKSFXSK5VQ5XWHJJ")


@pytest.fixture()
def fx_position_time() -> datetime:
    """Datetime for use with a Position."""
    return datetime(2014, 4, 24, 14, 30, 0, tzinfo=UTC)


@pytest.fixture()
def fx_position_geom_2d() -> Point:
    """2D Point for use with a Position."""
    return Point(0, 0)


@pytest.fixture()
def fx_position_geom_3d() -> Point:
    """3D Point for use with a Position."""
    return Point(0, 0, 0)


@pytest.fixture()
def fx_position_new_minimal(fx_asset: Asset, fx_position_time: datetime, fx_position_geom_3d: Point) -> PositionNew:
    """PositionNew with 3D geometry and minimal properties set."""
    return PositionNew(asset_id=fx_asset.id, time=fx_position_time, geom=fx_position_geom_3d, labels=Labels([]))


@pytest.fixture()
def fx_position_new_minimal_2d(fx_asset: Asset, fx_position_time: datetime, fx_position_geom_2d: Point) -> PositionNew:
    """PositionNew with 2D geometry and minimal properties set."""
    return PositionNew(asset_id=fx_asset.id, time=fx_position_time, geom=fx_position_geom_2d, labels=Labels([]))


@pytest.fixture()
def fx_position_minimal(
    fx_position_id: ULID, fx_asset: Asset, fx_position_time: datetime, fx_position_geom_3d: Point
) -> Position:
    """Position with 3D geometry and minimal properties set."""
    return Position(
        id=fx_position_id, asset_id=fx_asset.id, time=fx_position_time, geom=fx_position_geom_3d, labels=Labels([])
    )


@pytest.fixture()
def fx_position_minimal_2d(
    fx_position_id: ULID, fx_asset: Asset, fx_position_time: datetime, fx_position_geom_2d: Point
) -> Position:
    """Position with 2D geometry and minimal properties set."""
    return Position(
        id=fx_position_id, asset_id=fx_asset.id, time=fx_position_time, geom=fx_position_geom_2d, labels=Labels([])
    )


@pytest.fixture()
def fx_positions_client_empty(fx_assets_client_one: AssetsClient) -> PositionsClient:
    """Positions client using a disposable, migrated, database."""
    # noinspection PyProtectedMember,PyUnresolvedReferences
    return PositionsClient(db_client=fx_assets_client_one._db)


@pytest.fixture()
def fx_record_layer_slug() -> str:
    """Record/Layer slug."""
    return "ats_latest_assets_position"


@pytest.fixture()
def fx_layer_pre_init(fx_record_layer_slug: str) -> LayerNew:
    """Layer that has not yet been initialised."""
    return LayerNew(
        slug=fx_record_layer_slug,
        source_view="v_latest_assets_pos",
    )


@pytest.fixture()
def fx_layer_init(fx_layer_pre_init: Layer) -> Layer:
    """Layer that has been initialised but not setup or updated."""
    # this field would normally be set by the database as a system column
    created_at = datetime(2014, 4, 24, 14, 30, 0, tzinfo=UTC)

    return Layer(
        slug=fx_layer_pre_init.slug,
        source_view=fx_layer_pre_init.source_view,
        created_at=created_at,
    )


@pytest.fixture()
def fx_layer_updated(fx_layer_init: Layer) -> Layer:
    """Layer that has been initialised and updated at least once."""
    layer_updated = deepcopy(fx_layer_init)
    layer_updated.agol_id_geojson = "123geojsonV1"
    layer_updated.agol_id_feature = "234featuresV1"
    layer_updated.agol_id_feature_ogc = "345ogcV1"
    layer_updated.data_last_refreshed = datetime(2020, 8, 8, 8, 8, 8, tzinfo=UTC)
    layer_updated.metadata_last_refreshed = datetime(2020, 10, 10, 10, 10, 10, tzinfo=UTC)
    return layer_updated


@pytest.fixture()
def fx_layers_client_one(fx_db_client_tmp_db_pop_exported: DatabaseClient, fx_logger: logging.Logger) -> LayersClient:
    """Layers client setup using a disposable, migrated and exported database containing an updated layer."""
    return LayersClient(db_client=fx_db_client_tmp_db_pop_exported, logger=fx_logger)


@pytest.fixture()
def fx_record_new(fx_record_layer_slug: str) -> RecordNew:
    """Record."""
    dt = datetime(2014, 4, 24, 14, 30, 0, tzinfo=UTC)
    return RecordNew(
        slug=fx_record_layer_slug,
        edition="x",
        title="x",
        summary="x",
        publication=dt,
        released=dt,
        update_frequency="x",
        gitlab_issue="https://gitlab.data.bas.ac.uk/x",
    )


@pytest.fixture()
def fx_record(fx_record_new: RecordNew) -> Record:
    """Record."""
    id_ = uuid4()
    return Record(
        id=id_,
        slug=fx_record_new.slug,
        edition=fx_record_new.edition,
        title=fx_record_new.title,
        summary=fx_record_new.summary,
        publication=fx_record_new.publication,
        released=fx_record_new.released,
        update_frequency=fx_record_new.update_frequency,
        gitlab_issue=fx_record_new.gitlab_issue,
    )


@pytest.fixture()
def fx_records_client_one(fx_db_client_tmp_db_pop_exported: DatabaseClient, fx_logger: logging.Logger) -> RecordsClient:
    """Records client setup using a disposable, migrated and exported database containing a record."""  # noqa: D401
    return RecordsClient(db_client=fx_db_client_tmp_db_pop_exported)


@pytest.fixture()
def fx_provider_example(fx_config: Config, fx_logger: logging.Logger) -> ExampleProvider:
    """ExampleProvider."""
    return ExampleProvider(config=fx_config, logger=fx_logger)


@pytest.fixture()
def fx_provider_aircraft_tracking(fx_config: Config, fx_logger: logging.Logger) -> AircraftTrackingProvider:
    """AircraftTrackingProvider."""
    return AircraftTrackingProvider(config=fx_config, logger=fx_logger)


@pytest.fixture()
def fx_provider_geotab(fx_config: Config, fx_logger: logging.Logger) -> GeotabProvider:
    """GeotabProvider."""
    return GeotabProvider(config=fx_config, logger=fx_logger)


@pytest.fixture()
def fx_provider_geotab_mocked(mocker: MockerFixture, fx_config: Config, fx_logger: logging.Logger) -> GeotabProvider:
    """GeotabProvider with a mocked client."""
    mocker.patch("assets_tracking_service.providers.geotab.Geotab", return_value=mocker.MagicMock(auto_spec=True))
    return GeotabProvider(config=fx_config, logger=fx_logger)


@pytest.fixture()
def fx_provider_geotab_mocked_error_mygeotab(mocker: MockerFixture, fx_config: Config, fx_logger: logging.Logger):
    """GeotabProvider with a mocked client that raises a MyGeotabException."""
    mock_geotab_client = mocker.MagicMock(auto_spec=True)
    mock_geotab_client.get.side_effect = MyGeotabException(
        full_error={"errors": [{"name": "Fake Error", "message": "Fake Error."}]}
    )
    mocker.patch("assets_tracking_service.providers.geotab.Geotab", return_value=mock_geotab_client)

    return GeotabProvider(config=fx_config, logger=fx_logger)


@pytest.fixture()
def fx_provider_geotab_mocked_error_timeout(mocker: MockerFixture, fx_config: Config, fx_logger: logging.Logger):
    """GeotabProvider with a mocked client that raises a TimeoutException."""
    mock_geotab_client = mocker.MagicMock(auto_spec=True)
    mock_geotab_client.get.side_effect = TimeoutException(server="Fake Server")
    mocker.patch("assets_tracking_service.providers.geotab.Geotab", return_value=mock_geotab_client)

    return GeotabProvider(config=fx_config, logger=fx_logger)


@pytest.fixture()
def fx_provider_geotab_mocked_error_http(mocker: MockerFixture, fx_config: Config, fx_logger: logging.Logger):
    """GeotabProvider with a mocked client that raises an HTTPError."""
    mock_geotab_client = mocker.MagicMock(auto_spec=True)
    mock_geotab_client.get.side_effect = HTTPError()
    mocker.patch("assets_tracking_service.providers.geotab.Geotab", return_value=mock_geotab_client)

    return GeotabProvider(config=fx_config, logger=fx_logger)


@pytest.fixture()
def fx_provider_rvdas(mocker: MockerFixture, fx_config: Config, fx_logger: logging.Logger) -> RvdasProvider:
    """RvdasProvider."""
    provider = RvdasProvider(config=fx_config, logger=fx_logger)
    positions = [
        {
            "longitude": -45.579346,
            "latitude": -60.701442,
            "speedknots": 0.1,
            "headingtrue": 299.55,
            "gps_time": "2025-04-12 12:09:34.729+00",
            "_fake_vessel_id": "1",
            "_fake_position_id": "c28c61d85e803b933c722bef9307cf76",
        }
    ]
    mocker.patch.object(provider, "_fetch_latest_positions", return_value=positions)
    return provider


@pytest.fixture()
def fx_providers_manager_no_providers(
    mocker: MockerFixture, fx_db_client_tmp_db_mig: DatabaseClient, fx_logger: logging.Logger
) -> ProvidersManager:
    """ProvidersManager with no configured providers."""
    mock_config = mocker.Mock()
    type(mock_config).ENABLED_PROVIDERS = PropertyMock(return_value=[])

    return ProvidersManager(config=mock_config, db=fx_db_client_tmp_db_mig, logger=fx_logger)


@pytest.fixture()
def fx_providers_manager_eg_provider(
    fx_providers_manager_no_providers: ProvidersManager, fx_provider_example: ExampleProvider
) -> ProvidersManager:
    """ProvidersManager with ExampleProvider as configured provider."""
    fx_providers_manager_no_providers._providers = [fx_provider_example]
    return fx_providers_manager_no_providers


@pytest.fixture()
def fx_exporter_example(
    fx_config: Config, fx_db_client_tmp_db_pop: DatabaseClient, fx_logger: logging.Logger
) -> ExampleExporter:
    """ExampleExporter."""
    return ExampleExporter(config=fx_config, db=fx_db_client_tmp_db_pop, logger=fx_logger)


@pytest.fixture()
def fx_exporter_arcgis_layer(
    mocker: MockerFixture,
    fx_config: Config,
    fx_db_client_tmp_db_pop: DatabaseClient,
    fx_logger: logging.Logger,
    fx_record_layer_slug: str,
) -> ArcGisExporterLayer:
    """
    ArcGisExporterLayer with mocked clients.

    Mocked to prevent real interactions with external services.
    """
    layers_client = LayersClient(db_client=fx_db_client_tmp_db_pop, logger=fx_logger)
    init_geojson_item = _create_fake_arcgis_item(item_id="123geojsonV0")
    init_features_item = _create_fake_arcgis_item(item_id="234featuresV0")
    updated_features_item = _create_fake_arcgis_item(item_id="234featuresV1")

    mock_gis = mocker.MagicMock(auto_spec=True)
    mocker.patch("assets_tracking_service.exporters.arcgis.GIS", return_value=mock_gis)
    mock_arcgis_client = mocker.MagicMock(auto_spec=True)
    mock_arcgis_client.create_item.return_value = init_geojson_item
    mock_arcgis_client.publish_item.return_value = init_features_item
    mock_arcgis_client.overwrite_service_features.return_value = updated_features_item
    mock_arcgis_client.update_item.return_value = updated_features_item
    mocker.patch("assets_tracking_service.exporters.arcgis.ArcGisClient", return_value=mock_arcgis_client)

    return ArcGisExporterLayer(
        config=fx_config,
        db=fx_db_client_tmp_db_pop,
        logger=fx_logger,
        arcgis=mock_gis,
        layers=layers_client,
        layer_slug=fx_record_layer_slug,
    )


@pytest.fixture()
def fx_exporter_arcgis_layer_updated(
    fx_exporter_arcgis_layer: ArcGisExporterLayer, fx_layer_updated: Layer
) -> ArcGisExporterLayer:
    """ArcGisExporterLayer with an updated/setup layer."""
    exporter_layer = fx_exporter_arcgis_layer
    exporter_layer._layer = fx_layer_updated

    return exporter_layer


@pytest.fixture()
def fx_exporter_arcgis(
    mocker: MockerFixture,
    fx_config: Config,
    fx_db_client_tmp_db_pop: DatabaseClient,
    fx_logger: logging.Logger,
    fx_exporter_arcgis_layer: ArcGisExporterLayer,
) -> ArcGisExporter:
    """ArcGISExporter with mocked dependencies."""
    mocker.patch("assets_tracking_service.exporters.arcgis.GIS", return_value=mocker.MagicMock(auto_spec=True))
    mocker.patch("assets_tracking_service.exporters.arcgis.ArcGisExporterLayer", return_value=fx_exporter_arcgis_layer)

    return ArcGisExporter(config=fx_config, db=fx_db_client_tmp_db_pop, logger=fx_logger)


@pytest.fixture()
def fx_exporter_collection_record(
    fx_config: Config,
    fx_db_client_tmp_db_pop_exported: DatabaseClient,
    fx_logger: logging.Logger,
    fx_layer_updated: Layer,
) -> CollectionRecord:
    """CollectionRecord."""
    return CollectionRecord(config=fx_config, db=fx_db_client_tmp_db_pop_exported, logger=fx_logger)


@pytest.fixture()
def fx_exporter_layer_record(
    fx_config: Config,
    fx_db_client_tmp_db_pop_exported: DatabaseClient,
    fx_logger: logging.Logger,
    fx_record_layer_slug: str,
    fx_layer_updated: Layer,
) -> LayerRecord:
    """LayerRecord."""
    return LayerRecord(
        config=fx_config, db=fx_db_client_tmp_db_pop_exported, logger=fx_logger, layer_slug=fx_record_layer_slug
    )


@pytest.fixture()
def fx_exporter_catalogue(
    fx_config: Config,
    fx_db_client_tmp_db_pop: DatabaseClient,
    fx_s3_client: S3Client,
    fx_logger: logging.Logger,
) -> DataCatalogueExporter:
    """DataCatalogueExporter."""
    return DataCatalogueExporter(config=fx_config, db=fx_db_client_tmp_db_pop, s3=fx_s3_client, logger=fx_logger)


@pytest.fixture()
def fx_exporters_manager_no_exporters(
    mocker: MockerFixture, fx_db_client_tmp_db_pop: DatabaseClient, fx_s3_client: S3Client, fx_logger: logging.Logger
) -> ExportersManager:
    """ExportersManager with no configured exporters."""
    mock_config = mocker.Mock()
    type(mock_config).ENABLED_EXPORTERS = PropertyMock(return_value=[])

    return ExportersManager(config=mock_config, db=fx_db_client_tmp_db_pop, s3=fx_s3_client, logger=fx_logger)


@pytest.fixture()
def fx_exporters_manager_eg_exporter(
    fx_exporters_manager_no_exporters: ExportersManager, fx_exporter_example: ExampleExporter
) -> ExportersManager:
    """ExportersManager with ExampleExporter as configured exporter."""
    fx_exporters_manager_no_exporters._providers = [fx_exporter_example]
    return fx_exporters_manager_no_exporters


def _lib_record_config_minimal_iso() -> dict:
    """
    Minimal record configuration (ISO).

    Minimal record that will validate against the BAS Metadata Library ISO 19115:2003 / 19115-2:2009 v4 schema.

    Types must be safe to encode as JSON.

    Standalone method to allow use outside of fixtures in test parametrisation.
    """
    return {
        "$schema": "https://metadata-resources.data.bas.ac.uk/bas-metadata-generator-configuration-schemas/v2/iso-19115-2-v4.json",
        "hierarchy_level": "dataset",
        "metadata": {
            "contacts": [{"organisation": {"name": "x"}, "role": ["pointOfContact"]}],
            "date_stamp": "2014-06-30",
        },
        "identification": {
            "title": {"value": "x"},
            "dates": {"creation": "2014-06-30"},
            "abstract": "x",
        },
    }


@pytest.fixture()
def fx_lib_record_config_minimal_iso() -> dict:
    """
    Minimal record configuration (ISO).

    Minimal record that will validate against the BAS Metadata Library ISO 19115:2003 / 19115-2:2009 v4 schema.

    Types must be safe to encode as JSON.
    """
    return _lib_record_config_minimal_iso()


def _lib_record_config_minimal_item(base_config: dict) -> dict:
    """
    Minimal record configuration (Item).

    Minimal record that can be used with an ItemBase. Types must be safe to encode as JSON.

    Standalone method to allow use outside of fixtures in test parametrisation.
    """
    config = deepcopy(base_config)
    config["file_identifier"] = "x"
    return config


@pytest.fixture()
def fx_lib_record_config_minimal_item(fx_lib_record_config_minimal_iso: dict) -> dict:
    """Minimal record configuration (Item)."""
    return _lib_record_config_minimal_item(fx_lib_record_config_minimal_iso)


@pytest.fixture()
def fx_lib_record_config_minimal_magic_preset(fx_lib_record_config_minimal_item: dict) -> dict:
    """
    Minimal record configuration (MAGIC Preset).

    Minimal record that can create a valid RecordMagicDiscoveryV1 instance. Does not include properties that the
    preset will set (such as identifiers, contacts, domain consistencies).

    Types must be safe to encode as JSON.
    """
    return deepcopy(fx_lib_record_config_minimal_item)


def _lib_record_config_minimal_item_catalogue(base_config: dict) -> dict:
    """
    Minimal record configuration (ItemCatalogue).

    Minimal record that can be used with an ItemCatalogue. Types must be safe to encode as JSON.

    Standalone method to allow use outside of fixtures in test parametrisation.
    """
    config = deepcopy(base_config)
    config["identification"]["contacts"] = deepcopy(config["metadata"]["contacts"])
    config["identification"]["contacts"][0]["email"] = "x"
    config["identification"]["identifiers"] = [
        {
            "identifier": config["file_identifier"],
            "href": f"https://data.bas.ac.uk/items/{fx_lib_record_config_minimal_item}",
            "namespace": "data.bas.ac.uk",
        }
    ]

    return config


@pytest.fixture()
def fx_lib_record_config_minimal_item_catalogue(fx_lib_record_config_minimal_item: dict) -> dict:
    """Minimal record configuration (ItemCatalogue)."""
    return _lib_record_config_minimal_item_catalogue(fx_lib_record_config_minimal_item)


@pytest.fixture()
def fx_lib_record_minimal_iso(fx_lib_record_config_minimal_iso: dict) -> LibRecord:
    """Minimal record instance (ISO)."""
    return LibRecord.loads(fx_lib_record_config_minimal_iso)


@pytest.fixture()
def fx_lib_record_minimal_item(fx_lib_record_config_minimal_item: dict) -> LibRecord:
    """Minimal record instance (Item)."""
    return LibRecord.loads(fx_lib_record_config_minimal_item)


@pytest.fixture()
def fx_lib_record_minimal_item_catalogue(fx_lib_record_config_minimal_item_catalogue: dict) -> LibRecord:
    """Minimal record instance (ItemCatalogue)."""
    return LibRecord.loads(fx_lib_record_config_minimal_item_catalogue)


@pytest.fixture()
def fx_lib_record_summary_minimal_item(fx_lib_record_minimal_item_catalogue: Record) -> RecordSummary:
    """Minimal record summary instance (Item)."""
    return RecordSummary.loads(fx_lib_record_minimal_item_catalogue)


def _lib_get_record_summary(identifier: str) -> RecordSummary:
    """
    Minimal record summary lookup method.

    Standalone method to allow use outside of fixtures.
    """
    return RecordSummary(
        file_identifier=identifier,
        hierarchy_level=HierarchyLevelCode.PRODUCT,
        title="x",
        abstract="x",
        creation=Date(date=datetime(2014, 6, 30, tzinfo=UTC).date()),
    )


@pytest.fixture()
def fx_lib_get_record_summary() -> callable:
    """Minimal record summary lookup method."""
    return _lib_get_record_summary


@pytest.fixture()
def fx_lib_item_cat_info_tab_minimal() -> AdditionalInfoTab:
    """Minimal ItemCatalogue additional information tab."""
    dates = ItemCatDates(dates=Dates(creation=Date(date=datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC))))
    identifiers = ItemCatIdentifiers(Identifiers([]))
    return AdditionalInfoTab(
        item_id="x",
        item_type=HierarchyLevelCode.PRODUCT,
        identifiers=identifiers,
        dates=dates,
        datestamp=datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC).date(),
        kv={},
    )


def _lib_item_catalogue_min() -> ItemCatalogue:
    """
    ItemCatalogue based on minimal catalogue record.

    Standalone method to allow use outside of fixtures in test parametrisation.
    """
    return ItemCatalogue(
        record=LibRecord.loads(
            _lib_record_config_minimal_item_catalogue(_lib_record_config_minimal_item(_lib_record_config_minimal_iso()))
        ),
        embedded_maps_endpoint="x",
        item_contact_endpoint="x",
        get_record_summary=_lib_get_record_summary,
    )


@pytest.fixture()
def fx_lib_item_catalogue_min(
    fx_lib_record_minimal_item_catalogue: Record, fx_lib_get_record_summary: callable
) -> ItemCatalogue:
    """ItemCatalogue based on minimal catalogue record."""
    return ItemCatalogue(
        record=fx_lib_record_minimal_item_catalogue,
        embedded_maps_endpoint="x",
        item_contact_endpoint="x",
        get_record_summary=fx_lib_get_record_summary,
    )


@pytest.fixture()
def fx_s3_bucket_name() -> str:
    """S3 bucket name."""
    return "testing"


@pytest.fixture()
def fx_s3_client(mocker: MockerFixture, fx_s3_bucket_name: str) -> S3Client:
    """Mocked S3 client with testing bucket pre-created."""  # noqa: D401
    mock_config = mocker.Mock()
    type(mock_config).EXPORTER_DATA_CATALOGUE_AWS_ACCESS_ID = PropertyMock(return_value="x")
    type(mock_config).EXPORTER_DATA_CATALOGUE_AWS_ACCESS_SECRET = PropertyMock(return_value="x")

    with mock_aws():
        client = S3Client(
            "s3",
            aws_access_key_id=mock_config.EXPORTER_DATA_CATALOGUE_AWS_ACCESS_ID,
            aws_secret_access_key=mock_config.EXPORTER_DATA_CATALOGUE_AWS_ACCESS_SECRET,
            region_name="eu-west-1",
        )

        client.create_bucket(
            Bucket=fx_s3_bucket_name,
            CreateBucketConfiguration={"LocationConstraint": "eu-west-1"},
        )

        yield client


@pytest.fixture()
def fx_lib_s3_utils(fx_s3_client: S3Client, fx_s3_bucket_name: str) -> S3Utils:
    """S3Utils with a mocked S3 client."""
    with TemporaryDirectory() as tmp_path:
        base_path = Path(tmp_path)
    return S3Utils(s3=fx_s3_client, s3_bucket=fx_s3_bucket_name, relative_base=base_path)


@pytest.fixture()
def fx_lib_exporter_base(
    mocker: MockerFixture, fx_s3_bucket_name: str, fx_s3_client: S3Client, fx_lib_record_minimal_item: LibRecord
) -> Exporter:
    """Data Catalogue base exporter with a mocked config and S3 client."""  # noqa: D401
    with TemporaryDirectory() as tmp_path:
        output_path = Path(tmp_path)
    mock_config = mocker.Mock()
    type(mock_config).EXPORTER_DATA_CATALOGUE_OUTPUT_PATH = PropertyMock(return_value=output_path)
    type(mock_config).EXPORTER_DATA_CATALOGUE_AWS_S3_BUCKET = PropertyMock(return_value=fx_s3_bucket_name)

    exporter = Exporter(
        config=mock_config,
        s3=fx_s3_client,
        record=fx_lib_record_minimal_item,
        export_base=output_path.joinpath("x"),
        export_name="x.txt",
    )
    mocker.patch.object(exporter, "dumps", return_value="x")
    return exporter


@pytest.fixture()
def fx_lib_exporter_iso_xml_html(
    mocker: MockerFixture, fx_s3_bucket_name: str, fx_s3_client: S3Client, fx_lib_record_minimal_item: LibRecord
) -> Exporter:
    """ISO 19115 XML as HTML exporter with a mocked config and S3 client."""
    with TemporaryDirectory() as tmp_path:
        base_path = Path(tmp_path)
        exports_path = base_path.joinpath("exports")
        stylesheets_path = base_path.joinpath("static")
    mock_config = mocker.Mock()
    type(mock_config).EXPORTER_DATA_CATALOGUE_OUTPUT_PATH = PropertyMock(return_value=base_path)
    type(mock_config).EXPORTER_DATA_CATALOGUE_AWS_S3_BUCKET = PropertyMock(return_value=fx_s3_bucket_name)

    return IsoXmlHtmlExporter(
        config=mock_config,
        s3=fx_s3_client,
        record=fx_lib_record_minimal_item,
        export_base=exports_path,
        stylesheets_base=stylesheets_path,
    )


@pytest.fixture()
def fx_lib_exporter_html_alias(
    mocker: MockerFixture,
    fx_s3_bucket_name: str,
    fx_s3_client: S3Client,
    fx_lib_record_minimal_item_catalogue: LibRecord,
) -> Exporter:
    """HTML alias exporter with a mocked config and S3 client."""
    with TemporaryDirectory() as tmp_path:
        output_path = Path(tmp_path)
    mock_config = mocker.Mock()
    type(mock_config).EXPORTER_DATA_CATALOGUE_OUTPUT_PATH = PropertyMock(return_value=output_path)
    type(mock_config).EXPORTER_DATA_CATALOGUE_AWS_S3_BUCKET = PropertyMock(return_value=fx_s3_bucket_name)

    fx_lib_record_minimal_item_catalogue.identification.identifiers.append(
        Identifier(identifier="x", href="https://data.bas.ac.uk/datasets/x", namespace="alias.data.bas.ac.uk")
    )

    return HtmlAliasesExporter(
        config=mock_config, s3=fx_s3_client, record=fx_lib_record_minimal_item_catalogue, site_base=output_path
    )


@pytest.fixture()
def fx_lib_exporter_records(
    mocker: MockerFixture,
    fx_logger: logging.Logger,
    fx_s3_bucket_name: str,
    fx_s3_client: S3Client,
    fx_lib_record_minimal_item_catalogue: Record,
) -> RecordsExporter:
    """Records meta exporter with a mocked config and S3 client and minimal record."""  # noqa: D401
    with TemporaryDirectory() as tmp_path:
        output_path = Path(tmp_path)
    mock_config = mocker.Mock()
    type(mock_config).EXPORTER_DATA_CATALOGUE_OUTPUT_PATH = PropertyMock(return_value=output_path)
    type(mock_config).EXPORTER_DATA_CATALOGUE_AWS_S3_BUCKET = PropertyMock(return_value=fx_s3_bucket_name)
    type(mock_config).EXPORTER_DATA_CATALOGUE_EMBEDDED_MAPS_ENDPOINT = PropertyMock(return_value="x")
    type(mock_config).EXPORTER_DATA_CATALOGUE_ITEM_CONTACT_ENDPOINT = PropertyMock(return_value="x")

    records = [fx_lib_record_minimal_item_catalogue]
    summaries = [RecordSummary.loads(record) for record in records]
    return RecordsExporter(config=mock_config, logger=fx_logger, s3=fx_s3_client, records=records, summaries=summaries)


@pytest.fixture()
def fx_lib_exporter_site_resources(
    mocker: MockerFixture, fx_s3_bucket_name: str, fx_s3_client: S3Client
) -> SiteResourcesExporter:
    """Site resources exporter with a mocked config and S3 client."""
    with TemporaryDirectory() as tmp_path:
        output_path = Path(tmp_path)
    mock_config = mocker.Mock()
    type(mock_config).EXPORTER_DATA_CATALOGUE_OUTPUT_PATH = PropertyMock(return_value=output_path)
    type(mock_config).EXPORTER_DATA_CATALOGUE_AWS_S3_BUCKET = PropertyMock(return_value=fx_s3_bucket_name)

    return SiteResourcesExporter(config=mock_config, s3=fx_s3_client)


@pytest.fixture()
def fx_lib_exporter_site_index(
    mocker: MockerFixture,
    fx_s3_bucket_name: str,
    fx_logger: logging.Logger,
    fx_s3_client: S3Client,
    fx_lib_record_minimal_item_catalogue: Record,
) -> SiteIndexExporter:
    """Site resources exporter with a mocked config and S3 client."""
    with TemporaryDirectory() as tmp_path:
        output_path = Path(tmp_path)
    mock_config = mocker.Mock()
    type(mock_config).EXPORTER_DATA_CATALOGUE_OUTPUT_PATH = PropertyMock(return_value=output_path)
    type(mock_config).EXPORTER_DATA_CATALOGUE_AWS_S3_BUCKET = PropertyMock(return_value=fx_s3_bucket_name)

    summaries = [RecordSummary.loads(fx_lib_record_minimal_item_catalogue)]
    return SiteIndexExporter(config=mock_config, s3=fx_s3_client, logger=fx_logger, summaries=summaries)


def lib_exporter_static_site_records() -> list[LibRecord]:
    """Records for populating static site exporter."""  # noqa: D401
    return [
        collection_all_supported,
        product_min_supported,
        product_all_supported,
        formatting_supported,
        data_all_supported,
        ogl_record,
        cc_record,
        ops_record,
        rights_reversed_record,
        product_published_map,
    ]


def fx_lib_exporter_static_site_records() -> list[LibRecord]:
    """Records for populating static site exporter."""  # noqa: D401
    return lib_exporter_static_site_records()


@pytest.fixture(scope="module")
def fx_lib_exporter_static_site(module_mocker: MockerFixture) -> TemporaryDirectory:
    """
    Build static site and export to a temp directory.

    Module scoped for performance. Means usual fixtures for config and S3Client can't be used and are duplicated.
    """
    site_dir = TemporaryDirectory()

    logger = logging.getLogger("app")
    logger.setLevel(logging.DEBUG)

    config = Config()
    module_mocker.patch.object(
        type(config),
        attribute="EXPORTER_DATA_CATALOGUE_OUTPUT_PATH",
        new_callable=PropertyMock,
        return_value=Path(site_dir.name),
    )
    module_mocker.patch.object(
        type(config), attribute="EXPORTER_DATA_CATALOGUE_AWS_ACCESS_ID", new_callable=PropertyMock, return_value="x"
    )
    module_mocker.patch.object(
        type(config), attribute="EXPORTER_DATA_CATALOGUE_AWS_ACCESS_SECRET", new_callable=PropertyMock, return_value="x"
    )

    with mock_aws():
        s3_client = S3Client(
            "s3",
            aws_access_key_id=config.EXPORTER_DATA_CATALOGUE_AWS_ACCESS_ID,
            aws_secret_access_key=config.EXPORTER_DATA_CATALOGUE_AWS_ACCESS_SECRET,
            region_name="eu-west-1",
        )

    exporter = SiteExporter(config=config, s3=s3_client, logger=logger)
    exporter.export()

    if not Path(site_dir.name).joinpath("favicon.ico").exists():
        msg = "Failed to generate static site"
        raise RuntimeError(msg) from None

    return site_dir


@pytest.fixture(scope="module")
def fx_lib_exporter_static_server(fx_lib_exporter_static_site: TemporaryDirectory):
    """Expose static site from a local server."""
    retries = 5
    python_bin = sys.executable
    site_dir = fx_lib_exporter_static_site.name
    process = Popen([python_bin, "-m", "http.server", "8123", "--directory", site_dir], stdout=PIPE)  # noqa: S603

    while retries > 0:
        conn = HTTPConnection("localhost:8123")
        try:
            conn.request("HEAD", "/")
            response = conn.getresponse()
            if response is not None:
                yield process
                break
        except ConnectionRefusedError:
            time.sleep(1)
            retries -= 1

    if not retries:
        msg = "Failed to start http server"
        raise RuntimeError(msg) from None
    else:
        process.terminate()
        process.wait()
        fx_lib_exporter_static_site.cleanup()


@pytest.fixture()
def fx_lib_catalogue_arcgis_item(fx_lib_record_minimal_item: Record) -> CatalogueItemArcGis:
    """ItemArcGIS."""
    return CatalogueItemArcGis(
        record=fx_lib_record_minimal_item, arcgis_item_type=ItemTypeEnum.GEOJSON, arcgis_item_name="x"
    )


@pytest.fixture()
def fx_lib_arcgis_client(mocker: MockerFixture, fx_logger: logging.Logger) -> ArcGisClient:
    """BAS ArcGIS client."""
    return ArcGisClient(arcgis=mocker.MagicMock(auto_spec=True), logger=fx_logger)
