"""
Valens Semiconductor careers scraper.

Valens publishes their open positions as a server-side rendered list at:
    https://www.valens.com/positions/

Each role is wrapped in an <a> linking to /position/<slug>/. The card
text contains the title (often broken across two lines with newlines),
the location (e.g. "Valens HQ, Hod Hasharon, Israel"), the department,
and the employment type.

All Valens jobs are in Hod Hasharon (Israel) at the moment, but we
extract the location from the card text in case that changes.
"""
import re
import requests
from bs4 import BeautifulSoup
from config import REQUEST_TIMEOUT, USER_AGENT


CAREERS_URL = "https://www.valens.com/positions/"


def _headers():
    return {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "User-Agent": USER_AGENT,
    }


def fetch_valens(company_name="Valens"):
    print(f"[{company_name}] calling {CAREERS_URL}")

    try:
        r = requests.get(CAREERS_URL, headers=_headers(), timeout=REQUEST_TIMEOUT)
    except Exception as e:
        print(f"[{company_name}] request failed: {e}")
        return []

    if r.status_code != 200:
        print(f"[{company_name}] returned {r.status_code}")
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    out = []
    seen_urls = set()

    # Each job card is a link with href matching /position/<slug>/
    job_links = soup.select('a[href*="/position/"]')

    for link in job_links:
        href = link.get("href", "")
        # Need a slug after /position/ — skip category links
        if not re.search(r"/position/[a-z0-9-]+/?$", href):
            continue
        if href in seen_urls:
            continue
        seen_urls.add(href)

        full_url = href if href.startswith("http") else f"https://www.valens.com{href}"

        # Card text typically reads:
        #   "Title Title  Valens HQ, Hod Hasharon, Israel  Department  Full Time"
        # We split on the location prefix "Valens HQ" or fall back to known
        # cities to recover title and location.
        text = link.get_text(" ", strip=True)
        # Collapse multiple spaces
        text = re.sub(r"\s+", " ", text)

        title = text
        location = ""

        loc_match = re.search(
            r"(Valens HQ,\s*[^,]+,\s*Israel|Hod Hasharon,\s*Israel|[A-Z][a-zA-Z ]+,\s*Israel)",
            text,
        )
        if loc_match:
            location = loc_match.group(1).strip()
            title = text[:loc_match.start()].strip()

        # Title sometimes contains the bold-tag artifact; clean stray
        # leading/trailing punctuation.
        title = re.sub(r"\s+", " ", title).strip(" -|·")

        if not title:
            continue

        out.append({
            "title": title,
            "location": location or "Hod Hasharon, Israel",
            "company": company_name,
            "url": full_url,
            "description": "",
            "posted_on": "",
        })

    print(f"[{company_name}] fetched {len(out)} jobs total")
    return out


if __name__ == "__main__":
    jobs = fetch_valens()
    for j in jobs:
        print(f"  {j['title'][:60]:60s} | {j['location']}")
    print(f"\nTotal: {len(jobs)}")
