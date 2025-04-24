from datetime import date

from assets_tracking_service.lib.bas_data_catalogue.models.record import (
    DataQuality,
    Identification,
    Metadata,
    Record,
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
)
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.data_quality import (
    DomainConsistency,
)
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

# A record for an ItemCatalogue instance with all supported fields for collections.

record = Record(
    file_identifier="dbe5f712-696a-47d8-b4a7-3b173e47e3ab",
    hierarchy_level=HierarchyLevelCode.COLLECTION,
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
    identification=Identification(
        title="Test Resource - Collection with all supported fields",
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
        edition="1",
        identifiers=Identifiers(
            [
                Identifier(
                    identifier="dbe5f712-696a-47d8-b4a7-3b173e47e3ab",
                    href="https://data.bas.ac.uk/items/dbe5f712-696a-47d8-b4a7-3b173e47e3ab",
                    namespace="data.bas.ac.uk",
                ),
                Identifier(
                    identifier="https://gitlab.data.bas.ac.uk/MAGIC/test/-/issues/123",
                    href="https://gitlab.data.bas.ac.uk/MAGIC/test/-/issues/123",
                    namespace="gitlab.data.bas.ac.uk",
                ),
                Identifier(
                    identifier="collections/test123",
                    href="https://data.bas.ac.uk/collections/test123",
                    namespace="alias.data.bas.ac.uk",
                ),
                Identifier(
                    identifier="collections/test123alt",
                    href="https://data.bas.ac.uk/collections/test123alt",
                    namespace="alias.data.bas.ac.uk",
                ),
                Identifier(
                    identifier="10.123/dbe5f712-696a-47d8-b4a7-3b173e47e3ab",
                    href="https://doi.org/10.123/dbe5f712-696a-47d8-b4a7-3b173e47e3ab",
                    namespace="doi",
                ),
                Identifier(
                    identifier="10.123/test123",
                    href="https://doi.org/10.123/test123",
                    namespace="doi",
                ),
            ]
        ),
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
                    role=[ContactRoleCode.PUBLISHER, ContactRoleCode.POINT_OF_CONTACT],
                )
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
                        identifier="30825673-6276-4e5a-8a97-f97f2094cd25",
                        href="https://data.bas.ac.uk/items/30825673-6276-4e5a-8a97-f97f2094cd25",
                        namespace="data.bas.ac.uk",
                    ),
                    association_type=AggregationAssociationCode.IS_COMPOSED_OF,
                    initiative_type=AggregationInitiativeCode.COLLECTION,
                ),
                Aggregation(
                    identifier=Identifier(
                        identifier="e0df252c-fb8b-49ff-9711-f91831b66ea2",
                        href="https://data.bas.ac.uk/items/e0df252c-fb8b-49ff-9711-f91831b66ea2",
                        namespace="data.bas.ac.uk",
                    ),
                    association_type=AggregationAssociationCode.IS_COMPOSED_OF,
                    initiative_type=AggregationInitiativeCode.COLLECTION,
                ),
            ]
        ),
        maintenance=Maintenance(
            progress=ProgressCode.ON_GOING,
            maintenance_frequency=MaintenanceFrequencyCode.AS_NEEDED,
        ),
    ),
    data_quality=DataQuality(
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
)
