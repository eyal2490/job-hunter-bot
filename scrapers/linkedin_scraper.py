"""
LinkedIn jobs scraper using the public guest API.

LinkedIn exposes job listings to anonymous browsers via:
  https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search

The endpoint returns HTML fragments (job cards) that we parse for title,
company, location, posting date, and job URL.

LinkedIn supports filters via URL parameters - we use:
  - keywords:    free-text search
  - location:    geo-coded location string
  - f_TPR=r3600  time-posted-range: jobs in the last 1 hour
                 (we use this to only get the freshest jobs each run)
  - f_E:         experience level (1=Internship, 2=Entry level, 3=Associate)

We do multiple targeted searches (one per company name) and let LinkedIn
do the company filtering, since their global "Israel + EE" search returns
too much noise.
"""

import requests
from bs4 import BeautifulSoup
from config import REQUEST_TIMEOUT, USER_AGENT, LINKEDIN_COMPANIES, LINKEDIN_TIME_RANGE


SEARCH_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"


def _headers():
    return {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }


def _parse_cards(html_text):
    """Parse LinkedIn job cards from HTML fragment."""
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

        title = title_el.get_text(strip=True)
        company = company_el.get_text(strip=True) if company_el else ""
        location = location_el.get_text(strip=True) if location_el else ""
        url = link_el.get("href", "").split("?")[0]  # strip tracking params
        posted_on = time_el.get("datetime", "") if time_el else ""

        jobs.append({
            "title": title,
            "company": company,
            "location": location,
            "url": url,
            "description": "",  # LinkedIn job detail requires a separate request
            "posted_on": f"Posted {posted_on}" if posted_on else "",
        })

    return jobs


def fetch_linkedin_for_company(company_name):
    """Search LinkedIn for jobs at a specific company in Israel."""
    # Use keywords as just the company name. LinkedIn matches it against the
    # company field of postings, returning only that company's jobs.
    params = {
        "keywords": company_name,
        "location": "Israel",
        "f_TPR": LINKEDIN_TIME_RANGE,  # e.g. "r3600" = last hour, "r86400" = last 24h
        "start": 0,
    }

    try:
        r = requests.get(
            SEARCH_URL,
            params=params,
            headers=_headers(),
            timeout=REQUEST_TIMEOUT,
        )
    except Exception as e:
        print(f"[LinkedIn:{company_name}] request failed: {e}")
        return []

    if r.status_code != 200:
        print(f"[LinkedIn:{company_name}] returned {r.status_code}: {r.text[:150]}")
        return []

    jobs = _parse_cards(r.text)

    # LinkedIn's keyword search is fuzzy - filter strictly by company name match
    company_lower = company_name.lower()
    filtered = [
        j for j in jobs
        if company_lower in j.get("company", "").lower()
    ]

    print(f"[LinkedIn:{company_name}] fetched {len(jobs)} cards, {len(filtered)} match company")
    return filtered


def fetch_linkedin_all():
    """Fetch jobs for all configured LinkedIn companies."""
    all_jobs = []
    for company in LINKEDIN_COMPANIES:
        jobs = fetch_linkedin_for_company(company)
        all_jobs.extend(jobs)
    return all_jobs
