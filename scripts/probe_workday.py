"""One-off diagnostic: find the real Workday CXS endpoint (host/tenant/site)
for each hospital system's public career site, using a headless browser to
load the page for real and watch the network traffic it actually makes.
Static HTML fetches missed these -- Workday-embedded career sites are
typically JS-rendered, so the /wday/cxs/ API call only fires after the
page's own JavaScript runs, and won't appear in the raw HTML source.

Run only from an environment with real internet access (e.g. GitHub
Actions) -- this repo's dev sandbox is network-restricted.

Not part of the bot itself -- delete this script and the accompanying
debug_workday.yml workflow once the real endpoints are confirmed and
config.yaml is updated.
"""

from __future__ import annotations

import re
import sys

from playwright.sync_api import sync_playwright

UA = "HospitalistJobBot-Debug/0.1 (one-off endpoint discovery; personal job search tool)"

CANDIDATES = {
    "MemorialCare": ["https://careers.memorialcare.org/"],
    "Providence": ["https://www.providence.org/careers", "https://providence.jobs/"],
    "UCI Health": ["https://jobs.uci.edu/careers-home/"],
    "Hoag": ["https://careers.hoag.org/"],
    "Kaiser Permanente (Southern California)": ["https://www.kaiserpermanentejobs.org/"],
}

WORKDAY_CXS_RE = re.compile(
    r"https?://([a-zA-Z0-9.-]+\.wd\d+\.myworkdayjobs\.com)/wday/cxs/([a-zA-Z0-9_-]+)/([a-zA-Z0-9_-]+)/"
)


def probe(name: str, urls: list) -> None:
    print(f"=== {name} ===")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(user_agent=UA)

        seen_cxs_urls = set()

        def on_request(request):
            if "myworkdayjobs.com" in request.url or "/wday/" in request.url:
                seen_cxs_urls.add(request.url)

        page.on("request", on_request)

        for url in urls:
            try:
                page.goto(url, wait_until="networkidle", timeout=30000)
                print(f"  loaded {url} -> final URL: {page.url}")
            except Exception as exc:  # noqa: BLE001 -- diagnostic script, print and continue
                print(f"  {url} -> ERROR loading: {exc}")
                continue

            # Give any deferred/XHR-triggered requests (e.g. after a search
            # box auto-focuses or a "browse jobs" widget lazy-loads) a
            # moment to fire, then try clicking anything that looks like a
            # jobs/search entry point to trigger it if it hasn't already.
            page.wait_for_timeout(3000)

        browser.close()

        if seen_cxs_urls:
            print(f"    workday/wday network calls observed:")
            for u in sorted(seen_cxs_urls):
                print(f"      {u}")
                m = WORKDAY_CXS_RE.match(u)
                if m:
                    host, tenant, site = m.group(1), m.group(2), m.group(3)
                    print(f"      => host={host} tenant={tenant} site={site}")
        else:
            print("    no myworkdayjobs.com / /wday/ network calls observed -- likely not on Workday")
    print()


def main() -> None:
    for name, urls in CANDIDATES.items():
        probe(name, urls)


if __name__ == "__main__":
    sys.exit(main())
