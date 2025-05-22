import pytest

from assets_tracking_service.lib.bas_data_catalogue.models.item.base import AccessType
from assets_tracking_service.lib.bas_data_catalogue.models.item.base.elements import Link
from assets_tracking_service.lib.bas_data_catalogue.models.item.catalogue.distributions import (
    ArcGisFeatureLayer,
    ArcGisOgcApiFeatures,
    ArcGisVectorTileLayer,
    Distribution,
    FileDistribution,
    GeoJson,
    GeoPackage,
    Jpeg,
    Pdf,
    Png,
    Shapefile,
)
from assets_tracking_service.lib.bas_data_catalogue.models.item.catalogue.enums import DistributionType
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.common import (
    Contact,
    ContactIdentity,
    OnlineResource,
)
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.distribution import (
    Distribution as RecordDistribution,
)
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.distribution import (
    Format,
    Size,
    TransferOption,
)
from assets_tracking_service.lib.bas_data_catalogue.models.record.enums import (
    ContactRoleCode,
    OnlineResourceFunctionCode,
)


def _make_dist(format_href: str) -> RecordDistribution:
    return RecordDistribution(
        distributor=Contact(organisation=ContactIdentity(name="x"), role=[ContactRoleCode.DISTRIBUTOR]),
        transfer_option=TransferOption(
            online_resource=OnlineResource(href="x", function=OnlineResourceFunctionCode.DOWNLOAD)
        ),
        format=Format(format="x", href=format_href),
    )


class FakeDistributionType(Distribution):
    """For testing non-abstract distribution properties."""

    @classmethod
    def matches(cls, option: RecordDistribution, other_options: list[RecordDistribution]) -> bool:
        """Match."""
        return False

    @property
    def format_type(self) -> DistributionType:
        """Format."""
        return DistributionType.ARCGIS_FEATURE_LAYER

    @property
    def size(self) -> str:
        """Size."""
        return "x"

    @property
    def action(self) -> Link:
        """Link."""
        return Link(value="x", href="x")

    @property
    def action_btn_icon(self) -> str:
        """Link icon."""
        return "far fa-square"

    @property
    def access_target(self) -> None:
        """Access target."""
        return None


class FakeFileDistributionType(FileDistribution):
    """For testing non-abstract or common file distribution properties."""

    @classmethod
    def matches(cls, option: RecordDistribution, other_options: list[RecordDistribution]) -> bool:
        """Match."""
        return False

    @property
    def format_type(self) -> DistributionType:
        """Format."""
        return DistributionType.GEOJSON


class TestDistribution:
    """Test base Catalogue distribution."""

    def test_encode_url(self):
        """Can encode a URL into a DOM selector."""
        value = "https://example.com"
        expected = "aHR0cHM6Ly9leGFtcGxlLmNvbQ"

        result = Distribution._encode_url(value)
        assert result == expected

    @pytest.mark.cov()
    def test_defaults(self):
        """Can get default values."""
        dist = FakeDistributionType()
        assert dist.action_btn_variant != ""
        assert dist.action_btn_icon != ""


class TestFileDistribution:
    """Test base file based Catalogue distribution."""

    @pytest.mark.parametrize(
        ("size", "expected"),
        [(Size(unit="bytes", magnitude=2), "2 Bytes"), (Size(unit="x", magnitude=1), "1 x"), (None, "")],
    )
    def test_size(self, size: Size | None, expected: str):
        """Can format file size."""
        dist = FakeFileDistributionType(option=_make_dist("x"), other_options=[], access_type=AccessType.PUBLIC)
        dist._option.transfer_option.size = size
        assert dist.size == expected

    @pytest.mark.parametrize(
        ("access", "expected"), [(AccessType.PUBLIC, "Download"), (AccessType.BAS_SOME, "Download")]
    )
    def test_action(self, access: AccessType, expected: str):
        """Can get action link."""
        dist = FakeFileDistributionType(option=_make_dist("x"), other_options=[], access_type=access)
        assert dist.action == Link(value=expected, href="x")

    @pytest.mark.parametrize(("access", "expected"), [(AccessType.PUBLIC, "default"), (AccessType.BAS_SOME, "warning")])
    def test_action_btn_variant(self, access: AccessType, expected: str):
        """Can get action variant."""
        dist = FakeFileDistributionType(option=_make_dist("x"), other_options=[], access_type=access)
        assert dist.action_btn_variant == expected

    @pytest.mark.parametrize(
        ("access", "expected"), [(AccessType.PUBLIC, "far fa-download"), (AccessType.BAS_SOME, "far fa-lock-alt")]
    )
    def test_action_btn_icon(self, access: AccessType, expected: str):
        """Can get action icon."""
        dist = FakeFileDistributionType(option=_make_dist("x"), other_options=[], access_type=access)
        assert dist.action_btn_icon == expected

    def test_access_target(self):
        """Can get null action target."""
        dist = FakeFileDistributionType(option=_make_dist("x"), other_options=[], access_type=AccessType.PUBLIC)
        assert dist.access_target is None


class TestDistributionArcGisFeatureLayer:
    """Test ArcGIS Feature Layer catalogue distribution."""

    def test_init(self):
        """Can create a distribution."""
        main = _make_dist("https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+feature")
        others = [_make_dist("https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+feature")]

        dist = ArcGisFeatureLayer(main, others, access_type=AccessType.PUBLIC)

        # cov
        assert dist.format_type == DistributionType.ARCGIS_FEATURE_LAYER
        assert dist.size == "-"
        assert dist.item_link.href == main.transfer_option.online_resource.href
        assert dist.service_endpoint == others[0].transfer_option.online_resource.href
        assert isinstance(dist.action, Link)
        assert dist.action_btn_variant != ""
        assert dist.action_btn_icon != ""
        assert dist.access_target != ""

    def test_init_no_service(self):
        """Cannot create a distribution without the required additional service distribution."""
        main = _make_dist("https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+feature")
        others = [_make_dist("x")]

        with pytest.raises(
            ValueError, match="Required corresponding service option not found in resource distributions."
        ):
            ArcGisFeatureLayer(main, others, access_type=AccessType.PUBLIC)

    @pytest.mark.parametrize(
        ("main", "others", "expected"),
        [
            (
                _make_dist("https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+feature"),
                [_make_dist("https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+feature")],
                True,
            ),
            (
                _make_dist("https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+feature"),
                [_make_dist("x")],
                False,
            ),
            (
                _make_dist("x"),
                [_make_dist("https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+feature")],
                False,
            ),
            (_make_dist("x"), [_make_dist("y")], False),
        ],
    )
    def test_matches(self, main: RecordDistribution, others: list[Distribution], expected: bool):
        """Can determine if a record distribution matches this catalogue distribution."""
        result = ArcGisFeatureLayer.matches(main, others)
        assert result == expected


class TestDistributionArcGisOgcApiFeatures:
    """Test ArcGIS OGC Features Layer catalogue distribution."""

    def test_init(self):
        """Can create a distribution."""
        main = _make_dist("https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+feature+ogc")
        others = [_make_dist("https://metadata-resources.data.bas.ac.uk/media-types/x-service/ogc+api+feature")]

        dist = ArcGisOgcApiFeatures(main, others, access_type=AccessType.PUBLIC)

        # cov
        assert dist.format_type == DistributionType.ARCGIS_OGC_FEATURE_LAYER
        assert dist.size == "-"
        assert dist.item_link.href == main.transfer_option.online_resource.href
        assert dist.service_endpoint == others[0].transfer_option.online_resource.href
        assert isinstance(dist.action, Link)
        assert dist.action_btn_variant != ""
        assert dist.action_btn_icon != ""
        assert dist.access_target != ""

    def test_init_no_service(self):
        """Cannot create a distribution without the required additional service distribution."""
        main = _make_dist("https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+feature+ogc")
        others = [_make_dist("x")]

        with pytest.raises(
            ValueError, match="Required corresponding service option not found in resource distributions."
        ):
            ArcGisOgcApiFeatures(main, others, access_type=AccessType.PUBLIC)

    @pytest.mark.parametrize(
        ("main", "others", "expected"),
        [
            (
                _make_dist("https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+feature+ogc"),
                [_make_dist("https://metadata-resources.data.bas.ac.uk/media-types/x-service/ogc+api+feature")],
                True,
            ),
            (
                _make_dist("https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+feature+ogc"),
                [_make_dist("x")],
                False,
            ),
            (
                _make_dist("x"),
                [_make_dist("https://metadata-resources.data.bas.ac.uk/media-types/x-service/ogc+api+feature")],
                False,
            ),
            (_make_dist("x"), [_make_dist("y")], False),
        ],
    )
    def test_matches(self, main: RecordDistribution, others: list[Distribution], expected: bool):
        """Can determine if a record distribution matches this catalogue distribution."""
        result = ArcGisOgcApiFeatures.matches(main, others)
        assert result == expected


class TestDistributionArcGisVectorTileLayer:
    """Test ArcGIS Vector Tile Layer catalogue distribution."""

    def test_init(self):
        """Can create a distribution."""
        main = _make_dist("https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+tile+vector")
        others = [
            _make_dist("https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+tile+vector")
        ]

        dist = ArcGisVectorTileLayer(main, others, access_type=AccessType.PUBLIC)

        # cov
        assert dist.format_type == DistributionType.ARCGIS_VECTOR_TILE_LAYER
        assert dist.size == "-"
        assert dist.item_link.href == main.transfer_option.online_resource.href
        assert dist.service_endpoint == others[0].transfer_option.online_resource.href
        assert isinstance(dist.action, Link)
        assert dist.action_btn_variant != ""
        assert dist.action_btn_icon != ""
        assert dist.access_target != ""

    def test_init_no_service(self):
        """Cannot create a distribution without the required additional service distribution."""
        main = _make_dist("https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+tile+vector")
        others = [_make_dist("x")]

        with pytest.raises(
            ValueError, match="Required corresponding service option not found in resource distributions."
        ):
            ArcGisVectorTileLayer(main, others, access_type=AccessType.PUBLIC)

    @pytest.mark.parametrize(
        ("main", "others", "expected"),
        [
            (
                _make_dist("https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+tile+vector"),
                [
                    _make_dist(
                        "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+tile+vector"
                    )
                ],
                True,
            ),
            (
                _make_dist("https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+tile+vector"),
                [_make_dist("x")],
                False,
            ),
            (
                _make_dist("x"),
                [
                    _make_dist(
                        "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+tile+vector"
                    )
                ],
                False,
            ),
            (_make_dist("x"), [_make_dist("y")], False),
        ],
    )
    def test_matches(self, main: RecordDistribution, others: list[Distribution], expected: bool):
        """Can determine if a record distribution matches this catalogue distribution."""
        result = ArcGisVectorTileLayer.matches(main, others)
        assert result == expected


class TestDistributionGeoJson:
    """Test GeoJSON catalogue distribution."""

    def test_init(self):
        """Can create a distribution."""
        dist = GeoJson(
            option=_make_dist("https://www.iana.org/assignments/media-types/application/geo+json"),
            other_options=[],
            access_type=AccessType.PUBLIC,
        )

        assert dist.format_type == DistributionType.GEOJSON


class TestDistributionGeoPackage:
    """Test GeoPackage catalogue distribution."""

    @pytest.mark.parametrize(
        ("href", "format_type", "compressed"),
        [
            (
                "https://www.iana.org/assignments/media-types/application/geopackage+sqlite3",
                DistributionType.GEOPACKAGE,
                False,
            ),
            (
                "https://metadata-resources.data.bas.ac.uk/media-types/application/geopackage+sqlite3+zip",
                DistributionType.GEOPACKAGE_ZIP,
                True,
            ),
        ],
    )
    def test_init(self, href: str, format_type: DistributionType, compressed: bool):
        """Can create a distribution."""
        dist = GeoPackage(option=_make_dist(format_href=href), other_options=[], access_type=AccessType.PUBLIC)

        assert dist.format_type == format_type
        assert dist._compressed == compressed


class TestDistributionJpeg:
    """Test JPEG catalogue distribution."""

    def test_init(self):
        """Can create a distribution."""
        dist = Jpeg(option=_make_dist("https://jpeg.org/jpeg/"), other_options=[], access_type=AccessType.PUBLIC)
        assert dist.format_type == DistributionType.JPEG


class TestDistributionPdf:
    """Test PDF catalogue distribution."""

    @pytest.mark.parametrize(
        ("href", "format_type", "georeferenced"),
        [
            (
                "https://www.iana.org/assignments/media-types/application/pdf",
                DistributionType.PDF,
                False,
            ),
            (
                "https://metadata-resources.data.bas.ac.uk/media-types/application/pdf+geo",
                DistributionType.PDF_GEO,
                True,
            ),
        ],
    )
    def test_init(self, href: str, format_type: DistributionType, georeferenced: bool):
        """Can create a distribution."""
        dist = Pdf(option=_make_dist(format_href=href), other_options=[], access_type=AccessType.PUBLIC)

        assert dist.format_type == format_type
        assert dist._georeferenced == georeferenced


class TestDistributionPng:
    """Test PNG catalogue distribution."""

    def test_init(self):
        """Can create a distribution."""
        dist = Png(
            option=_make_dist("https://www.iana.org/assignments/media-types/image/png"),
            other_options=[],
            access_type=AccessType.PUBLIC,
        )
        assert dist.format_type == DistributionType.PNG


class TestDistributionShapefile:
    """Test Shapefile catalogue distribution."""

    def test_init(self):
        """Can create a distribution."""
        dist = Shapefile(
            option=_make_dist("https://metadata-resources.data.bas.ac.uk/media-types/application/vnd.shp+zip"),
            other_options=[],
            access_type=AccessType.PUBLIC,
        )
        assert dist.format_type == DistributionType.SHAPEFILE_ZIP
