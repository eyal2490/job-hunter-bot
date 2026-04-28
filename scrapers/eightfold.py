"""
Eightfold AI careers scraper.

Some companies host their careers on Eightfold AI's "talent intelligence
platform". Customer-facing URL is the company's own domain (e.g.
careers.qualcomm.com), but the unauthenticated public read endpoint
lives at:
    GET https://{tenant}.eightfold.ai/api/apply/v2/jobs

Query parameters we use:
    domain   - the company's domain (e.g. "qualcomm.com")
    location - free-text location filter (e.g. "Israel")
    start    - 0-indexed pagination offset
    num      - page size (Eightfold caps at ~100)

The response shape is { "positions": [...], "count": N }.

Currently used by:
    Qualcomm  (tenant=qualcomm, domain=qualcomm.com, location=Israel)
"""
import requests
from config import REQUEST_TIMEOUT, USER_AGENT


def _headers(tenant):
    return {
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "User-Agent": USER_AGENT,
        "Referer": f"https://{tenant}.eightfold.ai/careers",
    }


def fetch_eightfold(company_name, platform_id):
    tenant = platform_id["tenant"]
    domain = platform_id["domain"]
    location = platform_id.get("location", "")
    api_url = f"https://{tenant}.eightfold.ai/api/apply/v2/jobs"
    print(f"[{company_name}] calling {api_url}")

    all_jobs = []
    seen_ids = set()
    start = 0
    page_size = 100  # Eightfold's max
    max_pages = 15

    for page in range(max_pages):
        params = {
            "domain": domain,
            "start": start,
            "num": page_size,
            "sort_by": "relevance",
        }
        if location:
            params["location"] = location

        try:
            r = requests.get(api_url, params=params, headers=_headers(tenant), timeout=REQUEST_TIMEOUT)
        except Exception as e:
            print(f"[{company_name}] eightfold request failed: {e}")
            break

        if r.status_code != 200:
            print(f"[{company_name}] eightfold returned {r.status_code}: {r.text[:300]}")
            break

        try:
            data = r.json()
        except Exception:
            print(f"[{company_name}] eightfold non-JSON response. First 200 chars: {r.text[:200]}")
            break

        positions = data.get("positions") or []

        if page == 0:
            total = data.get("count", "unknown")
            print(f"[{company_name}] response total field: {total}")

        if not positions:
            break

        new_count = 0
        for pos in positions:
            pos_id = pos.get("id") or pos.get("ats_job_id") or pos.get("display_job_id") or ""
            if not pos_id or pos_id in seen_ids:
                continue
            seen_ids.add(pos_id)
            new_count += 1

            title = (pos.get("name") or "").strip()

            # Eightfold gives us a primary location string and a list of
            # all locations the role is offered in. Concatenate so the
            # bot's diagnostic and filter see all of them.
            primary_loc = (pos.get("location") or "").strip()
            all_locs = pos.get("locations") or []
            extra_locs = [l for l in all_locs if l and l != primary_loc]
            if extra_locs:
                full_location = primary_loc + " | " + ", ".join(extra_locs)
            else:
                full_location = primary_loc

            posted_ts = pos.get("t_create") or pos.get("t_update") or 0
            posted_on = ""
            if posted_ts:
                # t_create / t_update are unix epoch seconds
                try:
                    from datetime import datetime, timezone
                    posted_on = datetime.fromtimestamp(int(posted_ts), tz=timezone.utc).strftime("%Y-%m-%d")
                except Exception:
                    posted_on = ""

            canonical = pos.get("canonicalPositionUrl")
            if canonical:
                full_url = canonical
            else:
                full_url = f"https://{tenant}.eightfold.ai/careers/job/{pos_id}"

            all_jobs.append({
                "title": title,
                "location": full_location or location or "",
                "company": company_name,
                "url": full_url,
                "description": (pos.get("job_description") or "")[:1500],
                "posted_on": posted_on,
            })

        if new_count == 0:
            # All positions on this page were duplicates - end of results.
            break
        if len(positions) < page_size:
            break
        start += page_size

    print(f"[{company_name}] eightfold fetched {len(all_jobs)} jobs total (newest first)")
    return all_jobs
