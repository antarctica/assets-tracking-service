from datetime import UTC, datetime
from re import escape
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest
from pytest_mock import MockerFixture

from assets_tracking_service.models.record import Record, RecordNew, RecordsClient


class TestRecordNew:
    """Test data class in initial state."""

    @staticmethod
    def _get_resource_contents_abstract_ok(file: str) -> str:
        if file == "abstract.md":
            return "x"
        raise FileNotFoundError(file)

    def test_init(self, mocker: MockerFixture):
        """Creates a minimal RecordNew."""
        value = "x"
        mocker.patch(
            "assets_tracking_service.models.record.RecordNew._get_resource_contents",
            side_effect=self._get_resource_contents_abstract_ok,
        )
        dt = datetime.now(tz=UTC)

        record = RecordNew(
            slug=value,
            edition=value,
            title=value,
            summary=value,
            publication=dt,
            released=dt,
            update_frequency=value,
        )

        assert isinstance(record, RecordNew)
        assert record.slug == value
        assert record.edition == value
        assert record.title == value
        assert record.summary == value
        assert record.abstract == value
        assert record.publication == dt
        assert record.released == dt
        assert record.update_frequency == "x"
        assert record.gitlab_issue is None
        assert record.lineage is None

    def test_init_lineage(self, mocker: MockerFixture):
        """Creates a RecordNew with lineage file."""
        value = "x"
        mocker.patch("assets_tracking_service.models.record.RecordNew._get_resource_contents", return_value=value)
        dt = datetime.now(tz=UTC)

        record = RecordNew(
            slug=value,
            edition=value,
            title=value,
            summary=value,
            publication=dt,
            released=dt,
            update_frequency=value,
        )

        assert record.lineage == value

    def test_init_gitlab(self, fx_record_new: RecordNew):
        """Creates a RecordNew with GitLab issue link."""
        fx_record_new.gitlab_issue = "x"
        assert fx_record_new.gitlab_issue == "x"

    @pytest.mark.parametrize("slug", ["", "UPPER", "mixedCase", "with spaces", "with-hyphens", "with.dots"])
    def test_slug_invalid(self, slug: str):
        """Invalid slug triggers error."""
        dt = datetime.now(tz=UTC)

        with pytest.raises(
            ValueError, match=escape(f"Invalid slug: [{slug}]. It must be lowercase a-z, 0-9, and underscores only.")
        ):
            RecordNew(slug=slug, edition="x", title="x", summary="x", publication=dt, released=dt, update_frequency="x")

    @pytest.mark.parametrize("value", ["publication", "released"])
    def test_invalid_timezone(self, value: str):
        """Invalid timezone triggers error."""
        dt = datetime.now(tz=UTC)
        dt_invalid = datetime.now(tz=ZoneInfo("America/Lima"))
        # noinspection PyDictCreation
        values = {
            "slug": "x",
            "edition": "x",
            "title": "x",
            "summary": "x",
            "publication": dt,
            "released": dt,
            "update_frequency": "x",
        }
        values[value] = dt_invalid

        with pytest.raises(ValueError, match=escape(f"Invalid {value} timezone: [America/Lima]. It must be UTC.")):
            RecordNew(**values)

    def test_invalid_gitlab(self):
        """Invalid GitLab issue link triggers error."""
        dt = datetime.now(tz=UTC)
        with pytest.raises(
            ValueError, match=escape("Invalid gitlab_issue: [invalid]. It must be a valid BAS GitLab issue URL.")
        ):
            RecordNew(
                slug="x",
                edition="x",
                title="x",
                summary="x",
                publication=dt,
                released=dt,
                update_frequency="x",
                gitlab_issue="invalid",
            )

    def test_missing_abstract(self):
        """Missing abstract file triggers error."""
        dt = datetime.now(tz=UTC)
        with pytest.raises(FileNotFoundError):
            RecordNew(
                slug="x",
                edition="x",
                title="x",
                summary="x",
                publication=dt,
                released=dt,
                update_frequency="x",
            )

    def test_db_dict(self, fx_record_new: RecordNew):
        """Converts Record to a database dict."""
        data = fx_record_new.to_db_dict()
        assert data == {
            "slug": fx_record_new.slug,
            "edition": fx_record_new.edition,
            "title": fx_record_new.title,
            "summary": fx_record_new.summary,
            "publication": fx_record_new.publication,
            "released": fx_record_new.released,
            "update_frequency": fx_record_new.update_frequency,
            "gitlab_issue": fx_record_new.gitlab_issue,
        }

    def test_get_resource_contents(self, fx_record_new: RecordNew):
        """Can get contents of a resource file."""
        assert fx_record_new._get_resource_contents("abstract.md") != ""


class TestRecord:
    """Test data class in existing state."""

    def test_init(self, mocker: MockerFixture):
        """Creates a Record."""
        id_ = uuid4()
        value = "x"
        mocker.patch("assets_tracking_service.models.record.RecordNew._get_resource_contents", return_value=value)
        dt = datetime.now(tz=UTC)

        record = Record(
            id=id_,
            slug=value,
            edition=value,
            title=value,
            summary=value,
            publication=dt,
            released=dt,
            update_frequency=value,
            gitlab_issue=f"https://gitlab.data.bas.ac.uk/{value}",
        )

        assert isinstance(record, Record)
        assert record.id == id_

    def test_repr(self, fx_record: Record):
        """Representation."""
        assert repr(fx_record) == f"Record(id='{fx_record.id}', slug='{fx_record.slug}')"

    def test_from_db_dict(self, fx_record: Record):
        """Makes Record from a database dict."""
        data = {
            "id": fx_record.id,
            "slug": fx_record.slug,
            "edition": fx_record.edition,
            "title": fx_record.title,
            "summary": fx_record.summary,
            "publication": fx_record.publication,
            "released": fx_record.released,
            "update_frequency": fx_record.update_frequency,
            "gitlab_issue": fx_record.gitlab_issue,
        }

        record = Record.from_db_dict(data)

        assert record == fx_record


class TestRecordsClient:
    """Integration tests for a data/resource client."""

    def test_list_ids(self, fx_records_client_one: RecordsClient, fx_record: Record):
        """Can list record file identifiers."""
        records = fx_records_client_one.list_ids()
        assert len(records) == 2  # 1 collection , 1 layer

    def test_get_by_slug(self, fx_records_client_one: RecordsClient, fx_record: Record):
        """Can get Record by slug that exists."""
        record = fx_records_client_one.get_by_slug(fx_record.slug)
        assert isinstance(record, Record)

    def test_get_by_slug_unknown(self, fx_records_client_one: RecordsClient):
        """Cannot get Record for slug that does not exist."""
        result = fx_records_client_one.get_by_slug("unknown")
        assert result is None
