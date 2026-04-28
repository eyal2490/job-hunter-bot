"""
Main orchestrator.

Fetches jobs from:
  1. Workday-based careers pages (NVIDIA direct)
  2. LinkedIn guest API for many companies at once

Filters for relevance, deduplicates against SQLite store,
and sends Telegram notifications for new matches.
"""

import sys
import traceback

from config import COMPANIES, MAX_JOBS_PER_RUN
from filters import is_relevant
from storage import init_db, is_seen, mark_seen, make_hash, count_seen
from notifier import send_job, send_status

from scrapers.workday import fetch_workday
from scrapers.linkedin_scraper import fetch_linkedin_all


def fetch_company(name, platform, platform_id):
    if platform == "workday":
        return fetch_workday(name, platform_id)
    print(f"[{name}] unknown platform: {platform}")
    return []


def run():
    init_db()
    print(f"DB starts with {count_seen()} seen jobs")

    total_fetched = 0
    total_relevant = 0
    total_new = 0
    notified = 0
    errors = []

    # ----- Source 1: Workday-based companies -----
    for name, platform, platform_id in COMPANIES:
        print(f"\n=== {name} (workday) ===")
        try:
            jobs = fetch_company(name, platform, platform_id)
        except Exception as e:
            print(f"[{name}] crashed: {e}")
            traceback.print_exc()
            errors.append(f"{name}: {e}")
            continue

        notified += _process_jobs(name, jobs, notified)
        total_fetched += len(jobs)

    # ----- Source 2: LinkedIn (all configured companies) -----
    print(f"\n=== LinkedIn ===")
    try:
        linkedin_jobs = fetch_linkedin_all()
        print(f"[LinkedIn] total fetched across all companies: {len(linkedin_jobs)}")
        total_fetched += len(linkedin_jobs)
        notified += _process_jobs("LinkedIn", linkedin_jobs, notified)
    except Exception as e:
        print(f"[LinkedIn] crashed: {e}")
        traceback.print_exc()
        errors.append(f"LinkedIn: {e}")

    print(f"\n=== Summary ===")
    print(f"Total fetched:  {total_fetched}")
    print(f"Notified:       {notified}")

    if errors:
        msg = "⚠️ <b>Job hunter run had issues</b>\n\n"
        for e in errors[:5]:
            msg += f"• {e[:200]}\n"
        send_status(msg)


def _process_jobs(source_label, jobs, current_notified):
    """Filter, dedupe, and send. Returns number of new notifications sent."""
    if not jobs:
        return 0

    # Show Israel jobs sample for diagnostic
    israel_jobs = [
        j for j in jobs
        if "israel" in (j.get("location", "") or "").lower()
    ]
    if israel_jobs:
        print(f"[{source_label}] {len(israel_jobs)} jobs in Israel:")
        for j in israel_jobs[:10]:
            rel, reason = is_relevant(j)
            marker = "✓" if rel else "✗"
            posted = j.get("posted_on", "")
            print(f"    {marker} [{posted}] {j.get('title', '?')} @ {j.get('company', '?')} - {j.get('location', '?')}")

    sent_count = 0
    for job in jobs:
        relevant, reason = is_relevant(job)
        if not relevant:
            continue

        h = make_hash(job["company"], job.get("url", ""), job["title"])
        if is_seen(h):
            continue

        mark_seen(h, job["company"], job["title"], job.get("url", ""))

        if current_notified + sent_count < MAX_JOBS_PER_RUN:
            if send_job(job):
                sent_count += 1
                print(f"  + sent: {job['title']} @ {job['company']}")
            else:
                print(f"  ! telegram failed: {job['title']}")
        else:
            print(f"  · queued (over per-run cap): {job['title']}")

    return sent_count


if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        print(f"FATAL: {e}")
        traceback.print_exc()
        send_status(f"❌ Job hunter crashed: <code>{str(e)[:200]}</code>")
        sys.exit(1)
