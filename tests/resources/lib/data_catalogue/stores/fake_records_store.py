import logging

from assets_tracking_service.lib.bas_data_catalogue.models.record import Record
from assets_tracking_service.lib.bas_data_catalogue.models.record.summary import RecordSummary
from assets_tracking_service.lib.bas_data_catalogue.stores.base_store import Store
from tests.resources.lib.data_catalogue.records.item_cat_collection_all import record as collection_all_supported
from tests.resources.lib.data_catalogue.records.item_cat_collection_min import record as collection_min_supported
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
from tests.resources.lib.data_catalogue.records.item_cat_product_restricted import record as product_restricted
from tests.resources.lib.data_catalogue.records.item_cat_pub_map import combined as product_published_map_combined
from tests.resources.lib.data_catalogue.records.item_cat_pub_map import side_a as product_published_map_side_a
from tests.resources.lib.data_catalogue.records.item_cat_pub_map import side_b as product_published_map_side_b


class FakeRecordsStore(Store):
    """
    Simple in-memory store of fake/test records.

    Termed 'fake' rather than 'test' to avoid confusion between testing a store, vs. a store used for testing.
    """

    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger

        self._summaries: list[RecordSummary] = []
        self._records: list[Record] = []

    def __len__(self) -> int:
        """Record count."""
        return len(self._records)

    @property
    def _fake_records(self) -> list[Record]:
        return [
            collection_min_supported,
            collection_all_supported,
            product_min_supported,
            product_restricted,
            product_all_supported,
            formatting_supported,
            data_all_supported,
            ogl_record,
            cc_record,
            ops_record,
            rights_reversed_record,
            product_published_map_combined,
            product_published_map_side_a,
            product_published_map_side_b,
        ]

    @staticmethod
    def _get_related_identifiers(record: Record) -> set[str]:
        """For building a single item with its direct relations."""
        return {
            related.identifier.identifier
            for related in record.identification.aggregations
            if related.identifier.identifier != record.file_identifier
        }

    @property
    def summaries(self) -> list[RecordSummary]:
        """All record summaries."""
        return self._summaries

    @property
    def records(self) -> list[Record]:
        """All records."""
        return self._records

    def purge(self) -> None:
        """Empty records from store."""
        self._summaries = []
        self._records = []

    def loads(self, file_identifier: str | None, inc_related: bool = False) -> None:
        """
        Load test records, optionally limited to a file identifier and its direct dependencies.

        If `file_identifier` is not None, only a matching record will be loaded.
        If `inc_related` is True, the record's direct dependencies will also be loaded.
        """
        self._summaries = [RecordSummary.loads(record) for record in self._fake_records]

        if not file_identifier:
            self._logger.info("Loading all test records")
            self._records = self._fake_records
            return

        records_indexed = {record.file_identifier: record for record in self._fake_records}
        if file_identifier not in records_indexed:
            self._logger.warning(f"No test record found with identifier '{file_identifier}', skipping.")
            return

        record = records_indexed[file_identifier]
        self._records.append(record)
        if not inc_related:
            self._logger.info(f"Loading single test record '{file_identifier}'")
            return

        self._logger.info(f"Loading single test record '{file_identifier}' with direct dependencies")
        related_records = [records_indexed[related_id] for related_id in self._get_related_identifiers(record)]
        self._records.extend(related_records)
