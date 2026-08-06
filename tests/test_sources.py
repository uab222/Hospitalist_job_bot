from hospitalist_job_bot.sources.adzuna import AdzunaSource
from hospitalist_job_bot.sources.workday import WorkdaySource


def test_adzuna_to_posting_maps_fields():
    item = {
        "id": "987",
        "title": "Hospitalist Physician",
        "company": {"display_name": "Hoag Hospital"},
        "location": {"display_name": "Irvine, CA"},
        "redirect_url": "https://example.com/job/987",
        "description": "Join our hospitalist team.",
        "contract_time": "full_time",
        "created": "2026-08-01T00:00:00Z",
    }
    posting = AdzunaSource._to_posting(item)
    assert posting.source == "adzuna"
    assert posting.source_id == "987"
    assert posting.title == "Hospitalist Physician"
    assert posting.employer == "Hoag Hospital"
    assert posting.location == "Irvine, CA"
    assert posting.employment_type == "full_time"
    assert posting.url == "https://example.com/job/987"


def test_adzuna_to_posting_handles_missing_optional_fields():
    item = {"id": "1", "title": "Hospitalist"}
    posting = AdzunaSource._to_posting(item)
    assert posting.employer == "Unknown employer"
    assert posting.employment_type == "unknown"
    assert posting.location == ""


def test_workday_to_posting_builds_url_from_external_path():
    item = {
        "title": "Hospitalist Physician",
        "externalPath": "/job/Fountain-Valley-CA/Hospitalist_R1234",
        "locationsText": "Fountain Valley, CA",
        "bulletFields": ["Full-time, 7 on/7 off"],
        "postedOn": "Posted 3 Days Ago",
    }
    posting = WorkdaySource._to_posting(
        item, host="memorialcare.wd1.myworkdayjobs.com", site="MemorialCare_Careers",
        employer_name="MemorialCare",
    )
    assert posting.source == "workday:MemorialCare"
    assert posting.source_id == "/job/Fountain-Valley-CA/Hospitalist_R1234"
    assert posting.url == (
        "https://memorialcare.wd1.myworkdayjobs.com/MemorialCare_Careers"
        "/job/Fountain-Valley-CA/Hospitalist_R1234"
    )
    assert posting.location == "Fountain Valley, CA"
    assert posting.description == "Full-time, 7 on/7 off"
