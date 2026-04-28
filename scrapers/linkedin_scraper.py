"""
LinkedIn jobs scraper using the public guest API.

Endpoint: https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search
Returns HTML fragments (job cards) we parse with BeautifulSoup.
"""

import time
import requests
from bs4 import BeautifulSoup
from config import REQUEST_TIMEOUT, USER_AGENT, LINKEDIN_COMPANIES, LINKEDIN_TIME_RANGE


SEARCH_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
SLEEP_BETWEEN_QUERIES = 1.0  # seconds


def _headers():
    return {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }


def _parse_cards(html_text):
    soup = BeautifulSoup(html_text, "html.parser")
    jobs = []

    for card in soup.find_all("div", class_="base-card"):
        title_el = card.find("h3", class_="base-search-card__title")
        company_el = card.find("h4", class_="base-search-card__subtitle")
        location_el = card.find("span", class_="job-search-card__location")
        link_el = card.find("a", class_="base-card__full-link")
        time_el = card.find("time")

        if not title_el or not link_el:
            continue

        jobs.append({
            "title": title_el.get_text(strip=True),
            "company": company_el.get_text(strip=True) if company_el else "",
            "location": location_el.get_text(strip=True) if location_el else "",
            "url": link_el.get("href", "").split("?")[0],
            "description": "",
            "posted_on": f"Posted {time_el.get('datetime', '')}" if time_el else "",
        })

    return jobs


def _company_matches(query_name, posting_company):
    """
    Loose match: query "NVIDIA" matches "NVIDIA AI", "NVIDIA Israel", etc.
    All words from query must appear in posting company.
    """
    if not posting_company:
        return False
    posting_lower = posting_company.lower()
    for word in query_name.lower().split():
        if word not in posting_lower:
            return False
    return True


def fetch_linkedin_for_company(company_name):
    """Returns (jobs, hit_rate_limit)."""
    params = {
        "keywords": company_name,
        "location": "Israel",
        "f_TPR": LINKEDIN_TIME_RANGE,
        "start": 0,
    }

    try:
        r = requests.get(SEARCH_URL, params=params, headers=_headers(), timeout=REQUEST_TIMEOUT)
    except Exception as e:
        print(f"[LinkedIn:{company_name}] request failed: {e}")
        return [], False

    if r.status_code == 429:
        print(f"[LinkedIn:{company_name}] RATE LIMITED (429), stopping LinkedIn for this run")
        return [], True

    if r.status_code != 200:
        print(f"[LinkedIn:{company_name}] returned {r.status_code}")
        return [], False

    jobs = _parse_cards(r.text)
    filtered = [j for j in jobs if _company_matches(company_name, j.get("company", ""))]

    if jobs or filtered:
        print(f"[LinkedIn:{company_name}] fetched {len(jobs)} cards, {len(filtered)} match company")
    return filtered, False


def fetch_linkedin_all():
    all_jobs = []
    rate_limited = False

    for i, company in enumerate(LINKEDIN_COMPANIES):
        if rate_limited:
            print(f"[LinkedIn] skipping remaining companies due to rate limit")
            break

        jobs, hit_429 = fetch_linkedin_for_company(company)
        if hit_429:
            rate_limited = True
            continue

        all_jobs.extend(jobs)

        if i < len(LINKEDIN_COMPANIES) - 1:
            time.sleep(SLEEP_BETWEEN_QUERIES)

    return all_jobs
