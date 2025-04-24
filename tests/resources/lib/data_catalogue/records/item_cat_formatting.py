from datetime import date

from assets_tracking_service.lib.bas_data_catalogue.models.record import (
    Identification,
    Metadata,
    Record,
)
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.common import (
    Address,
    Contact,
    ContactIdentity,
    Contacts,
    Date,
    Dates,
    Identifier,
    Identifiers,
    OnlineResource,
)
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.identification import (
    Aggregation,
    Aggregations,
    Constraint,
    Constraints,
)
from assets_tracking_service.lib.bas_data_catalogue.models.record.enums import (
    AggregationAssociationCode,
    AggregationInitiativeCode,
    ConstraintRestrictionCode,
    ConstraintTypeCode,
    ContactRoleCode,
    DatePrecisionCode,
    HierarchyLevelCode,
    OnlineResourceFunctionCode,
)

# A record for an ItemCatalogue instance with all supported fields for products.

record = Record(
    file_identifier="e0df252c-fb8b-49ff-9711-f91831b66ea2",
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
    identification=Identification(
        title="Test Resource - Product to test **Markdown** _formatting_",
        dates=Dates(
            creation=Date(date=date(2023, 10, 1), precision=DatePrecisionCode.YEAR),
        ),
        edition="1",
        identifiers=Identifiers(
            [
                Identifier(
                    identifier="e0df252c-fb8b-49ff-9711-f91831b66ea2",
                    href="https://data.bas.ac.uk/items/e0df252c-fb8b-49ff-9711-f91831b66ea2",
                    namespace="data.bas.ac.uk",
                ),
            ]
        ),
        abstract="""
Pargraph: I spent so much time making sweet jam in the kitchen that it's hard to hear anything over the clatter of the
tin bath. I shall hide behind the couch.

Another paragraph: Interfere? Michael: I'm sorry, have we met? She calls it a mayonegg. The only thing more terrifying than the
escaped lunatic's hook was his twisted call…

Headings:

# Heading 1
...

## Heading 2
...

### Heading 3
...

#### Heading 4
...

##### Heading 5
...

###### Heading 6
...

Link: [Some link](#).

Bold: No, I was ashamed to be **SEEN** with you. I like being **WITH** you.

Italics: _(Guy's a pro.)_

Keyboard shortcut: <kbd>Cmd</kbd>+<kbd>v</kbd>

Inline code: `print("Hello Rencia.")`

Blockquote:
> Heyyyyy campers!

Unordered list:

* Say something that will terrify me.
* Lindsay: Kiss me.
* Tobias: No, that didn't do it.

Ordered list:

1. Chickens don't clap!
2. Am I in two thirds of a hospital room?

Code block:

```
def print_hello():
    print("Hello Rencia.")
```

Preformatted:

<pre>
lines = [
    "Probably out there without a flipper, swimming around in a circle, freaking out his whole family.",
    "We'll have to find something to do so that people can look at you without wanting to kill themselves.",
    "I'm gonna build me an airport, put my name on it. Why, Michael? So you can fly away from your feelings?",
]
</pre>

Table:

| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Row 1    | Row 1    | Row 1    |
| Row 2    | Row 2    | Row 2    |

Horizontal rule:

I didn't get into this business to please sophomore Tracy Schwartzman, so… onward and upward. On… Why, Tracy?! Why?!!
---
You're a good guy, mon frere. That means brother in French.

Markdown Image:

![I don't know how I know that. I took four years of Spanish.](https://images.unsplash.com/photo-1494216928456-ae75fd96603d?q=80&w=1080&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D)

HTML figure with caption:

<figure>
    <img src="https://images.unsplash.com/photo-1465060780892-48505fc8f941?q=80&w=1080&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D" alt="marmite" />
    <figcaption>We need a name. Maybe 'Operation Hot Mother'.</figcaption>
</figure>
        """,
        purpose="""
I shall hide behind the couch. _(Guy's a pro.)_

* Say something that will terrify me with [a link](#).

No, I was ashamed to be **SEEN** with you. I like being **WITH** you!

1. Chickens don't clap!
""",
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
        other_citation_details="""
I shall hide behind the couch. _(Guy's a pro.)_

* Say something that will terrify me with [a link](#).

No, I was ashamed to be **SEEN** with you. I like being **WITH** you!

1. Chickens don't clap!
        """,
    ),
)
