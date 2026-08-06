"""Scores a JobPosting against config.yaml preferences.

Scoring is intentionally simple and inspectable (no ML/LLM in the loop) so
you can see exactly why a job matched, in match_reasons.
"""

from __future__ import annotations

from .config import Config
from .models import JobPosting

TITLE_POINTS = 40
LOCATION_POINTS = 40
EMPLOYMENT_TYPE_POINTS = 10
SCHEDULE_PREF_POINTS = 10  # per matched schedule keyword, capped below
SCHEDULE_PREF_MAX_POINTS = 10


def _contains_any(haystack: str, needles: list) -> str | None:
    """Returns the first needle found in haystack (case-insensitive), else None."""
    haystack_lower = haystack.lower()
    for needle in needles:
        if needle.lower() in haystack_lower:
            return needle
    return None


def is_excluded_employer(posting: JobPosting, config: Config) -> bool:
    employer_lower = posting.employer.lower()
    return any(excluded.lower() in employer_lower for excluded in config.exclude_employers)


def score_posting(posting: JobPosting, config: Config) -> tuple[int, list]:
    """Returns (score 0-100, list of human-readable reasons)."""
    score = 0
    reasons: list = []

    title_hit = _contains_any(posting.title, config.titles)
    if title_hit:
        score += TITLE_POINTS
        reasons.append(f"title matches '{title_hit}'")

    location_text = f"{posting.location} {posting.description}"
    location_hit = _contains_any(location_text, config.locations)
    if location_hit:
        score += LOCATION_POINTS
        reasons.append(f"location matches '{location_hit}'")

    employment_hit = None
    normalized_type = posting.employment_type.replace(" ", "_").lower()
    if normalized_type in [e.lower() for e in config.employment_types]:
        employment_hit = normalized_type
        score += EMPLOYMENT_TYPE_POINTS
        reasons.append(f"employment type '{employment_hit}' matches preference")
    elif normalized_type == "unknown":
        # Don't penalize postings where the source didn't provide a type --
        # give partial credit so they aren't unfairly excluded.
        score += EMPLOYMENT_TYPE_POINTS // 2
        reasons.append("employment type unspecified by source (partial credit)")

    schedule_text = f"{posting.title} {posting.description}"
    schedule_hit = _contains_any(schedule_text, config.schedule_preferences)
    if schedule_hit:
        score += min(SCHEDULE_PREF_POINTS, SCHEDULE_PREF_MAX_POINTS)
        reasons.append(f"schedule mentions '{schedule_hit}'")

    return min(score, 100), reasons


def filter_and_score(postings: list, config: Config) -> list:
    """Scores all postings, drops excluded employers and postings that don't
    meet a hard bar (must at least match on title), sorts by score desc."""
    results = []
    for posting in postings:
        if is_excluded_employer(posting, config):
            continue

        score, reasons = score_posting(posting, config)

        # Hard requirement: must actually look like a hospitalist role.
        # Everything else (location, schedule, employment type) is scored,
        # not required, since source data is often incomplete.
        if not _contains_any(posting.title, config.titles):
            continue

        if score < config.min_score:
            continue

        posting.score = score
        posting.match_reasons = reasons
        results.append(posting)

    results.sort(key=lambda p: p.score, reverse=True)
    return results
