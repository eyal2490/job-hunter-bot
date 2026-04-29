"""
Google careers scraper.

Google's old jobs API was shut down in 2021, but their public careers
page at google.com/about/careers/applications/jobs/results is now
server-side rendered HTML. We can scrape it just like Apple.

Pagination uses ?page=N (1-indexed). 20 results per page. Stops when
a page returns no job cards (or when we've already seen all the URLs
on the new page, in case Google's pagination overflows).

The job link in the HTML doesn't always include "/jobs/" - sometimes
roles are listed without an apply link in the search results section
itself. We pick out title and location from the structured layout
each card uses: title | "Google | <locations>" | qualifications.

What we extract per role:
  - title (e.g. "Senior Formal Verification Engineer, Networking, Google Cloud")
  - location (e.g. "Tel Aviv, Israel; Haifa, Israel")
  - url (link to the role's detail page)
"""
import re
import requests
from bs4 import BeautifulSoup
from config import REQUEST_TIMEOUT, USER_AGENT


BASE_URL = "https://www.google.com/about/careers/applications/jobs/results/"


def _headers():
    return {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "User-Agent": USER_AGENT,
    }


def _parse_page(html, company_name):
    """
    Each job card in the rendered HTML has:
      <h3> or <a>  -> Title
      "Google | <City1>, Country; <City2>, Country" pattern -> Location
      Anchor with /jobs/results/<id>-<slug> path -> URL
    """
    soup = BeautifulSoup(html, "html.parser")
    out = []

    # Look for anchor tags whose href matches a job detail page.
    # Google's job detail URLs follow /about/careers/applications/jobs/results/<id>-<slug>
    title_links = soup.select('a[href*="/jobs/results/"]')

    seen_hrefs = set()
    for link in title_links:
        href = link.get("href", "")
        # Skip self-links to the search results page itself
        if not href or href.endswith("/jobs/results/") or "?" in href.split("/jobs/results/")[-1][:5]:
            continue

        title = link.get_text(strip=True)
        # Filter out short non-title link text like "Learn more", "Copy link"
        if not title or len(title) < 8:
            continue
        if title.lower() in ("learn more", "copy link", "email a friend", "share"):
            continue

        if href in seen_hrefs:
            continue
        seen_hrefs.add(href)

        # Walk up to find the card container, then look for the location text.
        # The location appears inside the same card with the pattern:
        #   "Google | <locations>" or just "<locations>" near a place icon.
        card = link
        for _ in range(8):
            card = card.parent
            if card is None:
                break
            # Card is usually an <li> or has more text content
            if card.name == "li":
                break

        location = ""
        if card is not None:
            card_text = card.get_text(" ", strip=True)
            # Pattern: "Google place <City>, <Country>" or
            # "Google | <City>, <Country>; <City>, <Country>"
            loc_match = re.search(
                r"Google\s*[|│\s]*place\s+([A-Za-z][^|]*?)(?:\s+bar_chart|\s+Mid|\s+Early|\s+Advanced|\s+Senior|$)",
                card_text,
            )
            if not loc_match:
                # Alt format: just look for "Israel" + neighborhood after "place"
                loc_match = re.search(
                    r"place\s+([A-Z][A-Za-z ,;]+(?:Israel|UK|France|US|USA))",
                    card_text,
                )
            if loc_match:
                location = loc_match.group(1).strip().rstrip(";,. ")

        full_url = href if href.startswith("http") else f"https://www.google.com{href}"

        out.append({
            "title": title,
            "location": location or "Israel",  # fetched with location=Israel filter
            "company": company_name,
            "url": full_url,
            "description": "",
            "posted_on": "",  # Google doesn't show post dates in the search results
        })

    return out


def fetch_google(company_name="Google"):
    print(f"[{company_name}] calling {BASE_URL}?location=Israel")

    all_jobs = []
    seen_urls = set()
    max_pages = 10  # ~200 jobs cap; Israel typically has 70-100

    for page in range(1, max_pages + 1):
        params = {"hl": "en-US", "location": "Israel", "page": page}

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
            break

        new_count = 0
        for job in page_jobs:
            if job["url"] in seen_urls:
                continue
            seen_urls.add(job["url"])
            all_jobs.append(job)
            new_count += 1

        if new_count == 0:
            # Pagination wrapped or stalled
            break

    print(f"[{company_name}] fetched {len(all_jobs)} jobs total (Israel filter applied at source)")
    return all_jobs


if __name__ == "__main__":
    jobs = fetch_google()
    for j in jobs[:20]:
        print(f"  {j['title'][:60]:60s} | {j['location'][:35]:35s}")
    print(f"\nTotal: {len(jobs)}")
