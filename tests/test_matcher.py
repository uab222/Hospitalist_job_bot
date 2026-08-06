from hospitalist_job_bot.config import Config
from hospitalist_job_bot.matcher import filter_and_score, is_excluded_employer, score_posting
from hospitalist_job_bot.models import JobPosting


def make_config(**overrides) -> Config:
    defaults = dict(
        titles=["Hospitalist", "Hospital Medicine"],
        locations=["Irvine", "Mission Viejo", "Newport Beach", "Orange County"],
        employment_types=["full_time", "part_time", "per_diem"],
        schedule_preferences=["7 on 7 off", "day shift"],
        min_score=40,
        exclude_employers=["Providence Torrance", "Providence San Pedro"],
        sources={},
    )
    defaults.update(overrides)
    return Config(**defaults)


def make_posting(**overrides) -> JobPosting:
    defaults = dict(
        source="adzuna",
        source_id="123",
        title="Hospitalist Physician",
        employer="Hoag Hospital",
        location="Irvine, CA",
        url="https://example.com/job/123",
        description="Join our hospitalist team, 7 on 7 off schedule, day shift.",
        employment_type="full_time",
    )
    defaults.update(overrides)
    return JobPosting(**defaults)


def test_strong_match_scores_high():
    config = make_config()
    posting = make_posting()
    score, reasons = score_posting(posting, config)
    assert score == 100
    assert any("title matches" in r for r in reasons)
    assert any("location matches" in r for r in reasons)
    assert any("schedule mentions" in r for r in reasons)


def test_non_hospitalist_title_is_dropped_by_filter():
    config = make_config()
    posting = make_posting(title="ICU Nurse Practitioner")
    results = filter_and_score([posting], config)
    assert results == []


def test_wrong_location_scores_lower_but_may_still_pass():
    config = make_config()
    posting = make_posting(location="Sacramento, CA", description="Hospitalist role, day shift")
    score, _ = score_posting(posting, config)
    assert score < 100
    # title(40) + employment_type(10) + schedule(10) = 60, still >= min_score
    assert score >= config.min_score


def test_excluded_employer_is_filtered_out():
    config = make_config()
    posting = make_posting(employer="Providence Torrance Medical Center")
    assert is_excluded_employer(posting, config) is True
    results = filter_and_score([posting], config)
    assert results == []


def test_below_min_score_is_dropped():
    config = make_config(min_score=90)
    posting = make_posting(location="Sacramento, CA", employment_type="unknown", description="Hospitalist role")
    results = filter_and_score([posting], config)
    assert results == []


def test_results_sorted_by_score_descending():
    config = make_config()
    strong = make_posting(source_id="1", location="Irvine, CA")
    weak = make_posting(source_id="2", location="Fresno, CA", employment_type="unknown", description="Hospitalist role")
    results = filter_and_score([weak, strong], config)
    assert len(results) == 2
    assert results[0].score >= results[1].score
