"""
Apple careers scraper.

Apple runs jobs.apple.com on their own server-side-rendered platform.
Every job posting is present in the HTML of the search page as a list
item - no JavaScript or API authentication needed. We just parse the
HTML and extract the job cards.

Search URL with Israel filter:
    https://jobs.apple.com/en-us/search?location=israel-ISR&page=N

The page parameter is 1-indexed. We fetch pages until one returns
no job cards, with a safety cap.

Each job card on the page contains:
  - Job title and detail URL: <a href="/en-us/details/<id>/<slug>?team=...">Title</a>
  - Posted date: appears as text near the team name (e.g. "HardwareMar 31, 2026")
  - Location: appears under "Location" label (e.g. "Herzliya", "Haifa",
    "Various Locations within Israel")

Because we already filter Israel at fetch time via the URL parameter,
all results are Israel-relevant and main.py's Israel filter is a no-op
for this scraper.
"""
import re
import requests
from bs4 import BeautifulSoup
from config import REQUEST_TIMEOUT, USER_AGENT


BASE_URL = "https://jobs.apple.com/en-us/search"
LOCATION_PARAM = "israel-ISR"


def _headers():
    return {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "User-Agent": USER_AGENT,
    }


def _parse_page(html, company_name):
    """
    Extract job cards from one search page.

    Apple wraps each result in an <li> containing an <a> with the role
    detail URL. We anchor on the <a href="/en-us/details/..."> and then
    walk to its surrounding container to pull team, posted date, and
    location.
    """
    soup = BeautifulSoup(html, "html.parser")
    out = []

    # Each role card has an <a> with href starting with /en-us/details/
    # whose text is the title (e.g. "Wireless SoC Design Verification Engineer").
    title_links = soup.select('a[href^="/en-us/details/"]')

    seen_hrefs = set()
    for link in title_links:
        href = link.get("href", "")
        # Each card has multiple links to the same detail page (title link,
        # "See full role description" link). De-duplicate on href, keep the
        # one whose text looks like a real title (longer, not "See full...").
        if not href:
            continue

        title = link.get_text(strip=True)
        if not title or title.lower().startswith("see full"):
            continue

        if href in seen_hrefs:
            continue
        seen_hrefs.add(href)

        # Walk up to the <li> or <article> containing this card to find
        # location and date.
        card = link
        for _ in range(8):
            card = card.parent
            if card is None:
                break
            if card.name in ("li", "article"):
                break

        location = ""
        posted_on = ""
        if card is not None:
            card_text = card.get_text(" ", strip=True)

            # Location: Apple labels it "Location<value>" with no space, e.g.
            # "LocationHerzliya" or "LocationVarious Locations within Israel".
            loc_match = re.search(
                r"Location\s*([A-Za-z][A-Za-z ,/'\-]+?)(?=\s+Actions|\s+See full|\s+Share|$)",
                card_text,
            )
            if loc_match:
                location = loc_match.group(1).strip()

            # Posted date: appears as "<Team><Month> <DD>, <YYYY>", e.g.
            # "HardwareMar 31, 2026". Match the date part directly.
            date_match = re.search(
                r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+\d{4}",
                card_text,
            )
            if date_match:
                posted_on = date_match.group(0)

        full_url = "https://jobs.apple.com" + href

        out.append({
            "title": title,
            "location": location or "Israel",  # we fetched with location=israel-ISR
            "company": company_name,
            "url": full_url,
            "description": "",
            "posted_on": posted_on,
        })

    return out


def fetch_apple(company_name="Apple"):
    print(f"[{company_name}] calling {BASE_URL}?location={LOCATION_PARAM}")

    all_jobs = []
    seen_urls = set()
    max_pages = 15  # Apple shows ~20/page; cap protects against runaway pagination

    for page in range(1, max_pages + 1):
        params = {"location": LOCATION_PARAM, "page": page}

        try:
            r = requests.get(BASE_URL, params=params, headers=_headers(), timeout=REQUEST_TIMEOUT)
        except Exception as e:
            print(f"[{company_name}] request failed on page {page}: {e}")
            break

        if r.status_code != 200:
            print(f"[{company_name}] returned {r.status_code} on page {page}")
            break

        page_jobs = _parse_page(r.text, company_name)
        if not page_jobs:
            # No more results. Apple's pagination doesn't 404 past the
            # last page - it returns a page with no job cards.
            break

        # Dedup across pages just in case Apple's pagination overlaps.
        new_count = 0
        for job in page_jobs:
            if job["url"] in seen_urls:
                continue
            seen_urls.add(job["url"])
            all_jobs.append(job)
            new_count += 1

        if new_count == 0:
            # Same URLs as last page - we've wrapped or stalled. Stop.
            break

    print(f"[{company_name}] fetched {len(all_jobs)} jobs total (Israel filter applied at source)")
    return all_jobs


if __name__ == "__main__":
    jobs = fetch_apple()
    for j in jobs[:20]:
        print(f"  [{j['posted_on']:20s}] {j['title'][:55]:55s} | {j['location'][:30]:30s}")
    print(f"\nTotal: {len(jobs)}")
