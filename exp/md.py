from exp.cat import EXPORTS_PATH, _get_identifier_title, _get_identifier_titles, _load_record
from jinja2 import Environment, FileSystemLoader, select_autoescape

from assets_tracking_service.config import Config
from assets_tracking_service.lib.bas_data_catalogue.models.item.base import ItemBase
from assets_tracking_service.lib.bas_data_catalogue.models.item.base.elements import Link
from assets_tracking_service.lib.bas_data_catalogue.models.item.base.enums import AccessType
from assets_tracking_service.lib.bas_data_catalogue.models.item.catalogue.elements import format_date
from assets_tracking_service.lib.bas_data_catalogue.models.record import Record
from assets_tracking_service.lib.bas_data_catalogue.models.record.enums import (
    ContactRoleCode,
    DateTypeCode,
    HierarchyLevelCode,
    MaintenanceFrequencyCode,
    ProgressCode,
)


def _md_link(link: Link) -> str:
    """Markdown encoding of a link."""
    return f"[{link.value}]({link.href})"


class Badge:
    """Badge."""

    def __init__(self, key: str, value: str, colour: str) -> None:
        self._endpoint = "https://img.shields.io/badge"
        self._key = key
        self._value = value
        self._colour = colour

    def render(self) -> str:
        """
        Encode badge as Markdown link.

        E.g. `Badge(key="Edition", value="Foo", colour="2B8CC4").render()` gives:
        ![Edition badge](https://img.shields.io/badge/Edition-Foo-2B8CC4)
        """
        key = self._key.replace("-", "--")
        value = self._value.replace("-", "--").replace(" ", "_")
        parts = [key, value, self._colour]
        link = Link(value=f"{self._key} badge", href=f"{self._endpoint}/{'-'.join(parts)}")
        return f"!{_md_link(link)}"


class ItemMarkdown(ItemBase):
    """..."""

    def __init__(self, record: Record, embedded_maps_endpoint: str) -> None:
        super().__init__(record)
        self._embedded_maps_endpoint = embedded_maps_endpoint

        _loader = FileSystemLoader("/Users/felix/Projects/assets-tracking-service/exp/templates")
        self._jinja = Environment(loader=_loader, autoescape=select_autoescape(), trim_blocks=True, lstrip_blocks=True)

    @staticmethod
    def _prettify_md(md: str) -> str:
        """Remove repeating blank lines from input, keeping single blank lines."""
        lines = md.split("\n")
        result = []
        prev_empty = False

        for line in lines:
            is_empty = not line.strip()
            if not (is_empty and prev_empty):
                result.append(line)
            prev_empty = is_empty

        return "\n".join(result)

    def render(self) -> str:
        """Render Markdown representation of item."""
        return self._prettify_md(self._jinja.get_template("item.md.j2").render(item=self))

    @property
    def _type_emoji(self) -> str:
        """Emoji for hierarchy level."""
        mapping = {
            HierarchyLevelCode.COLLECTION: "🧑‍🧑‍🧒‍🧒",
            HierarchyLevelCode.DATASET: "💾",
            HierarchyLevelCode.PRODUCT: "🗺️",
        }
        try:
            return mapping[self.resource_type]
        except KeyError:
            return "🫥"

    @property
    def _type_label(self) -> str:
        """Label for hierarchy level."""
        overrides = {
            HierarchyLevelCode.PRODUCT: "Product (Map)",
        }

        emoji = self._type_emoji
        label = self.resource_type.value.capitalize()
        if self.resource_type in overrides:
            label = overrides[self._record.hierarchy_level]

        return f"{emoji} {label}"

    @property
    def _edition_badge(self) -> Badge | None:
        return Badge(key="Edition", value=self.edition, colour="2B8CC4") if self.edition else None

    @property
    def _projection_badge(self) -> Badge | None:
        """Projection badge."""
        projection = (
            self._record.reference_system_info.code.value.split("::")[-1]
            if self._record.reference_system_info
            else None
        )
        return Badge(key="Projection", value=projection, colour="F499BE") if projection else None

    @property
    def _licence_badge(self) -> Badge | None:
        """Licence badge."""
        mapping = {"https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/": "OGL-3.0", None: None}
        code = mapping[self.licence.href if self.licence else None]
        return Badge(key="Licence", value=code, colour="FFBF47") if code else None

    @property
    def _access_badge(self) -> Badge | None:
        """Access badge."""
        mapping = {
            AccessType.PUBLIC: "Unrestricted",
            AccessType.BAS_ALL: "Staff Only",
            AccessType.NONE: "Restricted",
            None: None,
        }
        label = mapping[self.access if self.access else None]
        return Badge(key="Access", value=label, colour="379245") if label else None

    @property
    def _standard_badge(self) -> Badge | None:
        """Metadata standard badge."""
        value = (
            self._record.metadata.metadata_standard.version.replace("(E)", "")
            if self._record.metadata.metadata_standard
            else None
        )
        return Badge(key="Standard", value=value, colour="999999") if value else None

    @property
    def _profile_badge(self) -> Badge | None:
        """
        Profile badge.

        Limited to a first profile.
        """
        mapping = {"https://metadata-standards.data.bas.ac.uk/profiles/magic-discovery-v1/": "MAGIC Discovery v1"}
        profiles = self._record.data_quality.domain_consistency if self._record.data_quality is not None else []
        urls = [profile.specification.href for profile in profiles] if profiles else []
        labels = [mapping[url] for url in urls if url in mapping]
        label = labels[0] if labels else None

        return Badge(key="Profile", value=label, colour="6F72AF") if label else None

    @property
    def _language_badge(self) -> Badge:
        """Language badge."""
        mapping = {"eng": "English UK"}
        label = mapping[self._record.identification.language]
        return Badge(key="Language", value=label, colour="AAB437") if label else None

    @property
    def _character_set_badge(self) -> Badge:
        """Character badge badge."""
        mapping = {"utf8": "UTF-8"}
        label = mapping[self._record.identification.character_set]
        return Badge(key="Character-set", value=label, colour="B58840") if label else None

    def _get_item_identifier(self, namespace: str) -> str | None:
        try:
            return self.identifiers.filter(namespace=namespace)[0].href
        except IndexError:
            return None

    @property
    def _item_identifiers(self) -> str | None:
        """Item identifiers."""
        item_link = self._get_item_identifier(namespace="data.bas.ac.uk")
        alias_link = self._get_item_identifier(namespace="alias.data.bas.ac.uk")
        gitlab_link = self._get_item_identifier(namespace="gitlab.data.bas.ac.uk")

        text = f"**Item link:** [{item_link}]({item_link})<br />"
        if alias_link is not None:
            text += f"**Item alias:** [{alias_link}]({alias_link})<br />"
        if gitlab_link is not None:
            text += f"**Item GitLab:** [{gitlab_link}]({gitlab_link})<br />"
        return text

    @property
    def badges(self) -> str:
        """Badges."""
        badges = [self._edition_badge, self._projection_badge, self._licence_badge, self._access_badge]
        return " ".join([badge.render() for badge in badges if badge is not None])

    @property
    def badges_metadata(self) -> str:
        """Badges."""
        badges = [self._standard_badge, self._profile_badge, self._language_badge, self._character_set_badge]
        return " ".join([badge.render() for badge in badges if badge is not None])

    @property
    def title(self) -> str:
        """Title."""
        return f"# {self._type_emoji} {self.title_md}"

    @property
    def summary(self) -> str | None:
        """Summary."""
        return (
            f"""
## 💬 Summary
<blockquote>{self.summary_html}</blockquote>
        """
            if self.summary_html
            else None
        )

    @property
    def abstract(self) -> str:
        """Abstract."""
        return f"""
## 📖 Abstract
<blockquote>{self.abstract_html}</blockquote>
        """

    @property
    def citation(self) -> str | None:
        """Abstract."""
        return (
            f"""
## ✍️ Citation
<blockquote>{self.citation_html}</blockquote>
        """
            if self.citation_html
            else None
        )

    @property
    def lineage(self) -> str | None:
        """Abstract."""
        return (
            f"""
## 🧾 Lineage
<blockquote>{self.lineage_html}</blockquote>
        """
            if self.lineage_html
            else None
        )

    @property
    def dates(self) -> str:
        """Dates."""
        dates = []
        dates_ = self._record.identification.dates
        mapping = {
            DateTypeCode.CREATION: "🐣 Created",
            DateTypeCode.PUBLICATION: "📣 Published",
            DateTypeCode.RELEASED: "🔓 Released",
            DateTypeCode.REVISION: "🔄 Updated",
        }

        for date in mapping:
            if dates_[date.value] is not None:
                dates.append(f"{mapping[date]}: {format_date(dates_[date.value])}")

        dates_md = "\n\n* ".join(dates)
        output = f"## 📅 Dates\n\n* {dates_md}"

        if (
            self._record.identification.maintenance.progress == ProgressCode.ON_GOING
            and self._record.identification.maintenance.maintenance_frequency == MaintenanceFrequencyCode.CONTINUAL
        ):
            output += "\n\n> [!NOTE]\n>This record is updated multiple times per day."

        return output

    @property
    def data(self) -> str | None:
        """Data."""
        header = "| Format | Size | Link |\n| --- | --- | --- |\n"
        rows = [
            f"| {distribution.format_label} | {distribution.size} | {_md_link(distribution.action)} |"
            for distribution in self.distributions.ordered
        ]
        if len(rows) == 0:
            return None

        table = header + "\n".join(rows)
        text = f"## 📦 Data\n\n{table}"

        if (
            self.licence is not None
            and self.licence.href == "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
        ):
            text += "\n\n> [!IMPORTANT]\n> You must cite this item if you use it in your work."

        return text

    @property
    def authors(self) -> str | None:
        """Authors."""
        authors = []
        for author_ in self.contacts.filter(roles=ContactRoleCode.AUTHOR):
            name = ""
            if author_.organisation is not None:
                name = author_.organisation.name
            if author_.individual is not None and name != "":
                name = f"{author_.individual.name} ({name})"
            elif author_.individual is not None and name == "":
                name = author_.individual.name

            link = name
            if author_.online_resource is not None:
                link = _md_link(Link(value=name, href=author_.online_resource.href))

            author = link
            if (
                author_.organisation is not None
                and author_.organisation.href
                and author_.organisation.title == "ror"
                and author_.individual is None
            ):
                author = f"{author} (🦁 {author_.organisation.href})"
            elif author_.individual is not None and author_.individual.href and author_.individual.title == "orcid":
                author = f"{author} (🌸 {author_.individual.href})"
            authors.append(author)
        authors_md = "\n\n* ".join(authors)
        if len(authors) == 0:
            return None

        poc = ""
        poc_ = self.contacts.filter(ContactRoleCode.POINT_OF_CONTACT)
        if len(poc_) > 0:
            poc_link = _md_link(Link(value=poc_[0].organisation.name, href=f"mailto:{poc_[0].email}"))
            poc = f"\n\n> [!TIP]\n>If you have a question about this item, contact the {poc_link}, who manage it."

        return f"## 🧑‍🎨 Authors\n\n* {authors_md}\n\n{poc}"

    @property
    def extent_spatial(self) -> str | None:
        """Extent spatial."""
        extent = self.bounding_extent
        if extent is None:
            return None

        bbox = extent.geographic.bounding_box
        url = f"{self._embedded_maps_endpoint}/?bbox=[{bbox.west_longitude},{bbox.east_longitude},{bbox.north_latitude},{bbox.south_latitude}]"
        return f"""
## 🌍 Spatial coverage
<details>
<summary>Click to show bounding coordinates</summary>

**Min X:** {bbox.west_longitude}<br />
**Min Y:** {bbox.south_latitude}<br />
**Max X:** {bbox.east_longitude}<br />
**Max Y:** {bbox.north_latitude}
</details>

> [!TIP]
> {_md_link(Link(value="🗺️ Show on a map", href=url))}
        """

    @property
    def extent_temporal(self) -> str | None:
        """Extent temporal."""
        extent = self.bounding_extent
        if extent is None:
            return None

        text = "## ⌛️ Temporal coverage\n\n"
        if extent.start is None and extent.end is None:
            return f"{text}> [!NOTE]\n>Unknown."

        if extent.start is not None:
            text += f"**Start:** {format_date(extent.start)}"
        if extent.end is not None:
            if extent.start is not None:
                text += "<br/>"
            text += f"**End:** {format_date(extent.end)}"
        return text

    @property
    def collections(self) -> str | None:
        """Collections."""
        collections = []
        for collection_ in super().collections:
            title = _get_identifier_title(collection_.identifier.identifier)
            collections.append(_md_link(Link(value=title, href=collection_.identifier.href)))
        collections_md = "\n\n* ".join(collections)

        return f"## 🧩 Collections\n\n* {collections_md}" if len(collections) > 0 else None

    @property
    def metadata(self) -> str:
        """Metadata."""
        return f"""
## 📒️Metadata
{self.badges_metadata}<br />
**Item ID:** `{self.resource_id}`<br />
**Item type:** {self._type_label}<br />
{self._item_identifiers}
                """


def _save_markdown(filename: str, item: ItemMarkdown) -> None:
    """Load record from file."""
    output_path = EXPORTS_PATH / "markdown" / f"{filename.replace('.json', '')}.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w") as f:
        f.write(item.render())
    print(f"Saved to {output_path.resolve()}")


def main() -> None:
    """Entrypoint."""
    config = Config()
    _get_identifier_titles()
    filename = "ats_latest_assets_position.json"

    record = _load_record(filename)
    item = ItemMarkdown(record, embedded_maps_endpoint=config.EXPORTER_DATA_CATALOGUE_EMBEDDED_MAPS_ENDPOINT)
    _save_markdown(filename, item)


if __name__ == "__main__":
    main()
