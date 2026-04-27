"""
Main orchestrator.

For each configured company, fetch jobs, filter for relevance,
deduplicate against the SQLite store, and send Telegram notifications
for new matches.

This script is invoked by GitHub Actions on a schedule.
"""

import sys
import traceback

from config import COMPANIES, MAX_JOBS_PER_RUN
from filters import is_relevant
from storage import init_db, is_seen, mark_seen, make_hash, count_seen
from notifier import send_job, send_status

from scrapers.workday import fetch_workday
from scrapers.intel import fetch_intel
from scrapers.mobileye import fetch_mobileye


def fetch_company(name, platform, platform_id):
    """Dispatch to the appropriate scraper based on platform."""
    if platform == "workday":
        return fetch_workday(name, platform_id)
    if platform == "intel_custom":
        return fetch_intel(name)
    if platform == "mobileye_custom":
        return fetch_mobileye(name)
    print(f"[{name}] unknown platform: {platform}")
    return []


def run():
    init_db()
    print(f"DB starts with {count_seen()} seen jobs")

    total_fetched = 0
    total_relevant = 0
    total_new = 0
    notified = 0
    per_company_stats = []
    errors = []

    for name, platform, platform_id in COMPANIES:
        print(f"\n=== {name} ({platform}) ===")
        try:
            jobs = fetch_company(name, platform, platform_id)
        except Exception as e:
            print(f"[{name}] crashed: {e}")
            traceback.print_exc()
            errors.append(f"{name}: {e}")
            per_company_stats.append((name, 0, 0, 0))
            continue

        fetched = len(jobs)
        total_fetched += fetched
        company_relevant = 0
        company_new = 0

        for job in jobs:
            relevant, reason = is_relevant(job)
            if not relevant:
                continue
            company_relevant += 1

            h = make_hash(job["company"], job.get("url", ""), job["title"])
            if is_seen(h):
                continue
            company_new += 1

            # Mark as seen FIRST, then notify. If telegram fails we don't re-notify.
            mark_seen(h, job["company"], job["title"], job.get("url", ""))

            if notified < MAX_JOBS_PER_RUN:
                if send_job(job):
                    notified += 1
                    print(f"  + sent: {job['title']}")
                else:
                    print(f"  ! telegram failed: {job['title']}")
            else:
                print(f"  · queued (over per-run cap): {job['title']}")

        total_relevant += company_relevant
        total_new += company_new
        per_company_stats.append((name, fetched, company_relevant, company_new))
        print(f"[{name}] fetched={fetched} relevant={company_relevant} new={company_new}")

    # Summary
    print("\n=== Summary ===")
    print(f"Total fetched:  {total_fetched}")
    print(f"Total relevant: {total_relevant}")
    print(f"Total new:      {total_new}")
    print(f"Notified:       {notified}")

    # Send a status message ONLY on first run (when DB was empty) or on errors,
    # to avoid spamming Telegram every 15 minutes.
    if errors:
        msg = "⚠️ <b>Job hunter run had issues</b>\n\n"
        for name, fetched, rel, new in per_company_stats:
            msg += f"• {name}: fetched {fetched}, relevant {rel}, new {new}\n"
        msg += "\n<b>Errors:</b>\n"
        for e in errors[:5]:
            msg += f"• {e[:200]}\n"
        send_status(msg)


if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        print(f"FATAL: {e}")
        traceback.print_exc()
        send_status(f"❌ Job hunter crashed: <code>{str(e)[:200]}</code>")
        sys.exit(1)
