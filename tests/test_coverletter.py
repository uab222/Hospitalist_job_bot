from hospitalist_job_bot.coverletter import draft_cover_letter
from hospitalist_job_bot.models import JobPosting


def test_draft_includes_employer_and_resume_facts():
    posting = JobPosting(
        source="adzuna",
        source_id="1",
        title="Hospitalist Physician",
        employer="Hoag Hospital",
        location="Irvine, CA",
        url="https://example.com",
        description="7 on 7 off schedule, day shift.",
    )
    resume = {
        "name": "Usman Ali, MD",
        "email": "usman.ali@gmail.com",
        "years_experience": 14,
        "current_employer": "Providence (Torrance & San Pedro)",
        "relocation_reason": "for family reasons",
        "highlights": ["14 years of hospital medicine experience"],
    }

    letter = draft_cover_letter(posting, resume)

    assert "Hoag Hospital" in letter
    assert "Irvine, CA" in letter
    assert "14 years" in letter
    assert "Usman Ali, MD" in letter
    assert "usman.ali@gmail.com" in letter
    assert "7 on 7 off" in letter  # schedule note picked up from description


def test_draft_handles_missing_schedule_mention():
    posting = JobPosting(
        source="adzuna",
        source_id="2",
        title="Hospitalist Physician",
        employer="MemorialCare",
        location="Fountain Valley, CA",
        url="https://example.com",
        description="Join our team.",
    )
    resume = {"name": "Usman Ali, MD", "email": "usman.ali@gmail.com", "highlights": []}

    letter = draft_cover_letter(posting, resume)
    assert "MemorialCare" in letter
    assert letter  # renders without error even with sparse resume data
