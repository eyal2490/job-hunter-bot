"""
Oracle Recruiting Cloud HCM scraper.

Many large companies use Oracle's Recruiting Cloud product for their
careers site. The customer-facing URL (e.g. careers.ti.com) is often
just marketing - the actual jobs UI and JSON API live on Oracle's
hosted pod, e.g.:
    https://edbz.fa.us2.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX/jobs

We hit the underlying JSON API directly:
    GET https://{host}/hcmRestApi/resources/latest/recruitingCEJobRequisitions

Critical: results are paginated 50 at a time, sorted newest-first by
POSTING_DATES_DESC. We fetch many pages so main.py can apply its own
Israel filter the same way it does for Workday.

Currently used by:
    Texas Instruments  (host=edbz.fa.us2.oraclecloud.com, site=CX)
"""
import requests
from config import REQUEST_TIMEOUT, USER_AGENT


def _headers(host):
    return {
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "User-Agent": USER_AGENT,
        "Origin": f"https://{host}",
        "Referer": f"https://{host}/hcmUI/CandidateExperience/en/sites",
    }


def fetch_oracle_hcm(company_name, platform_id):
    host = platform_id["host"]
    site = platform_id["site"]
    api_url = f"https://{host}/hcmRestApi/resources/latest/recruitingCEJobRequisitions"
    print(f"[{company_name}] calling {api_url}")

    all_jobs = []
    offset = 0
    page_size = 50
    # Up to 1250 jobs - matches the wide-coverage approach in workday.py
    # because we filter by location (Israel) on our side and a global
    # company may have many non-Israel jobs in the most-recent list.
    max_pages = 25

    for page in range(max_pages):
        # Oracle's `finder` parameter encodes the search.
        # Empty keyword + sortBy=POSTING_DATES_DESC = all jobs, newest first.
        finder = ",".join([
            "findReqs",
            f"siteNumber={site}",
            "facetsList=LOCATIONS;WORK_LOCATIONS;WORKPLACE_TYPES;TITLES;"
            "CATEGORIES;ORGANIZATIONS;POSTING_DATES;FLEX_FIELDS",
            f"limit={page_size}",
            f"offset={offset}",
            "sortBy=POSTING_DATES_DESC",
        ])
        params = {
            "onlyData": "true",
            "expand": "requisitionList.secondaryLocations,requisitionList.requisitionFlexFields",
            "finder": finder,
        }

        try:
            r = requests.get(
                api_url,
                params=params,
                headers=_headers(host),
                timeout=REQUEST_TIMEOUT,
            )
        except Exception as e:
            print(f"[{company_name}] oracle_hcm request failed: {e}")
            break

        if r.status_code != 200:
            print(f"[{company_name}] oracle_hcm returned {r.status_code}: {r.text[:300]}")
            break

        try:
            data = r.json()
        except Exception:
            print(f"[{company_name}] oracle_hcm non-JSON response. First 200 chars: {r.text[:200]}")
            break

        # Oracle wraps the list one level deep:
        #   { "items": [ { "TotalJobsCount": ..., "hasMore": ..., "requisitionList": [...] } ] }
        items = data.get("items") or []
        if not items:
            break
        wrapper = items[0]

        if page == 0:
            total = wrapper.get("TotalJobsCount", "unknown")
            print(f"[{company_name}] response total field: {total}")

        postings = wrapper.get("requisitionList") or []
        if not postings:
            break

        for req in postings:
            req_id = req.get("Id") or req.get("id") or ""
            title = req.get("Title") or ""
            primary = (req.get("PrimaryLocation") or "").strip()

            # Fold secondary locations into the location string so main.py's
            # "israel" substring check picks up jobs primarily listed elsewhere
            # but also offered in Israel.
            secondary_names = [
                str(sec.get("Name") or "").strip()
                for sec in (req.get("secondaryLocations") or [])
            ]
            secondary_names = [s for s in secondary_names if s and s != primary]
            if secondary_names:
                location = primary + " | " + ", ".join(secondary_names)
            else:
                location = primary

            posted_on = req.get("PostedDate") or req.get("PostingStartDate") or ""

            if req_id:
                full_url = f"https://{host}/hcmUI/CandidateExperience/en/sites/{site}/job/{req_id}"
            else:
                full_url = f"https://{host}/hcmUI/CandidateExperience/en/sites/{site}/jobs"

            all_jobs.append({
                "title": title,
                "location": location,
                "company": company_name,
                "url": full_url,
                "description": "",
                "posted_on": str(posted_on),
            })

        # Oracle signals end-of-pagination on the wrapper.
        if not wrapper.get("hasMore", False):
            break
        if len(postings) < page_size:
            break
        offset += page_size

    print(f"[{company_name}] oracle_hcm fetched {len(all_jobs)} jobs total (newest first)")
    return all_jobs
