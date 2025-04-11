import pytest

from assets_tracking_service.lib.bas_data_catalogue.models.item.base.elements import Link
from assets_tracking_service.lib.bas_data_catalogue.models.item.catalogue.distributions import (
    ArcGisFeatureLayer,
    ArcGisOgcApiFeatures,
    Distribution,
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
    def access_target(self) -> None:
        """Access target."""
        return None


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


class TestDistributionArcGisFeatureLayer:
    """Test ArcGIS Feature Layer catalogue distribution."""

    def test_init(self):
        """Can create a distribution."""
        main = _make_dist("https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+feature")
        others = [_make_dist("https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+feature")]

        dist = ArcGisFeatureLayer(main, others)

        # cov
        assert dist.format_type == DistributionType.ARCGIS_FEATURE_LAYER
        assert dist.size == "N/A"
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
            ArcGisFeatureLayer(main, others)

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

        dist = ArcGisOgcApiFeatures(main, others)

        # cov
        assert dist.format_type == DistributionType.ARCGIS_OGC_FEATURE_LAYER
        assert dist.size == "N/A"
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
            ArcGisOgcApiFeatures(main, others)

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
