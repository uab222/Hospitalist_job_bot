"""Workday CXS API source.

Many hospital systems (including several in Orange County) host their
public career site on Workday. The career page itself calls a JSON API at

    POST https://{host}/wday/cxs/{tenant}/{site}/jobs

to render search results in the browser. This calls that same public
endpoint directly -- it's the identical data anyone browsing the career
site already receives, just fetched without a browser. No login, no
CAPTCHA bypass, no rate hammering (one request per configured tenant).

Workday tenant hostnames / site slugs occasionally change when an employer
reconfigures their career site. If a configured tenant starts returning
zero results, open the employer's careers page in a browser, check the
Network tab for a request to `/wday/cxs/...`, and update config.yaml with
the current host/tenant/site.
"""

from __future__ import annotations

import logging

import requests

from ..config import Config
from ..models import JobPosting
from .base import USER_AGENT, JobSource

logger = logging.getLogger(__name__)


class WorkdaySource(JobSource):
    name = "workday"

    def __init__(self, config: Config):
        self.config = config
        self.settings = config.sources.get("workday", {})

    def search(self) -> list[JobPosting]:
        if not self.settings.get("enabled", True):
            return []

        postings: list[JobPosting] = []
        for tenant_cfg in self.settings.get("tenants", []):
            postings.extend(self._search_tenant(tenant_cfg))
        return postings

    def _search_tenant(self, tenant_cfg: dict) -> list[JobPosting]:
        host = tenant_cfg.get("host")
        tenant = tenant_cfg.get("tenant")
        site = tenant_cfg.get("site")
        display_name = tenant_cfg.get("name", tenant or host)
        search_text = tenant_cfg.get("search_text", "hospitalist")

        if not (host and tenant and site):
            logger.warning("Skipping incomplete Workday tenant config: %s", tenant_cfg)
            return []

        url = f"https://{host}/wday/cxs/{tenant}/{site}/jobs"
        body = {
            "appliedFacets": {},
            "limit": 20,
            "offset": 0,
            "searchText": search_text,
        }

        try:
            response = requests.post(
                url,
                json=body,
                headers={"User-Agent": USER_AGENT, "Content-Type": "application/json"},
                timeout=30,
            )
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException as exc:
            logger.error("Workday search failed for tenant %s: %s", display_name, exc)
            return []
        except ValueError as exc:
            logger.error("Workday tenant %s returned non-JSON response: %s", display_name, exc)
            return []

        postings = []
        for item in payload.get("jobPostings", []):
            postings.append(self._to_posting(item, host, site, display_name))
        return postings

    @staticmethod
    def _to_posting(item: dict, host: str, site: str, employer_name: str) -> JobPosting:
        external_path = item.get("externalPath", "")
        job_url = f"https://{host}/{site}{external_path}" if external_path else f"https://{host}/{site}"

        return JobPosting(
            source=f"workday:{employer_name}",
            source_id=external_path or item.get("title", ""),
            title=item.get("title", ""),
            employer=employer_name,
            location=item.get("locationsText", ""),
            url=job_url,
            description=item.get("bulletFields", [""])[0] if item.get("bulletFields") else "",
            employment_type="unknown",
            posted_at=item.get("postedOn", ""),
            raw=item,
        )
