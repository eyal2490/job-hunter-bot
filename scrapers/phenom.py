"""
Phenom Careers (a.k.a. Phenom People) scraper.

Many companies host their careers site on Phenom's "career site" platform.
The customer-facing URL is the company's own domain (e.g.
careers.mobileye.com), but under the hood there's a JSON API at:
    POST https://{host}/widgets

The endpoint takes a JSON body with ddoKey="refineSearch" and returns
paginated job listings. No authentication required for the public
career-site read path.

What this module does:
- Pulls jobs from a Phenom-hosted careers site, paginated 50 at a time.
- Optionally narrows by country at fetch time (more efficient than
  pulling everything and filtering).
- Normalizes results into the bot's standard dict shape.

Currently used by:
    Mobileye  (host=careers.mobileye.com, country=Israel)
"""
import requests
from config import REQUEST_TIMEOUT, USER_AGENT


def _headers(host):
    return {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "User-Agent": USER_AGENT,
        "Origin": f"https://{host}",
        "Referer": f"https://{host}/jobs",
    }


def _build_payload(country, offset, limit):
    """
    The widgets payload Phenom expects. Based on what the Phenom-hosted
    career sites send when a user paginates through search results.
    """
    payload = {
        "lang": "en_global",
        "deviceType": "desktop",
        "country": country or "global",
        "pageName": "search-results",
        "size": limit,
        "from": offset,
        "jobs": True,
        "counts": True,
        "all_fields": ["category", "country", "city", "type"],
        "clearAll": False,
        "jdsource": "facets",
        "isSliderEnable": False,
        "pageId": "page0",
        "siteType": "external",
        "keywords": "",
        "global": True,
        "selected_fields": {},
        "sort": {"order": "desc", "field": "postedDate"},
        "locationData": {},
        "ddoKey": "refineSearch",
    }
    # Some Phenom deployments require an explicit country filter in
    # selected_fields rather than the top-level country key.
    if country and country.lower() != "global":
        payload["selected_fields"] = {"country": [country]}
    return payload


def fetch_phenom(company_name, platform_id):
    host = platform_id["host"]
    country = platform_id.get("country")  # optional fetch-time filter
    api_url = f"https://{host}/widgets"
    print(f"[{company_name}] calling {api_url}")

    all_jobs = []
    offset = 0
    page_size = 50
    max_pages = 25  # 1250-job safety cap
    total_count = None

    for page in range(max_pages):
        payload = _build_payload(country, offset, page_size)
        try:
            r = requests.post(
                api_url,
                json=payload,
                headers=_headers(host),
                timeout=REQUEST_TIMEOUT,
            )
        except Exception as e:
            print(f"[{company_name}] phenom request failed: {e}")
            break

        if r.status_code != 200:
            print(f"[{company_name}] phenom returned {r.status_code}: {r.text[:300]}")
            break

        try:
            data = r.json()
        except Exception:
            print(f"[{company_name}] phenom non-JSON response. First 200 chars: {r.text[:200]}")
            break

        # Phenom wraps results as { "refineSearch": { "totalHits": N, "data": { "jobs": [...] } } }.
        # Different deployments place the jobs list slightly differently,
        # so we look in a few likely paths.
        refine = data.get("refineSearch") or {}
        if page == 0:
            total_count = refine.get("totalHits") or 0
            print(f"[{company_name}] response total field: {total_count}")

        postings = (
            refine.get("data", {}).get("jobs")
            or refine.get("jobs")
            or data.get("jobs")
            or []
        )
        if not postings:
            break

        for job in postings:
            job_id = job.get("jobId") or job.get("jobSeqNo") or job.get("id") or ""
            title = (job.get("title") or "").strip()

            # Build a location string similar to other scrapers: city, country.
            city = (job.get("city") or "").strip()
            state = (job.get("state") or "").strip()
            cntry = (job.get("country") or "").strip()
            location_parts = [p for p in (city, state, cntry) if p]
            location = ", ".join(location_parts) or "Israel"

            posted_on = job.get("postedDate") or job.get("createdDate") or ""

            # Phenom canonical URL: /jobs/{jobSeqNo}
            seq = job.get("jobSeqNo") or job_id
            full_url = f"https://{host}/jobs/{seq}" if seq else f"https://{host}/jobs"

            all_jobs.append({
                "title": title,
                "location": location,
                "company": company_name,
                "url": full_url,
                "description": (job.get("description") or "")[:1500],
                "posted_on": str(posted_on),
            })

        if total_count and offset + len(postings) >= total_count:
            break
        if len(postings) < page_size:
            break
        offset += page_size

    print(f"[{company_name}] phenom fetched {len(all_jobs)} jobs total (newest first)")
    return all_jobs
