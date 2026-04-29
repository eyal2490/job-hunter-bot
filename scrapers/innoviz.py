"""
Innoviz careers scraper.

Innoviz publishes their open positions as a server-side rendered list at:
    https://innoviz.tech/careers-3

Each role is an <a> link inside a department section, with the URL
pattern:
    /careers-3/co/{country}/{position-id}/{slug}/all

The card text contains: <Title>, then "<Country> · <Type>" on the next
line.

Israel filter: we keep only roles where the URL contains "/co/israel/"
or whose card text mentions Israel.
"""
import re
import requests
from bs4 import BeautifulSoup
from config import REQUEST_TIMEOUT, USER_AGENT


CAREERS_URL = "https://innoviz.tech/careers-3"


def _headers():
    return {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "User-Agent": USER_AGENT,
    }


def fetch_innoviz(company_name="Innoviz"):
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

    # Each job card is a link to /careers-3/co/<country>/<id>/<slug>/all
    job_links = soup.select('a[href*="/careers-3/co/"]')

    for link in job_links:
        href = link.get("href", "")
        # Skip category-level links like /careers-3/co/business/all
        # Real job links contain a country segment like /co/israel/<id>/...
        if "/all" not in href:
            continue
        # The path between /co/ and the id has 5 dots/digits like "46.761"
        if not re.search(r"/co/[a-z]+/[A-F0-9]{2}\.[A-F0-9]{3}/", href, re.I):
            continue
        if href in seen_urls:
            continue
        seen_urls.add(href)

        full_url = href if href.startswith("http") else f"https://innoviz.tech{href}"

        # Title: the link's text minus the trailing "Country · Type" line.
        # The card markup looks like:
        #   <a href=...>Process Engineer  Israel · Full-time</a>
        text = link.get_text(" ", strip=True)
        # Split off the location/type tail
        m = re.match(r"(.+?)\s+(USA|Israel|Germany|UK|France|China)\s*[·•]\s*(.+)$", text)
        if m:
            title = m.group(1).strip()
            location = m.group(2).strip()
        else:
            title = text
            location = ""

        # Fall back: extract location from the URL path (/co/israel/...)
        if not location:
            url_loc = re.search(r"/co/([a-z]+)/[A-F0-9]", href, re.I)
            if url_loc:
                location = url_loc.group(1).capitalize()

        out.append({
            "title": title,
            "location": location,
            "company": company_name,
            "url": full_url,
            "description": "",
            "posted_on": "",
        })

    print(f"[{company_name}] fetched {len(out)} jobs total")
    return out


if __name__ == "__main__":
    jobs = fetch_innoviz()
    for j in jobs:
        print(f"  {j['title'][:60]:60s} | {j['location']:15s}")
    print(f"\nTotal: {len(jobs)}")
