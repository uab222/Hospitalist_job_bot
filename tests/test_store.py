import tempfile
from pathlib import Path

import pytest

from hospitalist_job_bot.models import STATUS_APPROVED, STATUS_NEW, JobPosting
from hospitalist_job_bot.store import JobStore


@pytest.fixture
def store():
    with tempfile.TemporaryDirectory() as tmp:
        yield JobStore(db_path=Path(tmp) / "jobs.db")


def make_posting(**overrides) -> JobPosting:
    defaults = dict(
        source="adzuna",
        source_id="123",
        title="Hospitalist Physician",
        employer="Hoag Hospital",
        location="Irvine, CA",
        url="https://example.com/job/123",
        score=85,
        match_reasons=["title matches 'Hospitalist'"],
    )
    defaults.update(overrides)
    return JobPosting(**defaults)


def test_upsert_new_posting_returns_true(store):
    posting = make_posting()
    assert store.upsert(posting) is True
    row = store.get(posting.job_id)
    assert row["status"] == STATUS_NEW
    assert row["title"] == "Hospitalist Physician"


def test_upsert_duplicate_returns_false_and_does_not_reset_status(store):
    posting = make_posting()
    store.upsert(posting)
    store.set_status(posting.job_id, STATUS_APPROVED)

    posting.score = 95
    assert store.upsert(posting) is False

    row = store.get(posting.job_id)
    assert row["status"] == STATUS_APPROVED  # untouched by the re-upsert
    assert row["score"] == 95  # score still refreshed


def test_different_source_id_is_a_different_job(store):
    a = make_posting(source_id="1")
    b = make_posting(source_id="2")
    store.upsert(a)
    store.upsert(b)
    assert a.job_id != b.job_id
    assert len(store.list_by_status()) == 2


def test_list_by_status_filters(store):
    posting = make_posting()
    store.upsert(posting)
    store.set_status(posting.job_id, STATUS_APPROVED)

    assert len(store.list_by_status(STATUS_APPROVED)) == 1
    assert len(store.list_by_status(STATUS_NEW)) == 0
