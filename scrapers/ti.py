"""
scrapers/ti.py - Texas Instruments scraper.

TI runs careers on Oracle Recruiting Cloud. The customer-facing site at
careers.ti.com is just marketing; the actual jobs UI and JSON API live at:
    https://edbz.fa.us2.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX/jobs

We hit the underlying JSON API directly:
    GET https://edbz.fa.us2.oraclecloud.com/hcmRestApi/resources/latest/recruitingCEJobRequisitions

What this module does:
- Pulls every currently-posted TI requisition (paginated 50 at a time).
- Filters down to Israel-based roles by location string.
- Normalizes each result into the bot's standard dict shape so the
  central student/intern + chip-design filter can process it the same
  way it processes Workday and LinkedIn results.

This module does NOT do the title/keyword filtering for "student",
"intern", "verification", etc. - that lives in the central filter.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Set

import requests

logger = logging.getLogger(__name__)

COMPANY = "Texas Instruments"
SOURCE = "ti_oracle_hcm"

# Oracle "pod" hosting TI's Recruiting Cloud instance - confirmed by
# resolving the Search Jobs link from careers.ti.com.
ORACLE_HOST = "https://edbz.fa.us2.oraclecloud.com"
SITE_NUMBER = "CX"

BASE_URL = f"{ORACLE_HOST}/hcmRestApi/resources/latest/recruitingCEJobRequisitions"
JOB_URL_TEMPLATE = (
    f"{ORACLE_HOST}/hcmUI/CandidateExperience/en/sites/{SITE_NUMBER}/job/{{job_id}}"
)

PAGE_SIZE = 50
MAX_PAGES = 20  # 1000-job safety cap

ISRAEL_TOKENS = (
    "Israel",
    "Ra'anana", "Raanana",
    "Herzliya", "Herzlia",
    "Tel Aviv", "Tel-Aviv",
    "Haifa",
    "Jerusalem",
    "Kfar Saba", "Kfar-Saba",
    "Petah Tikva", "Petach Tikva",
)

DEFAULT_HEADERS = {
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (compatible; JobHunterBot/1.0)",
}


def _build_finder(offset: int, limit: int) -> str:
    """Build Oracle's `finder` query parameter."""
    parts = [
        "findReqs",
        f"siteNumber={SITE_NUMBER}",
        # Facets aren't strictly required, but Oracle's UI always sends them
        # and stricter deployments can 400 without them.
        "facetsList=LOCATIONS;WORK_LOCATIONS;WORKPLACE_TYPES;TITLES;"
        "CATEGORIES;ORGANIZATIONS;POSTING_DATES;FLEX_FIELDS",
        f"limit={limit}",
        f"offset={offset}",
        "sortBy=POSTING_DATES_DESC",
    ]
    return ",".join(parts)


def _request_page(session: requests.Session, offset: int) -> Dict[str, Any]:
    params = {
        "onlyData": "true",
        "expand": "requisitionList.secondaryLocations,requisitionList.requisitionFlexFields",
        "finder": _build_finder(offset, PAGE_SIZE),
    }
    resp = session.get(BASE_URL, params=params, headers=DEFAULT_HEADERS, timeout=20)
    resp.raise_for_status()
    return resp.json()


def _is_israel(req: Dict[str, Any]) -> bool:
    if "IL" in (req.get("PrimaryLocationCountry") or ""):
        return True

    parts: List[str] = [
        str(req.get("PrimaryLocation") or ""),
        str(req.get("PrimaryLocationCountry") or ""),
    ]
    for sec in req.get("secondaryLocations") or []:
        parts.append(str(sec.get("Name") or ""))
        parts.append(str(sec.get("CountryCode") or ""))
    haystack = " | ".join(parts)
    return any(token in haystack for token in ISRAEL_TOKENS)


def _normalize(req: Dict[str, Any]) -> Dict[str, Any]:
    job_id = req.get("Id") or req.get("id") or ""
    title = (req.get("Title") or "").strip()
    location = (req.get("PrimaryLocation") or "").strip()
    posted = req.get("PostedDate") or req.get("PostingStartDate") or ""

    # Pass through fields the central filter can match on
    # ("student"/"intern" + "chip design / verification / analog / board").
    categories = req.get("Category") or req.get("Categories") or ""
    if isinstance(categories, list):
        categories = ", ".join(c for c in categories if c)
    organization = req.get("Organization") or req.get("PrimaryOrganization") or ""
    work_type = req.get("WorkerType") or req.get("WorkType") or ""

    return {
        "company": COMPANY,
        "id": str(job_id),
        "title": title,
        "location": location,
        "url": JOB_URL_TEMPLATE.format(job_id=job_id) if job_id else "",
        "posted_at": str(posted),
        "category": str(categories),
        "organization": str(organization),
        "work_type": str(work_type),
        "source": SOURCE,
    }


def _extract_items(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Oracle wraps the list one level deep: payload['items'][0]['requisitionList']."""
    items = payload.get("items") or []
    if not items:
        return []
    return items[0].get("requisitionList") or []


def _has_more(payload: Dict[str, Any]) -> bool:
    items = payload.get("items") or []
    if not items:
        return False
    if "hasMore" in items[0]:
        return bool(items[0]["hasMore"])
    return False  # caller also stops on empty page, so this is safe


def fetch_jobs(israel_only: bool = True) -> List[Dict[str, Any]]:
    """Fetch all currently-posted TI requisitions; optionally filter to Israel."""
    out: List[Dict[str, Any]] = []
    seen: Set[str] = set()

    with requests.Session() as session:
        for page in range(MAX_PAGES):
            offset = page * PAGE_SIZE
            try:
                payload = _request_page(session, offset)
            except requests.HTTPError as e:
                logger.warning("TI: HTTP error at offset=%d: %s", offset, e)
                break
            except requests.RequestException as e:
                logger.warning("TI: network error at offset=%d: %s", offset, e)
                break

            items = _extract_items(payload)
            if not items:
                break

            for req in items:
                if israel_only and not _is_israel(req):
                    continue
                norm = _normalize(req)
                if not norm["id"] or norm["id"] in seen:
                    continue
                seen.add(norm["id"])
                out.append(norm)

            if not _has_more(payload):
                break

    logger.info("TI: %d jobs (israel_only=%s)", len(out), israel_only)
    return out


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    jobs = fetch_jobs(israel_only=True)
    for j in jobs[:20]:
        print(f"{j['title'][:55]:55s} | {j['location'][:25]:25s} | {j['url']}")
    print(f"\nTotal: {len(jobs)}")
