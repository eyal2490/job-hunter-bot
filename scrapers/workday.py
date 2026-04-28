"""
Workday scraper.

Many large companies use Workday hosted careers product.
Exposes a JSON API on /wday/cxs/{tenant}/{site}/jobs that accepts a POST.

Critical: results are sorted by Workday's relevance score by default,
which is not useful for our "find newest jobs" goal. We pass an empty
searchText (so all jobs are eligible) and rely on the fact that Workday
returns NEWEST jobs first when there's no search query. Then we fetch
several pages to catch all recent postings.
"""

import requests
from config import REQUEST_TIMEOUT, USER_AGENT


def _headers(host, site):
    return {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "User-Agent": USER_AGENT,
        "Origin": f"https://{host}",
        "Referer": f"https://{host}/en-US/{site}",
    }


def fetch_workday(company_name, platform_id):
    tenant = platform_id["tenant"]
    site = platform_id["site"]
    host = platform_id["host"]

    api_url = f"https://{host}/wday/cxs/{tenant}/{site}/jobs"
    print(f"[{company_name}] calling {api_url}")

    all_jobs = []
    offset = 0
    page_size = 20
    # Fetch up to 500 jobs - newest first. We need wide coverage because
    # we filter by location (Israel) on our side, and a global company
    # may have many non-Israel jobs interleaved in the most-recent list.
    max_pages = 25

    for page in range(max_pages):
        # Empty searchText + empty appliedFacets returns all jobs in
        # newest-first order.
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
            print(f"[{company_name}] workday returned {r.status_code}: {r.text[:300]}")
            break

        try:
            data = r.json()
        except Exception:
            print(f"[{company_name}] workday non-JSON response. First 200 chars: {r.text[:200]}")
            break

        if page == 0:
            total = data.get("total", "unknown")
            print(f"[{company_name}] response total field: {total}")

        postings = data.get("jobPostings", [])
        if not postings:
            break

        for posting in postings:
            title = posting.get("title", "")
            location = posting.get("locationsText", "")
            external_path = posting.get("externalPath", "")
            posted_on = posting.get("postedOn", "")  # e.g. "Posted Today" or "Posted 5 Days Ago"
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
                "posted_on": posted_on,
            })

        if len(postings) < page_size:
            break

        offset += page_size

    print(f"[{company_name}] workday fetched {len(all_jobs)} jobs total (newest first)")
    return all_jobs
