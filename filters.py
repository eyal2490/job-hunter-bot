"""
Filtering logic: decides whether a job is relevant for an EE student (year 3).
"""

from config import (
    LOCATION_KEYWORDS,
    POSITIVE_KEYWORDS,
    NEGATIVE_TITLE_KEYWORDS,
    NEGATIVE_DESCRIPTION_PHRASES,
)


def _norm(text):
    """Normalize text for matching: lowercase, strip whitespace."""
    if not text:
        return ""
    return str(text).lower().strip()


def is_in_israel(location_text):
    """Check if a job location is in Israel."""
    loc = _norm(location_text)
    if not loc:
        # If we don't have a location string, don't reject — let it pass and rely on other filters.
        # Most company scrapers below already filter by country at the API level.
        return True
    return any(kw in loc for kw in LOCATION_KEYWORDS)


def has_positive_keyword(title, description):
    """Job must contain at least one positive keyword."""
    text = _norm(title) + " " + _norm(description)
    return any(kw in text for kw in POSITIVE_KEYWORDS)


def has_negative_signal(title, description):
    """Reject jobs with strong negative signals in title or description."""
    title_lower = _norm(title)
    for kw in NEGATIVE_TITLE_KEYWORDS:
        if kw in title_lower:
            return True

    desc_lower = _norm(description)
    for phrase in NEGATIVE_DESCRIPTION_PHRASES:
        if phrase in desc_lower:
            return True

    return False


def is_relevant(job):
    """
    Top-level relevance check.

    job is a dict with keys: title, description, location, company, url
    Returns (is_relevant: bool, reason: str)
    """
    title = job.get("title", "")
    description = job.get("description", "")
    location = job.get("location", "")

    if not is_in_israel(location):
        return False, f"not in Israel: {location}"

    if has_negative_signal(title, description):
        return False, "negative signal (senior/manager/many-years-exp)"

    if not has_positive_keyword(title, description):
        return False, "no positive keyword match"

    return True, "match"
