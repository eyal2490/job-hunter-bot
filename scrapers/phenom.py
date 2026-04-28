"""
Phenom Careers (a.k.a. Phenom People) scraper.

Many companies host their careers site on Phenom's "career site" platform.
The customer-facing URL is the company's own domain (e.g.
careers.mobileye.com), but under the hood there's a JSON API at:
    POST https://{host}/widgets

The endpoint takes a JSON body with ddoKey="refineSearch" and returns
paginated job listings. No authentication required for the public
career-site read path.

Note: Phenom sites typically sit behind CloudFront, which rejects
requests that don't look like a real browser. We set the full set of
headers Chrome sends when paginating search results, including the
Sec-Fetch-* family. A plain Python requests-default User-Agent or a
minimal header set will get a 403 from CloudFront.

Currently used by:
    Mobileye  (host=careers.mobileye.com, country=Israel)
"""
import requests
from config import REQUEST_TIMEOUT, USER_AGENT


def _headers(host):
    """Mimic Chrome's headers when paginating search results on a Phenom site."""
    return {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Content-Type": "application/json",
        "Origin": f"https://{host}",
        "Referer": f"https://{host}/jobs",
        "Sec-Ch-Ua": '"Chromium";v="121", "Not A(Brand";v="99"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": USER_AGENT,
    }


def _build_payload(country, offset, limit):
    """
    The widgets payload Phenom expects when a user paginates through
    search results.
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
    if country and country.lower() != "global":
        payload["selected_fields"] = {"country": [country]}
    return payload


def fetch_phenom(company_name, platform_id):
    host = platform_id["host"]
    country = platform_id.get("country")
    api_url = f"https://{host}/widgets"
    print(f"[{company_name}] calling {api_url}")

    all_jobs = []
    offset = 0
    page_size = 50
    max_pages = 25
    total_count = None

    # Use a Session so cookies set by the first request (e.g. CloudFront's
    # session token) are sent on subsequent ones. Some Phenom deployments
    # set a cookie that gates further requests.
    session = requests.Session()

    # Warm-up GET to the public jobs page. This lets CloudFront/Phenom
    # set whatever cookies it expects to see on the /widgets POST.
    try:
        warmup = session.get(
            f"https://{host}/jobs",
            headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "User-Agent": USER_AGENT,
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
            },
            timeout=REQUEST_TIMEOUT,
        )
        if warmup.status_code != 200:
            print(f"[{company_name}] phenom warmup returned {warmup.status_code}")
    except Exception as e:
        print(f"[{company_name}] phenom warmup failed: {e}")

    for page in range(max_pages):
        payload = _build_payload(country, offset, page_size)
        try:
            r = session.post(
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

            city = (job.get("city") or "").strip()
            state = (job.get("state") or "").strip()
            cntry = (job.get("country") or "").strip()
            location_parts = [p for p in (city, state, cntry) if p]
            location = ", ".join(location_parts) or "Israel"

            posted_on = job.get("postedDate") or job.get("createdDate") or ""

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
