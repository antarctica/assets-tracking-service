import json
from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta

from assets_tracking_service.lib.bas_data_catalogue.models.item.base import ItemSummaryBase, md_as_html
from assets_tracking_service.lib.bas_data_catalogue.models.item.base.elements import Extent as ItemExtent
from assets_tracking_service.lib.bas_data_catalogue.models.item.base.elements import Link, unpack
from assets_tracking_service.lib.bas_data_catalogue.models.item.catalogue.enums import ResourceTypeIcon
from assets_tracking_service.lib.bas_data_catalogue.models.record import RecordSummary
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.common import Date
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.common import Dates as RecordDates
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.identification import (
    Aggregations as RecordAggregations,
)
from assets_tracking_service.lib.bas_data_catalogue.models.record.enums import (
    AggregationAssociationCode,
    AggregationInitiativeCode,
    DatePrecisionCode,
    DateTypeCode,
    HierarchyLevelCode,
)


def format_date(value: Date, relative_to: datetime | None = None) -> str:
    """
    Format date to string.

    Uses the 'DD MMM YYYY' (e.g. 01 Oct 2023) format for dates where precision allows.
    Date times within 24 hours of now (or other specified time) return the date and time, otherwise the time is omitted.
    """
    relative_to = relative_to or datetime.now(tz=UTC)

    if not isinstance(value, Date):
        msg = "Value must be a record Date object."
        raise TypeError(msg) from None

    if isinstance(value.date, datetime) and not relative_to - value.date > timedelta(hours=24):
        return value.date.strftime("%d %B %Y %H:%M:%S %Z")
    if isinstance(value.date, date) and value.precision is DatePrecisionCode.YEAR:
        return value.date.strftime("%Y")
    if isinstance(value.date, date) and value.precision is DatePrecisionCode.MONTH:
        return value.date.strftime("%B %Y")
    return value.date.strftime("%d %B %Y")


class ItemSummaryCatalogue(ItemSummaryBase):
    """
    Summary of a resource within the BAS Data Catalogue.

    Catalogue item summaries provide additional context for base summaries for use when presenting search results or
    resources related to the current item within the BAS Data Catalogue website.
    """

    def __init__(self, record_summary: RecordSummary) -> None:
        super().__init__(record_summary)

    @property
    def title_html(self) -> str | None:
        """Title with Markdown formatting, if present, encoded as HTML."""
        return md_as_html(self.title_md)

    @property
    def _resource_type_icon(self) -> str:
        """Resource type icon."""
        return ResourceTypeIcon[self.resource_type.name].value

    @property
    def _date(self) -> str | None:
        """Formatted date."""
        return format_date(self.date) if self.date else None

    @property
    def fragments(self) -> list[tuple[str | None, str | None, str]]:
        """UI fragments (icons and labels) for item summary."""
        fragments = [(self._resource_type_icon, None, self.resource_type.value.capitalize())]
        if self.edition and self.resource_type != HierarchyLevelCode.COLLECTION:
            fragments.append((None, "Edition", self.edition))
        if self._date and self.resource_type != HierarchyLevelCode.COLLECTION:
            fragments.append((None, "Published", self._date))
        return fragments

    @property
    def href_graphic(self) -> str:
        """Item graphic, or generic default (bas roundel)."""
        default = (
            "data:image/png;base64, iVBORw0KGgoAAAANSUhEUgAAALQAAAC0CAMAAAAKE/YAAAAC+lBMVEUAAADu7u739/fz8/Pt7e3w"
            "8PDv7+/t7e3u7u7u7u7t7e3v7+/u7u7u7u7v7+/x8fH////9/f3s7Ozu7u7s7Ozv7+/u7u7v7+/u7u7u7u7u7u7u7u7u7u7v7+/"
            "////u7u709PTu7u76+vrv7+/x8fHt7e3v7+/u7u7u7u6AgIDs7Ozv7+/u7u7v7+/u7u7u7u7u7u7u7u7u7u7////u7u7u7u7u7u"
            "7p6enr6+vv7+/s7Ozu7u7v7+/u7u7////u7u7t7e3u7u7y8vLs7Oz19fXs7Ozw8PDu7u74+Pjv7+/8/Pzu7u7t7e3u7u7////v7"
            "+/w8PDu7u7q6uru7u7v7+/v7+/v7+/v7+/v7+/u7u7v7+/u7u7u7u7t7e3u7u7+/v7v7+/z8/Pu7u7u7u7y8vLu7u7u7u7u7u7u"
            "7u7u7u7////09PTw8PD29vb5+fnr6+vt7e3u7u7t7e3u7u7u7u7////t7e3u7u7v7+/t7e37+/vu7u7u7u7u7u7////u7u7w8PD"
            "v7+/x8fHu7u7v7+/////u7u7v7+/s7Ozu7u7u7u7u7u7v7+/u7u7x8fHu7u7u7u7y8vLu7u7t7e3u7u7v7+/u7u7v7+/t7e3x8f"
            "Hu7u7u7u7t7e3q6urv7+/u7u7u7u7u7u7u7u7u7u7v7+/u7u7v7+/t7e3v7+/w8PDs7Ozu7u7u7u719fXu7u7x8fHu7u7u7u7u7"
            "u7v7+/u7u7v7+/t7e3u7u7s7Ozu7u7u7u7v7+/u7u7v7+/s7Ozt7e3////v7+/v7+/u7u7u7u7////u7u7v7+/u7u7u7u7u7u7u"
            "7u7t7e3t7e3t7e3v7+/v7+/v7+/v7+/u7u7u7u7u7u7u7u7u7u7t7e3t7e3v7+/w8PDt7e3b29vr6+vz8/Pt7e3o6Oi/v7/w8PD"
            "u7u7y8vLw8PDt7e3V1dXf39/u7u7t7e3t7e3t7e3t7e3q6urt7e3t7e3h4eHt7e3s7Oyqqqru7u7n5+fr6+vt7e3u7u7t7e3u7u"
            "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"
        )
        return super().href_graphic if super().href_graphic else default


class Aggregations:
    """
    Aggregations.

    Container for aggregations formatted as links and grouped by type.
    """

    def __init__(self, aggregations: RecordAggregations, get_summary: Callable[[str], RecordSummary]) -> None:
        self._aggregations = aggregations
        self._summaries = self._generate_summaries(get_summary)

    def _generate_summaries(self, get_summary: Callable[[str], RecordSummary]) -> dict[str, ItemSummaryCatalogue]:
        """Generate item summaries for aggregations indexed by resource identifier."""
        summaries = {}
        for aggregation in self._aggregations:
            identifier = aggregation.identifier.identifier
            summaries[identifier] = ItemSummaryCatalogue(get_summary(identifier))
        return summaries

    def __len__(self) -> int:
        """Count."""
        return len(self._aggregations)

    @staticmethod
    def as_links(summaries: list[ItemSummaryCatalogue]) -> list[Link]:
        """Structure item summaries as generic links."""
        return [Link(value=summary.title_html, href=summary.href) for summary in summaries]

    def _filter(
        self,
        namespace: str | None = None,
        associations: AggregationAssociationCode | list[AggregationAssociationCode] | None = None,
        initiatives: AggregationInitiativeCode | list[AggregationInitiativeCode] | None = None,
    ) -> list[ItemSummaryCatalogue]:
        """
        Filter aggregations as item summaries, by namespace and/or association(s) and/or initiative(s).

        Wrapper around Record Aggregations.filter() returning results as ItemSummaryCatalogue instances.
        """
        results = self._aggregations.filter(namespace=namespace, associations=associations, initiatives=initiatives)
        return [self._summaries[aggregation.identifier.identifier] for aggregation in results]

    @property
    def collections(self) -> list[ItemSummaryCatalogue]:
        """Collection aggregations."""
        return self._filter(
            associations=AggregationAssociationCode.LARGER_WORK_CITATION,
            initiatives=AggregationInitiativeCode.COLLECTION,
        )

    @property
    def items(self) -> list[ItemSummaryCatalogue]:
        """Item aggregations."""
        return self._filter(
            associations=AggregationAssociationCode.IS_COMPOSED_OF,
            initiatives=AggregationInitiativeCode.COLLECTION,
        )


class Dates(RecordDates):
    """
    Dates.

    Wrapper around Record Dates to apply automatic formatting.
    """

    def __init__(self, dates: RecordDates) -> None:
        # noinspection PyTypeChecker
        super().__init__(**unpack(dates))

    def __getattribute__(self, name: str) -> str | None:
        """Get formatted date by name."""
        if name not in object.__getattribute__(self, "__dataclass_fields__"):
            return object.__getattribute__(self, name)

        val: Date = super().__getattribute__(name)
        if val is None:
            return None
        return format_date(val)

    def as_dict_enum(self) -> dict[DateTypeCode, str]:
        """Non-None values as a dictionary with DateTypeCode enum keys."""
        # noinspection PyTypeChecker
        return super().as_dict_enum()

    def as_dict_labeled(self) -> dict[str, str]:
        """Non-None values as a dictionary with human-readable labels as keys."""
        mapping = {
            DateTypeCode.CREATION: "Item created",
            DateTypeCode.PUBLICATION: "Item published",
            DateTypeCode.REVISION: "Item updated",
            DateTypeCode.ADOPTED: "Item adopted",
            DateTypeCode.DEPRECATED: "Item deprecated",
            DateTypeCode.DISTRIBUTION: "Item distributed",
            DateTypeCode.EXPIRY: "Item expiry",
            DateTypeCode.IN_FORCE: "Item in force from",
            DateTypeCode.LAST_REVISION: "Item last revised",
            DateTypeCode.LAST_UPDATE: "Item last updated",
            DateTypeCode.NEXT_UPDATE: "Item next update",
            DateTypeCode.RELEASED: "Item released",
            DateTypeCode.SUPERSEDED: "Item superseded",
            DateTypeCode.UNAVAILABLE: "Item unavailable from",
            DateTypeCode.VALIDITY_BEGINS: "Item valid from",
            DateTypeCode.VALIDITY_EXPIRES: "Item valid until",
        }
        return {mapping[key]: value for key, value in self.as_dict_enum().items()}


class Extent(ItemExtent):
    """
    ItemCatalogue Extent.

    Wrapper around Item Extent adding date formatting and extent map properties.
    """

    def __init__(self, extent: ItemExtent, embedded_maps_endpoint: str) -> None:
        super().__init__(extent)
        self._map_endpoint = embedded_maps_endpoint

    @property
    def start(self) -> str | None:
        """Temporal period start."""
        return format_date(super().start) if super().start else None

    @property
    def end(self) -> str | None:
        """Temporal period end."""
        return format_date(super().end) if super().end else None

    @property
    def map_iframe(self) -> str:
        """Visualise bounding box as an embedded map using the BAS Embedded Maps Service."""
        bbox = json.dumps(list(self.bounding_box)).replace(" ", "")
        params = f"bbox={bbox}&globe-overview"
        return f"<iframe src='{self._map_endpoint}/?{params}' width='100%' height='400' frameborder='0'></iframe>"


class PageHeader:
    """Page header information."""

    def __init__(self, title: str, item_type: HierarchyLevelCode) -> None:
        self._title = title
        self._item_type = item_type

    @property
    def title(self) -> str:
        """Title."""
        return self._title.replace("<p>", "").replace("</p>", "")

    @property
    def subtitle(self) -> tuple[str, str]:
        """Subtitle."""
        return self._item_type.value, ResourceTypeIcon[self._item_type.name].value


class Summary:
    """Item summary information."""

    def __init__(
        self,
        item_type: HierarchyLevelCode,
        edition: str | None,
        released_date: str | None,
        aggregations: Aggregations,
        citation: str | None,
        abstract: str,
    ) -> None:
        self._item_type = item_type
        self._edition = edition
        self._released_date = released_date
        self._aggregations = aggregations
        self._citation = citation
        self._abstract = abstract

    @property
    def edition(self) -> str | None:
        """Edition."""
        if self._item_type == HierarchyLevelCode.COLLECTION:
            return None
        return self._edition

    @property
    def released(self) -> str | None:
        """Formatted released date."""
        if self._item_type == HierarchyLevelCode.COLLECTION:
            return None
        return self._released_date

    @property
    def collections(self) -> list[Link]:
        """Collections item is part of."""
        return self._aggregations.as_links(self._aggregations.collections)

    @property
    def items_count(self) -> int:
        """Number of items that form item."""
        return len(self._aggregations.items)

    @property
    def citation(self) -> str | None:
        """Citation."""
        if self._item_type == HierarchyLevelCode.COLLECTION:
            return None
        return self._citation

    @property
    def abstract(self) -> str:
        """Abstract."""
        return self._abstract
