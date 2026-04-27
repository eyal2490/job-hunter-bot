"""
Workday scraper.

Many large companies use Workday hosted careers product.
The product exposes a JSON API on /wday/cxs/{tenant}/{site}/jobs
that accepts a POST.

Key requirements:
  - The Referer header must point to the careers landing page
    including /en-US/ locale path
  - The user-facing URL is /en-US/{site}{externalPath}, not just {externalPath}
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
            print(f"[{company_name}] workday returned {r.status_code}: {r.text[:300]}")
            break

        try:
            data = r.json()
        except Exception:
            print(f"[{company_name}] workday non-JSON response. First 200 chars: {r.text[:200]}")
            break

        # Diagnostic: show the response shape on first page
        if page == 0:
            total = data.get("total", "unknown")
            print(f"[{company_name}] response total field: {total}")

        postings = data.get("jobPostings", [])
        if not postings:
            if page == 0:
                # Diagnostic: print top-level keys to debug empty response
                print(f"[{company_name}] empty jobPostings. Response keys: {list(data.keys())[:10]}")
            break

        for posting in postings:
            title = posting.get("title", "")
            location = posting.get("locationsText", "")
            external_path = posting.get("externalPath", "")
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
