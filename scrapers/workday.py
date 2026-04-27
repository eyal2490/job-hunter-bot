"""
Workday scraper.

Many large companies (NVIDIA, Apple, Qualcomm, ARM) use Workday's hosted
careers product. The product exposes a JSON API on /wday/cxs/{tenant}/{site}/jobs
that accepts a POST with a search query.

We send a search restricted to Israel and yield job dicts.
"""

import requests
from config import REQUEST_TIMEOUT, USER_AGENT


def _headers(host):
    return {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": USER_AGENT,
        "Origin": f"https://{host}",
        "Referer": f"https://{host}/",
    }


def fetch_workday(company_name, platform_id):
    """
    Fetch Israel-based jobs from a Workday-hosted careers site.

    platform_id keys:
      - tenant: company tenant on Workday (e.g. "nvidia")
      - site:   careers site name (e.g. "NVIDIAExternalCareerSite")
      - host:   full host (e.g. "nvidia.wd5.myworkdayjobs.com")
    """
    tenant = platform_id["tenant"]
    site = platform_id["site"]
    host = platform_id["host"]

    api_url = f"https://{host}/wday/cxs/{tenant}/{site}/jobs"

    # Strategy: search by free text "Israel" — Workday's full-text search
    # picks up the country in location fields. Then we re-filter on our side.
    payload = {
        "appliedFacets": {},
        "limit": 50,
        "offset": 0,
        "searchText": "Israel",
    }

    try:
        r = requests.post(api_url, json=payload, headers=_headers(host), timeout=REQUEST_TIMEOUT)
    except Exception as e:
        print(f"[{company_name}] workday request failed: {e}")
        return []

    if r.status_code != 200:
        print(f"[{company_name}] workday returned {r.status_code}: {r.text[:150]}")
        return []

    try:
        data = r.json()
    except Exception:
        print(f"[{company_name}] workday non-JSON response")
        return []

    out = []
    for posting in data.get("jobPostings", []):
        title = posting.get("title", "")
        location = posting.get("locationsText", "")
        external_path = posting.get("externalPath", "")
        full_url = f"https://{host}{external_path}" if external_path else ""

        out.append({
            "title": title,
            "location": location,
            "company": company_name,
            "url": full_url,
            "description": "",  # Workday list view doesn't include description; we filter on title+location
        })

    return out
