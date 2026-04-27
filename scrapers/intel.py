"""
Intel scraper.

Intel's careers site uses a JSON endpoint at jobs.intel.com.
We query Israel-based listings. The structure is similar to the public-facing UI.
"""

import requests
from config import REQUEST_TIMEOUT, USER_AGENT


def fetch_intel(company_name="Intel"):
    """
    Intel exposes a search API. The exact endpoint can change, so we use
    the public search URL with parameters and parse JSON.

    If Intel changes its API and this breaks, the bot's run summary
    will report 0 jobs for Intel — easy to spot, easy to fix.
    """
    url = "https://jobs.intel.com/api/jobs"
    params = {
        "country": "Israel",
        "location": "Israel",
        "stretchUnit": "MILES",
        "stretch": 10,
        "page": 1,
        "limit": 50,
    }
    headers = {
        "Accept": "application/json",
        "User-Agent": USER_AGENT,
    }

    try:
        r = requests.get(url, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
    except Exception as e:
        print(f"[{company_name}] request failed: {e}")
        return []

    if r.status_code != 200:
        print(f"[{company_name}] returned {r.status_code}")
        return []

    try:
        data = r.json()
    except Exception:
        print(f"[{company_name}] non-JSON response")
        return []

    # The Intel API returns jobs in a "jobs" array; each item has nested data.
    jobs = data.get("jobs", []) or data.get("results", [])
    out = []
    for j in jobs:
        item = j.get("data", j) if isinstance(j, dict) else {}
        title = item.get("title", "")
        location = item.get("full_location", "") or item.get("city", "") or item.get("country", "")
        slug = item.get("slug", "")
        job_id = item.get("req_id", "") or item.get("id", "")
        if slug:
            full_url = f"https://jobs.intel.com/en/job/{slug}/"
        elif job_id:
            full_url = f"https://jobs.intel.com/en/job/{job_id}/"
        else:
            full_url = "https://jobs.intel.com/"

        out.append({
            "title": title,
            "location": location,
            "company": company_name,
            "url": full_url,
            "description": item.get("description", "")[:1500],
        })

    return out
