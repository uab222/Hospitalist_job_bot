"""One-off diagnostic: find the real Workday CXS endpoint (host/tenant/site)
for each hospital system's public career site, by following redirects from
their known careers URL and scanning the resulting HTML/JS for
*.myworkdayjobs.com references. Run only from an environment with real
internet access (e.g. GitHub Actions) -- this repo's dev sandbox is
network-restricted.

Not part of the bot itself -- delete this script and the accompanying
debug_workday.yml workflow once the real endpoints are confirmed and
config.yaml is updated.
"""

from __future__ import annotations

import re
import sys

import requests

UA = "HospitalistJobBot-Debug/0.1 (one-off endpoint discovery; personal job search tool)"

CANDIDATES = {
    "MemorialCare": [
        "https://www.memorialcare.org/careers",
        "https://memorialcare.org/careers",
        "https://careers.memorialcare.org",
    ],
    "Providence": [
        "https://www.providence.org/careers",
        "https://careers.providence.org",
        "https://jobs.providence.org",
    ],
    "UCI Health": [
        "https://www.ucihealth.org/careers",
        "https://jobs.uci.edu",
        "https://careers.uci.edu",
        "https://www.uci.edu/careers",
    ],
    "Hoag": [
        "https://www.hoag.org/careers",
        "https://careers.hoag.org",
    ],
    "Kaiser Permanente (Southern California)": [
        "https://www.kaiserpermanentejobs.org",
    ],
}

WORKDAY_HOST_RE = re.compile(r"[a-zA-Z0-9.-]+\.wd\d+\.myworkdayjobs\.com")
WORKDAY_URL_RE = re.compile(r"https?://[a-zA-Z0-9.-]+\.wd\d+\.myworkdayjobs\.com/[a-zA-Z0-9_/\-]*")


def probe_cxs(host: str, tenant: str, site: str) -> bool:
    url = f"https://{host}/wday/cxs/{tenant}/{site}/jobs"
    body = {"appliedFacets": {}, "limit": 1, "offset": 0, "searchText": ""}
    try:
        resp = requests.post(url, json=body, headers={"User-Agent": UA}, timeout=15)
        ok = resp.status_code == 200 and "jobPostings" in resp.text
        print(f"    CXS probe {url} -> {resp.status_code} {'OK, has jobPostings' if ok else ''}")
        return ok
    except requests.RequestException as exc:
        print(f"    CXS probe {url} -> ERROR {exc}")
        return False


def main() -> None:
    for name, urls in CANDIDATES.items():
        print(f"=== {name} ===")
        for url in urls:
            try:
                resp = requests.get(
                    url, headers={"User-Agent": UA}, timeout=20, allow_redirects=True
                )
                final_url = resp.url
                print(f"  {url} -> {resp.status_code} (final: {final_url})")

                found_hosts = set(WORKDAY_HOST_RE.findall(final_url))
                found_hosts |= set(WORKDAY_HOST_RE.findall(resp.text))
                found_full_urls = set(WORKDAY_URL_RE.findall(resp.text))

                if found_hosts:
                    print(f"    workday hosts referenced: {sorted(found_hosts)}")
                if found_full_urls:
                    print(f"    full workday URLs referenced: {sorted(found_full_urls)}")

                if "wd" in final_url and "myworkdayjobs.com" in final_url:
                    # landed directly on the Workday site -- parse host/tenant/site
                    m = re.match(
                        r"https?://([a-zA-Z0-9.-]+\.wd\d+\.myworkdayjobs\.com)/([a-zA-Z0-9_-]+)",
                        final_url,
                    )
                    if m:
                        host, site = m.group(1), m.group(2)
                        tenant = host.split(".")[0]
                        print(f"    => derived host={host} tenant={tenant} site={site}")
                        probe_cxs(host, tenant, site)
            except requests.RequestException as exc:
                print(f"  {url} -> ERROR {exc}")
        print()

    print("=== Re-checking currently configured tenants in config.yaml ===")
    configured = [
        ("MemorialCare", "memorialcare.wd1.myworkdayjobs.com", "memorialcare", "MemorialCare_Careers"),
        ("Providence", "providence.wd5.myworkdayjobs.com", "providence", "External"),
        ("UCI Health", "uci.wd1.myworkdayjobs.com", "uci", "External_Career"),
    ]
    for name, host, tenant, site in configured:
        print(f"  {name}:")
        probe_cxs(host, tenant, site)


if __name__ == "__main__":
    sys.exit(main())
