"""Adzuna job search API.

Adzuna (https://developer.adzuna.com/) is a licensed job-listing aggregator
with a public, documented API and a free tier. Its results include postings
pulled from Indeed, LinkedIn, and direct employer sites -- so this covers
the "general boards" case without us having to scrape sites whose own
Terms of Service prohibit automated access.

Requires ADZUNA_APP_ID / ADZUNA_APP_KEY (see README setup step 3).
"""

from __future__ import annotations

import logging
import time

import requests

from ..config import Config
from ..models import JobPosting
from .base import USER_AGENT, JobSource

logger = logging.getLogger(__name__)

API_URL_TEMPLATE = "https://api.adzuna.com/v1/api/jobs/{country}/search/1"


class AdzunaSource(JobSource):
    name = "adzuna"

    def __init__(self, config: Config):
        self.config = config
        self.settings = config.sources.get("adzuna", {})

    def search(self) -> list[JobPosting]:
        if not self.settings.get("enabled", True):
            return []

        app_id = self.config.secrets.adzuna_app_id
        app_key = self.config.secrets.adzuna_app_key
        if not app_id or not app_key:
            logger.warning(
                "Adzuna source skipped: set ADZUNA_APP_ID / ADZUNA_APP_KEY to enable it."
            )
            return []

        params = {
            "app_id": app_id,
            "app_key": app_key,
            "what": self.settings.get("what", "hospitalist"),
            "where": self.settings.get("where", "Orange County, CA"),
            "results_per_page": self.settings.get("results_per_page", 50),
            "content-type": "application/json",
        }
        url = API_URL_TEMPLATE.format(country=self.settings.get("country", "us"))

        try:
            response = requests.get(
                url, params=params, headers={"User-Agent": USER_AGENT}, timeout=30
            )
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException as exc:
            logger.error("Adzuna search failed: %s", exc)
            return []

        postings = []
        for item in payload.get("results", []):
            postings.append(self._to_posting(item))
        return postings

    @staticmethod
    def _to_posting(item: dict) -> JobPosting:
        contract_time = (item.get("contract_time") or "").lower()  # full_time / part_time
        employment_type = contract_time or "unknown"

        company = (item.get("company") or {}).get("display_name", "Unknown employer")
        location = (item.get("location") or {}).get("display_name", "")

        return JobPosting(
            source="adzuna",
            source_id=str(item.get("id", "")),
            title=item.get("title", ""),
            employer=company,
            location=location,
            url=item.get("redirect_url", ""),
            description=item.get("description", ""),
            employment_type=employment_type,
            posted_at=item.get("created", ""),
            raw=item,
        )
