"""
Filtering logic: decides whether a job is relevant for an EE student (year 3).

Two-tier matching:
  1. Title MUST contain a student-level indicator (student/intern/etc.)
  2. Title or description MUST contain an EE field indicator (hardware/FPGA/etc.)
Plus negative checks for seniority, PhD-only, years of experience, etc.
"""

from config import (
    LOCATION_KEYWORDS,
    STUDENT_LEVEL_TITLE_KEYWORDS,
    FIELD_RELEVANCE_KEYWORDS,
    NEGATIVE_TITLE_KEYWORDS,
    NEGATIVE_DESCRIPTION_PHRASES,
)


def _norm(text):
    if not text:
        return ""
    return str(text).lower().strip()


def is_in_israel(location_text):
    loc = _norm(location_text)
    if not loc:
        return True  # don't reject just for missing location
    return any(kw in loc for kw in LOCATION_KEYWORDS)


def title_has_student_level(title):
    """The title MUST indicate a student/intern role."""
    title_lower = _norm(title)
    return any(kw in title_lower for kw in STUDENT_LEVEL_TITLE_KEYWORDS)


def has_field_relevance(title, description):
    """Title or description must mention an EE-relevant field."""
    text = _norm(title) + " " + _norm(description)
    return any(kw in text for kw in FIELD_RELEVANCE_KEYWORDS)


def has_negative_signal(title, description):
    title_lower = _norm(title)
    for kw in NEGATIVE_TITLE_KEYWORDS:
        if kw in title_lower:
            return True, f"title contains '{kw}'"

    desc_lower = _norm(description)
    for phrase in NEGATIVE_DESCRIPTION_PHRASES:
        if phrase in desc_lower:
            return True, f"description contains '{phrase}'"

    return False, ""


def is_relevant(job):
    """
    Returns (is_relevant: bool, reason: str)
    """
    title = job.get("title", "")
    description = job.get("description", "")
    location = job.get("location", "")

    if not is_in_israel(location):
        return False, f"not in Israel: {location}"

    if not title_has_student_level(title):
        return False, "title does not indicate student/intern role"

    has_neg, neg_reason = has_negative_signal(title, description)
    if has_neg:
        return False, neg_reason

    if not has_field_relevance(title, description):
        return False, "no EE-field keyword match"

    return True, "match"
