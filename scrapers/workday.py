"""
Workday scraper.

Many large companies use Workday's hosted careers product
(NVIDIA, Qualcomm, ARM, etc.). The product exposes a JSON API
on /wday/cxs/{tenant}/{site}/jobs that accepts a POST.

Key requirement: the Referer header must point to the careers landing
page including the /en-US/ locale path. Workday rejects requests
with a generic Referer.
"""

import requests
from config import REQUEST_TIMEOUT, USER_AGENT


def _headers(host, site):
    """Build headers that match what a real browser sends to Workday."""
    return {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "User-Agent": USER_AGENT,
        "Origin": f"https://{host}",
        # CRITICAL: Workday checks the Referer matches the careers landing page
        "Referer": f"https://{host}/en-US/{site}",
    }


def fetch_workday(company_name, platform_id):
    """
    Fetch jobs from a Workday-hosted careers site.

    platform_id keys:
      - tenant: company tenant on Workday (e.g. "nvidia")
      - site:   careers site name (e.g. "NVIDIAExternalCareerSite")
      - host:   full host (e.g. "nvidia.wd5.myworkdayjobs.com")

    Strategy: fetch all jobs, then filter on our side. Workday's
    location facet IDs are tenant-specific and would require manual
    discovery per company, so we let our config.LOCATION_KEYWORDS
    do the Israel filter.
    """
    tenant = platform_id["tenant"]
    site = platform_id["site"]
    host = platform_id["host"]

    api_url = f"https://{host}/wday/cxs/{tenant}/{site}/jobs"

    all_jobs = []
    offset = 0
    page_size = 20  # Workday's typical page size

    # Fetch up to 5 pages = 100 jobs per company per run.
    # That's plenty: we only care about NEW postings each run.
    for page in range(5):
        payload = {
            "appliedFacets": {},
            "limit": page_size,
            "offset": offset,
            "searchText": "",
        }

        try:
            r = requests.post(
                api_url,
                json=payload,
                headers=_headers(host, site),
                timeout=REQUEST_TIMEOUT,
            )
        except Exception as e:
            print(f"[{company_name}] workday request failed: {e}")
            break

        if r.status_code != 200:
            print(f"[{company_name}] workday returned {r.status_code}: {r.text[:150]}")
            break

        try:
            data = r.json()
        except Exception:
            print(f"[{company_name}] workday non-JSON response")
            break

        postings = data.get("jobPostings", [])
        if not postings:
            break

        for posting in postings:
            title = posting.get("title", "")
            location = posting.get("locationsText", "")
            external_path = posting.get("externalPath", "")
            full_url = f"https://{host}{external_path}" if external_path else ""

            all_jobs.append({
                "title": title,
                "location": location,
                "company": company_name,
                "url": full_url,
                "description": "",
            })

        # Stop if we received fewer than page_size — that was the last page
        if len(postings) < page_size:
            break

        offset += page_size

    print(f"[{company_name}] workday fetched {len(all_jobs)} jobs total")
    return all_jobs      - host:   full host (e.g. "nvidia.wd5.myworkdayjobs.com")

    Strategy: fetch all jobs, then filter on our side. Workday's
    location facet IDs are tenant-specific and would require manual
    discovery per company, so we let our config.LOCATION_KEYWORDS
    do the Israel filter.
    """
    tenant = platform_id["tenant"]
    site = platform_id["site"]
    host = platform_id["host"]

    api_url = f"https://{host}/wday/cxs/{tenant}/{site}/jobs"

    all_jobs = []
    offset = 0
    page_size = 20  # Workday's typical page size

    # Fetch up to 5 pages = 100 jobs per company per run.
    # That's plenty: we only care about NEW postings each run.
    for page in range(5):
        payload = {
            "appliedFacets": {},
            "limit": page_size,
            "offset": offset,
            "searchText": "",
        }

        try:
            r = requests.post(
                api_url,
                json=payload,
                headers=_headers(host, site),
                timeout=REQUEST_TIMEOUT,
            )
        except Exception as e:
            print(f"[{company_name}] workday request failed: {e}")
            break

        if r.status_code != 200:
            print(f"[{company_name}] workday returned {r.status_code}: {r.text[:150]}")
            break

        try:
            data = r.json()
        except Exception:
            print(f"[{company_name}] workday non-JSON response")
            break

        postings = data.get("jobPostings", [])
        if not postings:
            break

        for posting in postings:
            title = posting.get("title", "")
            location = posting.get("locationsText", "")
            external_path = posting.get("externalPath", "")
            full_url = f"https://{host}{external_path}" if external_path else ""

            all_jobs.append({
                "title": title,
                "location": location,
                "company": company_name,
                "url": full_url,
                "description": "",
            })

        # Stop if we received fewer than page_size — that was the last page
        if len(postings) < page_size:
            break

        offset += page_size

    print(f"[{company_name}] workday fetched {len(all_jobs)} jobs total")
    return all_jobs

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
