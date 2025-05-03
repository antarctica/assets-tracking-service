import json
from datetime import date

from resources.lib.data_catalogue.records.utils import make_record

from assets_tracking_service.lib.bas_data_catalogue.models.record import Distribution
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.common import (
    Address,
    Contact,
    ContactIdentity,
    Date,
    Identifier,
    OnlineResource,
    Series,
)
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.distribution import TransferOption
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.identification import (
    Constraint,
    Constraints,
    Extent,
    Extents,
    GraphicOverview,
    GraphicOverviews,
    Maintenance,
)
from assets_tracking_service.lib.bas_data_catalogue.models.record.enums import (
    ConstraintRestrictionCode,
    ConstraintTypeCode,
    ContactRoleCode,
    DatePrecisionCode,
    HierarchyLevelCode,
    MaintenanceFrequencyCode,
    OnlineResourceFunctionCode,
    ProgressCode,
)
from assets_tracking_service.lib.bas_data_catalogue.models.record.presets.extents import make_bbox_extent

# A record to demonstrate a published map.

abstract = """
This double-sided topographic map provides an overview, and comparison, of both polar regions at the same scale and
with the same geographical extent. Smaller panels show seasonal sea-ice extent for both areas; Arctic climatic and
bio-geographical boundaries, and Antarctica's relationship to the other southern continents.

Side A: Antarctica. A topographic map of Antarctica, including: Coastline and ice shelves, bathymetry, ice/rock limits,
contours, key mountain summits and hill-shaded terrain, and scientific research stations.

Side B: The Arctic. A topographic map of the Arctic, including: Coastline: bathymetry, contours, key mountain summits
and hill-shaded terrain, major rivers and lakes, and glaciers and ice caps. It also shows major towns, transport
networks, airports and national boundaries.

The folded map comes either with an Antarctic card cover (snowy mountains) or an Arctic cover (reindeer). Both
versions are identical inside and have the same ISBN.

Limits: 90° S - 60° S and 90° N - 60° N (all Antarctica south of 60°S and the Arctic north of 60°N).
"""

record = make_record(
    file_identifier="53ed9f6a-2d68-46c2-b5c5-f15422aaf5b2",
    hierarchy_level=HierarchyLevelCode.PRODUCT,
    title="Test Resource - Published map (Antarctica and the Arctic)",
    abstract=abstract,
    purpose="Item to test published maps are presented correctly.",
)
record.identification.identifiers.append(Identifier(identifier="978-0-85665-230-1 (Folded)", namespace="isbn"))
record.identification.identifiers.append(Identifier(identifier="978-0-85665-231-8 (Flat)", namespace="isbn"))
record.identification.edition = "5"
record.identification.series = Series(name="BAS Miscellaneous", edition="15")
record.identification.dates.creation = Date(date=date(year=2020, month=1, day=1), precision=DatePrecisionCode.YEAR)
record.identification.dates.published = Date(date=date(year=2020, month=1, day=1), precision=DatePrecisionCode.YEAR)
record.identification.dates.released = Date(date=date(year=2020, month=1, day=1), precision=DatePrecisionCode.YEAR)
record.identification.spatial_resolution = 10_000_000
record.identification.supplemental_information = json.dumps({"width": 890, "height": 840})
record.identification.maintenance = Maintenance(
    progress=ProgressCode.COMPLETED, maintenance_frequency=MaintenanceFrequencyCode.NOT_PLANNED
)
record.identification.graphic_overviews = GraphicOverviews(
    [
        GraphicOverview(
            identifier="overview",
            href="https://www.bas.ac.uk/wp-content/uploads/2023/03/Cover-both-lower-res-726x600.png",
            mime_type="image/png",
        )
    ]
)
record.identification.constraints = Constraints(
    [
        Constraint(
            type=ConstraintTypeCode.ACCESS,
            restriction_code=ConstraintRestrictionCode.UNRESTRICTED,
            statement="Open Access (Anonymous)",
        ),
        Constraint(
            type=ConstraintTypeCode.USAGE,
            restriction_code=ConstraintRestrictionCode.LICENSE,
            href="https://metadata-resources.data.bas.ac.uk/licences/all-rights-reserved-v1/",
            statement="All rights for this information are reserved. View the (Local) All Rights Reserved v1 licence, https://metadata-resources.data.bas.ac.uk/licences/operations-mapping-v1/, for more information.",
        ),
    ]
)
record.identification.extents = Extents(
    [Extent(identifier="bounding", geographic=make_bbox_extent(-180, 180, -90, -60))]
)
record.identification.contacts.append(
    Contact(
        individual=ContactIdentity(
            name="Gerrish, Laura",
            href="https://orcid.org/0000-0003-1410-9122",
            title="orcid",
        ),
        organisation=ContactIdentity(
            name="British Antarctic Survey",
            href="https://ror.org/01rhff309",
            title="ror",
        ),
        email="lauger@bas.ac.uk",
        address=Address(
            delivery_point="British Antarctic Survey, High Cross, Madingley Road",
            city="Cambridge",
            administrative_area="Cambridgeshire",
            postal_code="CB3 0ET",
            country="United Kingdom",
        ),
        online_resource=OnlineResource(
            href="https://www.bas.ac.uk/profile/lauger",
            title="Personal profile for Laura Gerrish - BAS public website",
            description="Staff profile for Laura Gerrish from the British Antarctic Survey (BAS) public website.",
            function=OnlineResourceFunctionCode.INFORMATION,
        ),
        role=[ContactRoleCode.AUTHOR],
    )
)
record.distribution = [
    Distribution(
        distributor=Contact(
            organisation=ContactIdentity(
                name="Mapping and Geographic Information Centre, British Antarctic Survey",
                href="https://ror.org/01rhff309",
                title="ror",
            ),
            phone="+44 (0)1223 221400",
            email="magic@bas.ac.uk",
            address=Address(
                delivery_point="British Antarctic Survey, High Cross, Madingley Road",
                city="Cambridge",
                administrative_area="Cambridgeshire",
                postal_code="CB3 0ET",
                country="United Kingdom",
            ),
            online_resource=OnlineResource(
                href="https://www.bas.ac.uk/teams/magic",
                title="Mapping and Geographic Information Centre (MAGIC) - BAS public website",
                description="General information about the BAS Mapping and Geographic Information Centre (MAGIC) from the British Antarctic Survey (BAS) public website.",
                function=OnlineResourceFunctionCode.INFORMATION,
            ),
            role=[ContactRoleCode.DISTRIBUTOR],
        ),
        transfer_option=TransferOption(
            online_resource=OnlineResource(
                href="https://www.bas.ac.uk/data/our-data/maps/how-to-order-a-map/",
                function=OnlineResourceFunctionCode.DOWNLOAD,
                title="GeoJSON",
                description="Access information as a GeoJSON file.",
            ),
        ),
    )
]
