"""Data model for a job posting as it moves through the pipeline."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field


# Lifecycle of a posting once it's in the store.
STATUS_NEW = "new"
STATUS_REVIEWED = "reviewed"
STATUS_APPROVED = "approved"
STATUS_APPLIED = "applied"
STATUS_REJECTED = "rejected"
STATUS_MANUAL_NEEDED = "manual_needed"  # approved, but no email to auto-submit to

ALL_STATUSES = (
    STATUS_NEW,
    STATUS_REVIEWED,
    STATUS_APPROVED,
    STATUS_APPLIED,
    STATUS_REJECTED,
    STATUS_MANUAL_NEEDED,
)


@dataclass
class JobPosting:
    source: str              # e.g. "adzuna", "workday:MemorialCare"
    source_id: str            # id assigned by the source, for dedupe within a source
    title: str
    employer: str
    location: str
    url: str
    description: str = ""
    employment_type: str = ""   # full_time / part_time / per_diem / unknown
    apply_email: str = ""        # if the posting lists a direct application email
    posted_at: str = ""            # ISO date string if available
    raw: dict = field(default_factory=dict)  # original payload, for debugging

    # populated by the matcher, not the source
    score: int = 0
    match_reasons: list = field(default_factory=list)

    @property
    def job_id(self) -> str:
        """Stable id used as the primary key in the store, independent of source id format."""
        digest = hashlib.sha256(f"{self.source}:{self.source_id}".encode("utf-8")).hexdigest()
        return digest[:16]
