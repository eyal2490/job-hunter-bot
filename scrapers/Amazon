"""
Amazon careers scraper.

Amazon runs amazon.jobs as their public careers site. The same URL that
serves the human-facing search page also returns JSON if you hit
.json instead of leaving it as HTML:
    GET https://amazon.jobs/en/search.json

Query parameters mirror the search-page URL:
    country=ISR      ISO-3 country code; ISR = Israel
    result_limit=N   page size (max 100 in practice)
    offset=N         pagination offset (0-indexed)
    sort=recent      newest first; alternative is "relevant"

Response shape:
    { "hits": <int>, "jobs": [ {...}, ... ] }

Each job dict gives us title, posted_date, location, job_path (relative URL
back to the listing), and a description preview.

We sort newest first and paginate to the end of results because we
want the broadest coverage; main.py applies the student/intern + chip
filter after.
"""
import requests
from config import REQUEST_TIMEOUT, USER_AGENT


BASE_URL = "https://amazon.jobs/en/search.json"


def _headers():
    return {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "User-Agent": USER_AGENT,
        "Referer": "https://amazon.jobs/en/search?country=ISR&loc_query=Israel",
    }


def fetch_amazon(company_name="Amazon"):
    print(f"[{company_name}] calling {BASE_URL}?country=ISR")

    all_jobs = []
    offset = 0
    page_size = 100  # Amazon's search.json caps at 100 per page
    max_pages = 15
    total_hits = None

    for page in range(max_pages):
        params = {
            "country": "ISR",
            "loc_query": "Israel",
            "result_limit": page_size,
            "offset": offset,
            "sort": "recent",
        }

        try:
            r = requests.get(BASE_URL, params=params, headers=_headers(), timeout=REQUEST_TIMEOUT)
        except Exception as e:
            print(f"[{company_name}] amazon request failed: {e}")
            break

        if r.status_code != 200:
            print(f"[{company_name}] amazon returned {r.status_code}: {r.text[:300]}")
            break

        try:
            data = r.json()
        except Exception:
            print(f"[{company_name}] amazon non-JSON response. First 200 chars: {r.text[:200]}")
            break

        if page == 0:
            total_hits = data.get("hits", 0)
            print(f"[{company_name}] response total field: {total_hits}")

        jobs = data.get("jobs") or []
        if not jobs:
            break

        for j in jobs:
            title = (j.get("title") or "").strip()
            location = (j.get("location") or "").strip()
            posted_on = j.get("posted_date") or j.get("updated_time") or ""

            job_path = j.get("job_path") or ""
            if job_path:
                full_url = f"https://amazon.jobs{job_path}"
            else:
                full_url = "https://amazon.jobs/en/jobs"

            all_jobs.append({
                "title": title,
                "location": location,
                "company": company_name,
                "url": full_url,
                "description": (j.get("description_short") or j.get("description") or "")[:1500],
                "posted_on": str(posted_on),
            })

        # Stop if we've fetched everything Amazon says exists
        if total_hits is not None and offset + len(jobs) >= total_hits:
            break
        if len(jobs) < page_size:
            break
        offset += page_size

    print(f"[{company_name}] amazon fetched {len(all_jobs)} jobs total (newest first)")
    return all_jobs


if __name__ == "__main__":
    jobs = fetch_amazon()
    for j in jobs[:20]:
        print(f"  [{j['posted_on']:20s}] {j['title'][:55]:55s} | {j['location'][:30]:30s}")
    print(f"\nTotal: {len(jobs)}")
