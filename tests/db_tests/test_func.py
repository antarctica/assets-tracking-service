from uuid import UUID

import pytest
from psycopg.sql import SQL
from psycopg.types.json import Jsonb
from ulid import parse as ulid_parse

from assets_tracking_service.db import DatabaseClient, DatabaseError


class TestDbFuncUlid:
    """Test ULID functions."""

    def test_generate(self, fx_db_client_tmp_db_mig: DatabaseClient):
        """ULID can be generated as a UUID."""
        result = fx_db_client_tmp_db_mig.get_query_result(SQL("""SELECT generate_ulid() as id;"""))
        assert len(result) == 1
        assert isinstance(result[0][0], UUID)

        ulid_parse(result[0][0])

    def test_parse(self, fx_db_client_tmp_db_mig: DatabaseClient):
        """External ULID can be parsed."""
        result = fx_db_client_tmp_db_mig.get_query_result(
            SQL("""SELECT parse_ulid('01HYR9NC4WSVF2ZR0AHQCV1SE8') as id;""")
        )
        assert len(result) == 1

    def test_ulid_to_uuid(self, fx_db_client_tmp_db_mig: DatabaseClient):
        """ULID can be converted to a UUID."""
        result = fx_db_client_tmp_db_mig.get_query_result(
            SQL("""SELECT ulid_to_uuid('01HYR9NC4WSVF2ZR0AHQCV1SE8') as id;""")
        )
        assert result[0][0] == UUID("018fb09a-b09c-cede-2fe0-0a8dd9b0e5c8")

    def test_uuid_to_ulid(self, fx_db_client_tmp_db_mig: DatabaseClient):
        """UUID can be converted to a ULID."""
        result = fx_db_client_tmp_db_mig.get_query_result(
            SQL("""SELECT uuid_to_ulid('018fb09a-b09c-cede-2fe0-0a8dd9b0e5c8') as id;""")
        )
        assert result[0][0] == "01HYR9NC4WSVF2ZR0AHQCV1SE8"


class TestDbFuncDdm:
    """test DDM coordinate formatting function."""

    def test_format(self, fx_db_client_tmp_db_mig: DatabaseClient):
        """DDM can be formatted."""
        result = fx_db_client_tmp_db_mig.get_query_result(
            SQL("""SELECT geom_as_ddm('POINT (30.432 40.265)'::geometry(POINT, 4326)) as ddm;""")
        )
        assert result[0][0] == '("30° 25.92\' E","40° 15.9\' N")'


class TestDbFuncLabelsValidity:
    """Test label validation function."""

    def test_valid(self, fx_db_client_tmp_db_mig: DatabaseClient):
        """Valid labels can be inserted."""
        fx_db_client_tmp_db_mig.insert_dict(
            "public",
            "asset",
            {
                "labels": Jsonb(
                    {
                        "version": "1",
                        "values": [
                            {
                                "rel": "self",
                                "scheme": "skos:prefLabel",
                                "value": "foo",
                                "creation": 1339338620,
                                "expiration": None,
                            }
                        ],
                    }
                )
            },
        )

    def test_invalid_wrapper_not_obj(self, fx_db_client_tmp_db_mig: DatabaseClient):
        """Labels that are not in a wrapper object are not allowed."""
        with pytest.raises(DatabaseError):
            fx_db_client_tmp_db_mig.insert_dict(
                "public",
                "asset",
                {"labels": Jsonb(["invalid"])},
            )

    def test_invalid_wrapper_no_version(self, fx_db_client_tmp_db_mig: DatabaseClient):
        """Labels not wrapped in an object with a 'version' property are not allowed."""
        with pytest.raises(DatabaseError):
            fx_db_client_tmp_db_mig.insert_dict(
                "public",
                "asset",
                {
                    "labels": Jsonb(
                        {
                            "values": [
                                {
                                    "rel": "self",
                                    "scheme": "skos:prefLabel",
                                    "value": "foo",
                                    "creation": 1339338620,
                                    "expiration": None,
                                }
                            ],
                        }
                    )
                },
            )

    def test_invalid_wrapper_invalid_version(self, fx_db_client_tmp_db_mig: DatabaseClient):
        """Labels with a wrapper version that is not '1' are not allowed."""
        with pytest.raises(DatabaseError):
            fx_db_client_tmp_db_mig.insert_dict(
                "public",
                "asset",
                {
                    "labels": Jsonb(
                        {
                            "version": "invalid",
                            "values": [
                                {
                                    "rel": "self",
                                    "scheme": "skos:prefLabel",
                                    "value": "foo",
                                    "creation": 1339338620,
                                    "expiration": None,
                                }
                            ],
                        }
                    )
                },
            )

    def test_invalid_wrapper_no_values(self, fx_db_client_tmp_db_mig: DatabaseClient):
        """Labels not wrapped in an object with a 'values' property are not allowed."""
        with pytest.raises(DatabaseError):
            fx_db_client_tmp_db_mig.insert_dict(
                "public",
                "asset",
                {"labels": Jsonb({"version": "1"})},
            )

    def test_invalid_values_not_list(self, fx_db_client_tmp_db_mig: DatabaseClient):
        """Labels that are not in a list are not allowed."""
        with pytest.raises(DatabaseError):
            fx_db_client_tmp_db_mig.insert_dict(
                "public",
                "asset",
                {
                    "labels": Jsonb(
                        {
                            "version": "1",
                            "values": {
                                "rel": "foo",
                                "value": "bar",
                                "scheme": "baz",
                                "creation": 1339338620,
                                "expiration": None,
                            },
                        }
                    )
                },
            )

    def test_invalid_items_not_objects(self, fx_db_client_tmp_db_mig: DatabaseClient):
        """Labels that are not objects are not allowed."""
        with pytest.raises(DatabaseError):
            fx_db_client_tmp_db_mig.insert_dict(
                "public", "asset", {"labels": Jsonb({"version": "1", "values": ["invalid"]})}
            )

    def test_invalid_missing_required_scheme(self, fx_db_client_tmp_db_mig: DatabaseClient):
        """Labels with a missing required field (scheme as example) are not allowed."""
        with pytest.raises(DatabaseError):
            fx_db_client_tmp_db_mig.insert_dict(
                "public",
                "asset",
                {
                    "labels": Jsonb(
                        {
                            "version": "1",
                            "values": [{"rel": "foo", "value": "bar", "creation": 1339338620, "expiration": None}],
                        }
                    )
                },
            )

    def test_invalid_missing_pref_labels(self, fx_db_client_tmp_db_mig: DatabaseClient):
        """Missing prefLabel is not allowed."""
        with pytest.raises(DatabaseError):
            fx_db_client_tmp_db_mig.insert_dict(
                "public",
                "asset",
                {
                    "labels": Jsonb(
                        {
                            "version": "1",
                            "values": [
                                {
                                    "rel": "foo",
                                    "value": "bar",
                                    "scheme": "baz",
                                    "creation": 1339338620,
                                    "expiration": None,
                                }
                            ],
                        }
                    )
                },
            )

    def test_invalid_multiple_pref_labels(self, fx_db_client_tmp_db_mig: DatabaseClient):
        """Multiple prefLabels are not allowed."""
        with pytest.raises(DatabaseError):
            fx_db_client_tmp_db_mig.insert_dict(
                "public",
                "asset",
                {
                    "labels": Jsonb(
                        {
                            "version": "1",
                            "values": [
                                {
                                    "rel": "self",
                                    "scheme": "skos:prefLabel",
                                    "value": "foo",
                                    "creation": 1339338620,
                                    "expiration": None,
                                },
                                {
                                    "rel": "self",
                                    "scheme": "skos:prefLabel",
                                    "value": "bar",
                                    "creation": 1339338620,
                                    "expiration": None,
                                },
                            ],
                        }
                    )
                },
            )
