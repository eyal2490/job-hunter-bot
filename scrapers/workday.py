"""
Workday scraper.

Many large companies use Workday hosted careers product
(NVIDIA, Qualcomm, ARM, etc.). The product exposes a JSON API
on /wday/cxs/{tenant}/{site}/jobs that accepts a POST.

Key requirements:
  - The Referer header must point to the careers landing page
    including /en-US/ locale path
  - The user-facing URL is /en-US/{site}{externalPath}, not just {externalPath}
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
        "Referer": f"https://{host}/en-US/{site}",
    }


def fetch_workday(company_name, platform_id):
    """Fetch jobs from a Workday hosted careers site."""
    tenant = platform_id["tenant"]
    site = platform_id["site"]
    host = platform_id["host"]

    api_url = f"https://{host}/wday/cxs/{tenant}/{site}/jobs"

    all_jobs = []
    offset = 0
    page_size = 20

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
            # Correct URL format: https://{host}/en-US/{site}{externalPath}
            # externalPath is something like "/job/Yokneam/Software-Engineer_JR12345"
            if external_path:
                full_url = f"https://{host}/en-US/{site}{external_path}"
            else:
                full_url = f"https://{host}/en-US/{site}"

            all_jobs.append({
                "title": title,
                "location": location,
                "company": company_name,
                "url": full_url,
                "description": "",
            })

        if len(postings) < page_size:
            break

        offset += page_size

    print(f"[{company_name}] workday fetched {len(all_jobs)} jobs total")
    return all_jobs
