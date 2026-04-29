"""
Altair Semiconductor careers scraper.

Altair publishes their open positions as a server-side rendered list at:
    https://www.altairsemi.com/careers/

Each role is a link with URL pattern /careers/<id> where id looks like
"07.369" or "ED.86B". The card layout is:
    <a>Title</a>  Location

Currently (as of writing), Altair has both an "ASIC Design Student for
the SoC Group" and a "Verification Student for the SoC group" role
posted in Israel — exactly the type of role the bot is hunting for.
"""
import re
import requests
from bs4 import BeautifulSoup
from config import REQUEST_TIMEOUT, USER_AGENT


CAREERS_URL = "https://www.altairsemi.com/careers/"


def _headers():
    return {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "User-Agent": USER_AGENT,
    }


def fetch_altair(company_name="Altair Semiconductor"):
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

    # Each job link has href matching /careers/<id> where id is like "07.369"
    job_links = soup.select('a[href*="/careers/"]')

    for link in job_links:
        href = link.get("href", "")
        # Match the id pattern "XX.XXX" with two segments of hex/digits
        if not re.search(r"/careers/[A-F0-9]{2}\.[A-F0-9]{3}\b", href, re.I):
            continue

        title = link.get_text(strip=True)
        if not title or title.lower() == "join our team":
            continue

        # The same role appears twice in the markup (title link and
        # "Join Our Team" button). De-dup on the URL.
        if href in seen_urls:
            continue
        seen_urls.add(href)

        full_url = href if href.startswith("http") else f"https://www.altairsemi.com{href}"

        # Location appears as plain text after the title link in the card.
        # Walk up to find the parent block, then look for "Israel" or
        # "Taiwan Office" etc.
        location = ""
        parent = link.parent
        for _ in range(5):
            if parent is None:
                break
            ptext = parent.get_text(" ", strip=True)
            loc_match = re.search(r"\b(Israel|Taiwan Office|Taiwan|USA|UK|Hod ?HaSharon)\b", ptext)
            if loc_match:
                location = loc_match.group(1)
                break
            parent = parent.parent

        out.append({
            "title": title,
            "location": location or "Israel",  # Altair is HQ'd in Hod HaSharon
            "company": company_name,
            "url": full_url,
            "description": "",
            "posted_on": "",
        })

    print(f"[{company_name}] fetched {len(out)} jobs total")
    return out


if __name__ == "__main__":
    jobs = fetch_altair()
    for j in jobs:
        print(f"  {j['title'][:60]:60s} | {j['location']}")
    print(f"\nTotal: {len(jobs)}")
