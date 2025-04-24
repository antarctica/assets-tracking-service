import json
from datetime import date

from assets_tracking_service.lib.bas_data_catalogue.models.record import (
    DataQuality,
    Distribution,
    Identification,
    Metadata,
    Record,
    ReferenceSystemInfo,
)
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.common import (
    Address,
    Citation,
    Contact,
    ContactIdentity,
    Contacts,
    Date,
    Dates,
    Identifier,
    Identifiers,
    OnlineResource,
    Series,
)
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.data_quality import (
    DomainConsistency,
    Lineage,
)
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.distribution import Format, TransferOption
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.identification import (
    Aggregation,
    Aggregations,
    BoundingBox,
    Constraint,
    Constraints,
    Extent,
    ExtentGeographic,
    Extents,
    ExtentTemporal,
    GraphicOverview,
    GraphicOverviews,
    Maintenance,
    TemporalPeriod,
)
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.projection import Code
from assets_tracking_service.lib.bas_data_catalogue.models.record.enums import (
    AggregationAssociationCode,
    AggregationInitiativeCode,
    ConstraintRestrictionCode,
    ConstraintTypeCode,
    ContactRoleCode,
    DatePrecisionCode,
    HierarchyLevelCode,
    MaintenanceFrequencyCode,
    OnlineResourceFunctionCode,
    ProgressCode,
)

# A record for an ItemCatalogue instance with all supported fields for products.

record = Record(
    file_identifier="30825673-6276-4e5a-8a97-f97f2094cd25",
    hierarchy_level=HierarchyLevelCode.PRODUCT,
    metadata=Metadata(
        contacts=Contacts(
            [
                Contact(
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
                    role=[ContactRoleCode.POINT_OF_CONTACT],
                )
            ]
        ),
        date_stamp=date(2008, 11, 12),
    ),
    reference_system_info=ReferenceSystemInfo(
        code=Code(
            value="urn:ogc:def:crs:EPSG::4326",
            href="http://www.opengis.net/def/crs/EPSG/0/4326",
        ),
        version="6.18.3",
        authority=Citation(
            title="European Petroleum Survey Group (EPSG) Geodetic Parameter Registry",
            dates=Dates(publication=Date(date=date(2008, 11, 12))),
            contacts=Contacts(
                [
                    Contact(
                        organisation=ContactIdentity(name="European Petroleum Survey Group"),
                        email="EPSGadministrator@iogp.org",
                        online_resource=OnlineResource(
                            href="https://www.epsg-registry.org/",
                            title="EPSG Geodetic Parameter Dataset",
                            description="The EPSG Geodetic Parameter Dataset is a structured dataset of Coordinate Reference Systems and Coordinate Transformations, accessible through this online registry.",
                            function=OnlineResourceFunctionCode.INFORMATION,
                        ),
                        role=[ContactRoleCode.PUBLISHER],
                    )
                ]
            ),
        ),
    ),
    identification=Identification(
        title="Test Resource - Product with all supported fields",
        dates=Dates(
            creation=Date(date=date(2023, 10, 1), precision=DatePrecisionCode.YEAR),
            publication=Date(date=date(2023, 10, 1)),
            revision=Date(date=date(2023, 10, 1)),
            adopted=Date(date=date(2023, 10, 1)),
            deprecated=Date(date=date(2023, 10, 1)),
            distribution=Date(date=date(2023, 10, 1)),
            expiry=Date(date=date(2023, 10, 1)),
            in_force=Date(date=date(2023, 10, 1)),
            last_revision=Date(date=date(2023, 10, 1)),
            last_update=Date(date=date(2023, 10, 1)),
            next_update=Date(date=date(2023, 10, 1)),
            released=Date(date=date(2023, 10, 1), precision=DatePrecisionCode.MONTH),
            superseded=Date(date=date(2023, 10, 1)),
            unavailable=Date(date=date(2023, 10, 1)),
            validity_begins=Date(date=date(2023, 10, 1)),
            validity_expires=Date(date=date(2023, 10, 1)),
        ),
        edition="1.2.3",
        identifiers=Identifiers(
            [
                Identifier(
                    identifier="30825673-6276-4e5a-8a97-f97f2094cd25",
                    href="https://data.bas.ac.uk/items/30825673-6276-4e5a-8a97-f97f2094cd25",
                    namespace="data.bas.ac.uk",
                ),
                Identifier(
                    identifier="https://gitlab.data.bas.ac.uk/MAGIC/test/-/issues/123",
                    href="https://gitlab.data.bas.ac.uk/MAGIC/test/-/issues/123",
                    namespace="gitlab.data.bas.ac.uk",
                ),
                Identifier(
                    identifier="maps/test123",
                    href="https://data.bas.ac.uk/maps/test123",
                    namespace="alias.data.bas.ac.uk",
                ),
                Identifier(
                    identifier="maps/test123alt",
                    href="https://data.bas.ac.uk/maps/test123alt",
                    namespace="alias.data.bas.ac.uk",
                ),
                Identifier(
                    identifier="10.123/30825673-6276-4e5a-8a97-f97f2094cd25",
                    href="https://doi.org/10.123/30825673-6276-4e5a-8a97-f97f2094cd25",
                    namespace="doi",
                ),
                Identifier(
                    identifier="10.123/test123",
                    href="https://doi.org/10.123/test123",
                    namespace="doi",
                ),
                Identifier(
                    identifier="123-1",
                    namespace="isbn",
                ),
                Identifier(
                    identifier="234-1",
                    namespace="isbn",
                ),
            ]
        ),
        series=Series(name="Test Series", edition="1"),
        abstract="""
I spent so much time making sweet jam in the kitchen that it's hard to hear anything over the clatter of the
tin bath. I shall hide behind the couch. _(Guy's a pro.)_

Interfere? Michael: I'm sorry, have we met? She calls it a mayonegg. The only thing more terrifying than the
escaped lunatic's hook was his twisted call…

> Heyyyyy campers!

I didn't get into this business to please sophomore Tracy Schwartzman, so… onward and upward. On… Why, Tracy?! Why?!!

* Say something that will terrify me.
* Lindsay: Kiss me.
* Tobias: No, that didn't do it.

No, I was ashamed to be **SEEN** with you. I like being **WITH** you.

1. Chickens don't clap!
2. Am I in two thirds of a hospital room?

You're a good guy, mon frere. That means brother in French. I don't know how I know that. I took four years of Spanish.

See [here](#) for more good stuff.

The guy runs a prison, he can have any piece of cake he wants. In fact, it was a box of Oscar's legally obtained
medical marijuana. Primo bud. Real sticky weed. So, what do you say? We got a basket full of father-son fun here.
What's Kama Sutra oil? Maybe it's not for us. He… she… what's the difference? Oh hear, hear. In the dark, it all looks
the same. Well excuse me, Judge Reinhold!
        """,
        purpose="""I shall hide behind the couch. _(Guy's a pro.)_ No, I was ashamed to be **SEEN** with you. I like being **WITH** you!""",
        spatial_resolution=1_234_567_890,
        contacts=Contacts(
            [
                Contact(
                    individual=ContactIdentity(
                        name="Connie Watson",
                        href="https://sandbox.orcid.org/0000-0001-8373-6934",
                        title="orcid",
                    ),
                    organisation=ContactIdentity(
                        name="Mapping and Geographic Information Centre, British Antarctic Survey",
                        href="https://ror.org/01rhff309",
                        title="ror",
                    ),
                    phone="+44 (0)1223 221400",
                    email="conwat@bas.ac.uk",
                    address=Address(
                        delivery_point="British Antarctic Survey, High Cross, Madingley Road",
                        city="Cambridge",
                        administrative_area="Cambridgeshire",
                        postal_code="CB3 0ET",
                        country="United Kingdom",
                    ),
                    online_resource=OnlineResource(
                        href="https://www.bas.ac.uk/people/conwat",
                        title="Connie Watson - BAS public website",
                        description="Personal profile for Connie Watson from the British Antarctic Survey (BAS) public website.",
                        function=OnlineResourceFunctionCode.INFORMATION,
                    ),
                    role=[ContactRoleCode.AUTHOR],
                ),
                Contact(
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
                    role=[ContactRoleCode.AUTHOR, ContactRoleCode.PUBLISHER, ContactRoleCode.POINT_OF_CONTACT],
                ),
            ]
        ),
        constraints=Constraints(
            [
                Constraint(
                    type=ConstraintTypeCode.ACCESS,
                    restriction_code=ConstraintRestrictionCode.UNRESTRICTED,
                    statement="Open Access (Anonymous)",
                ),
                Constraint(
                    type=ConstraintTypeCode.USAGE,
                    restriction_code=ConstraintRestrictionCode.LICENSE,
                    href="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
                    statement="This information is licensed under the Open Government Licence v3.0. To view this licence, visit https://www.nationalarchives.gov.uk/doc/open-government-licence/.",
                ),
            ]
        ),
        graphic_overviews=GraphicOverviews(
            [
                GraphicOverview(
                    identifier="overview",
                    description="Overview",
                    href="https://cdn.web.bas.ac.uk/add-catalogue/0.0.0/img/items/e46046cc-7375-444a-afaa-3356c278d446/1005-thumbnail.png",
                    mime_type="image/png",
                )
            ]
        ),
        extents=Extents(
            [
                Extent(
                    identifier="bounding",
                    geographic=ExtentGeographic(
                        bounding_box=BoundingBox(
                            west_longitude=1.0, east_longitude=2.0, south_latitude=3.0, north_latitude=4.0
                        )
                    ),
                    temporal=ExtentTemporal(
                        period=TemporalPeriod(
                            start=Date(date=date(2023, 10, 1)),
                            end=Date(date=date(2023, 10, 2)),
                        )
                    ),
                )
            ]
        ),
        aggregations=Aggregations(
            [
                Aggregation(
                    identifier=Identifier(
                        identifier="dbe5f712-696a-47d8-b4a7-3b173e47e3ab",
                        href="https://data.bas.ac.uk/items/dbe5f712-696a-47d8-b4a7-3b173e47e3ab",
                        namespace="data.bas.ac.uk",
                    ),
                    association_type=AggregationAssociationCode.LARGER_WORK_CITATION,
                    initiative_type=AggregationInitiativeCode.COLLECTION,
                )
            ]
        ),
        maintenance=Maintenance(
            progress=ProgressCode.ON_GOING,
            maintenance_frequency=MaintenanceFrequencyCode.AS_NEEDED,
        ),
        other_citation_details="Produced by the Mapping and Geographic Information Centre, British Antarctic Survey, 2025, version 1, https://data.bas.ac.uk/maps/1005.",
        supplemental_information=json.dumps({"width": "210", "height": "297"}),
    ),
    data_quality=DataQuality(
        lineage=Lineage(
            statement="""
Do you guys know where I could get one of those gold necklaces with the T on it? That's a cross. Across from where? Could it be love? No, it's the opposite. I think that's one of Mom's little fibs, you know, like I'll sacrifice anything for my children. He… she… what's the difference? Oh hear, hear. In the dark, it all looks the same. I never thought I'd miss a hand so much!

I've been in the film business for a while but I just cant seem to get one in the can. You don't want a hungry dove down your pants. We need a name. Maybe 'Operation Hot Mother'. I'm going to buy you the single healthiest call girl this town has ever seen. What a fun, sexy time for you.

Yes, Annyong. Your name is Annyong! We all know you're Annyong! Mister gay is bleeding! Mister gay! Gosh Mom… after all these years, God's not going to take a call from you. Do the right thing here. String this blind girl along so that dad doesn't have to pay his debt to society.

That's so you can videotape it when they put you in a naked pyramid and point to your Charlie Browns. No, I was ashamed to be SEEN with you. I like being WITH you. Everything they do is so dramatic and flamboyant. It just makes me want to set myself on fire. The Army had half a day. You just made a fool out of yourself in front of T-Bone. How about a turtle? I've always loved those leathery little snappy faces.
        """
        ),
        domain_consistency=[
            DomainConsistency(
                specification=Citation(
                    title="British Antarctic Survey (BAS) Mapping and Geographic Information Centre (MAGIC) Discovery Metadata Profile",
                    href="https://metadata-standards.data.bas.ac.uk/profiles/magic-discovery-v1/",
                    dates=Dates(publication=Date(date=date(2024, 11, 1))),
                    edition="1",
                    contacts=Contacts(
                        [
                            Contact(
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
                                role=[ContactRoleCode.PUBLISHER],
                            )
                        ]
                    ),
                ),
                explanation="Resource within scope of British Antarctic Survey (BAS) Mapping and Geographic Information Centre (MAGIC) Discovery Metadata Profile.",
                result=True,
            )
        ],
    ),
    distribution=[
        Distribution(
            distributor=Contact(
                organisation=ContactIdentity(
                    name="Environmental Systems Research Institute", href="https://ror.org/0428exr50", title="ror"
                ),
                address=Address(
                    delivery_point="380 New York Street",
                    city="Redlands",
                    administrative_area="California",
                    postal_code="92373",
                    country="United States of America",
                ),
                online_resource=OnlineResource(
                    href="https://www.esri.com",
                    title="GIS Mapping Software, Location Intelligence & Spatial Analytics | Esri",
                    description="Corporate website for Environmental Systems Research Institute (ESRI).",
                    function=OnlineResourceFunctionCode.INFORMATION,
                ),
                role=[ContactRoleCode.DISTRIBUTOR],
            ),
            format=Format(
                format="ArcGIS Feature Service",
                href="https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+feature",
            ),
            transfer_option=TransferOption(
                online_resource=OnlineResource(
                    href="x",
                    function=OnlineResourceFunctionCode.DOWNLOAD,
                    title="ArcGIS Online",
                    description="Access information as an ArcGIS feature service.",
                )
            ),
        ),
        Distribution(
            distributor=Contact(
                organisation=ContactIdentity(
                    name="Environmental Systems Research Institute", href="https://ror.org/0428exr50", title="ror"
                ),
                address=Address(
                    delivery_point="380 New York Street",
                    city="Redlands",
                    administrative_area="California",
                    postal_code="92373",
                    country="United States of America",
                ),
                online_resource=OnlineResource(
                    href="https://www.esri.com",
                    title="GIS Mapping Software, Location Intelligence & Spatial Analytics | Esri",
                    description="Corporate website for Environmental Systems Research Institute (ESRI).",
                    function=OnlineResourceFunctionCode.INFORMATION,
                ),
                role=[ContactRoleCode.DISTRIBUTOR],
            ),
            format=Format(
                format="ArcGIS Feature Layer",
                href="https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+feature",
            ),
            transfer_option=TransferOption(
                online_resource=OnlineResource(
                    href="x",
                    function=OnlineResourceFunctionCode.DOWNLOAD,
                    title="ArcGIS Online",
                    description="Access information as an ArcGIS feature layer.",
                )
            ),
        ),
        Distribution(
            distributor=Contact(
                organisation=ContactIdentity(
                    name="Environmental Systems Research Institute", href="https://ror.org/0428exr50", title="ror"
                ),
                address=Address(
                    delivery_point="380 New York Street",
                    city="Redlands",
                    administrative_area="California",
                    postal_code="92373",
                    country="United States of America",
                ),
                online_resource=OnlineResource(
                    href="https://www.esri.com",
                    title="GIS Mapping Software, Location Intelligence & Spatial Analytics | Esri",
                    description="Corporate website for Environmental Systems Research Institute (ESRI).",
                    function=OnlineResourceFunctionCode.INFORMATION,
                ),
                role=[ContactRoleCode.DISTRIBUTOR],
            ),
            format=Format(
                format="OGC API Features Service",
                href="https://metadata-resources.data.bas.ac.uk/media-types/x-service/ogc+api+feature",
            ),
            transfer_option=TransferOption(
                online_resource=OnlineResource(
                    href="y",
                    function=OnlineResourceFunctionCode.DOWNLOAD,
                    title="ArcGIS Online",
                    description="Access information as an OGC API feature service.",
                )
            ),
        ),
        Distribution(
            distributor=Contact(
                organisation=ContactIdentity(
                    name="Environmental Systems Research Institute", href="https://ror.org/0428exr50", title="ror"
                ),
                address=Address(
                    delivery_point="380 New York Street",
                    city="Redlands",
                    administrative_area="California",
                    postal_code="92373",
                    country="United States of America",
                ),
                online_resource=OnlineResource(
                    href="https://www.esri.com",
                    title="GIS Mapping Software, Location Intelligence & Spatial Analytics | Esri",
                    description="Corporate website for Environmental Systems Research Institute (ESRI).",
                    function=OnlineResourceFunctionCode.INFORMATION,
                ),
                role=[ContactRoleCode.DISTRIBUTOR],
            ),
            format=Format(
                format="ArcGIS OGC Feature Layer",
                href="https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+feature+ogc",
            ),
            transfer_option=TransferOption(
                online_resource=OnlineResource(
                    href="y",
                    function=OnlineResourceFunctionCode.DOWNLOAD,
                    title="ArcGIS Online",
                    description="Access information as an ArcGIS OGC feature layer.",
                )
            ),
        ),
    ],
)
