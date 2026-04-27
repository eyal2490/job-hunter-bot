"""
Mobileye scraper.

Mobileye uses Comeet for their careers site. Comeet has a public JSON
endpoint at comeet.com/companies/{company}/positions.
"""

import requests
from config import REQUEST_TIMEOUT, USER_AGENT


def fetch_mobileye(company_name="Mobileye"):
    """
    Mobileye's Comeet-hosted positions feed.
    """
    # Comeet companies use slugs. Mobileye's may change; the careers site URL is the source of truth.
    url = "https://www.comeet.com/careers-api/2.0/company/77.005/positions"

    headers = {
        "Accept": "application/json",
        "User-Agent": USER_AGENT,
    }

    try:
        r = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
    except Exception as e:
        print(f"[{company_name}] request failed: {e}")
        return []

    if r.status_code != 200:
        print(f"[{company_name}] returned {r.status_code}")
        return []

    try:
        data = r.json()
    except Exception:
        print(f"[{company_name}] non-JSON response")
        return []

    # Comeet returns a list of positions
    positions = data if isinstance(data, list) else data.get("positions", [])
    out = []
    for p in positions:
        title = p.get("name", "")
        location = p.get("location", {})
        if isinstance(location, dict):
            loc_text = ", ".join(filter(None, [location.get("city"), location.get("country")]))
        else:
            loc_text = str(location)

        url_pos = p.get("url_active_post", "") or p.get("url", "")
        out.append({
            "title": title,
            "location": loc_text,
            "company": company_name,
            "url": url_pos,
            "description": p.get("description", "")[:1500] if p.get("description") else "",
        })

    return out
