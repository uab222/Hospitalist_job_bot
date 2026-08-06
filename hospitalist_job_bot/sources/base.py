"""Interface every job source implements."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import JobPosting

# Identify ourselves honestly to whatever API/endpoint we call -- this is a
# personal job-search tool, not a scraper trying to look like a browser.
USER_AGENT = "HospitalistJobBot/0.1 (personal job search assistant; contact via source account)"

# Be polite: this is a low-volume personal tool, not a crawler. A short
# delay between requests to the same host is plenty and keeps us well
# within any reasonable rate limit.
REQUEST_DELAY_SECONDS = 1.0


class JobSource(ABC):
    """A place to look for job postings."""

    name: str = "base"

    @abstractmethod
    def search(self) -> list[JobPosting]:
        """Return matching postings. Should not raise on empty/no results --
        return an empty list instead. Network/API errors should be caught
        and logged by the implementation so one bad source doesn't kill a run."""
        raise NotImplementedError
