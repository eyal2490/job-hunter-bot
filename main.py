"""
Main orchestrator.

For each configured company, fetch jobs (newest first), filter for relevance,
deduplicate against the SQLite store, and send Telegram notifications.
"""

import sys
import traceback

from config import COMPANIES, MAX_JOBS_PER_RUN
from filters import is_relevant
from storage import init_db, is_seen, mark_seen, make_hash, count_seen
from notifier import send_job, send_status

from scrapers.workday import fetch_workday


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
    per_company_stats = []
    errors = []

    for name, platform, platform_id in COMPANIES:
        print(f"\n=== {name} ===")
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

        # Diagnostic: log Israel-based jobs found in this batch
        israel_jobs = [
            j for j in jobs
            if "israel" in (j.get("location", "") or "").lower()
        ]
        print(f"[{name}] fetched {fetched} total, {len(israel_jobs)} in Israel")

        # Show all Israel jobs (whether relevant or not) so we know what's there
        if israel_jobs:
            print(f"[{name}] Israel jobs sample:")
            for j in israel_jobs[:15]:
                rel, reason = is_relevant(j)
                marker = "✓" if rel else "✗"
                posted = j.get("posted_on", "")
                print(f"    {marker} [{posted}] {j.get('title', '?')} @ {j.get('location', '?')}")

        for job in jobs:
            relevant, reason = is_relevant(job)
            if not relevant:
                continue
            company_relevant += 1

            h = make_hash(job["company"], job.get("url", ""), job["title"])
            if is_seen(h):
                continue
            company_new += 1

            mark_seen(h, job["company"], job["title"], job.get("url", ""))

            if notified < MAX_JOBS_PER_RUN:
                if send_job(job):
                    notified += 1
                    print(f"  + sent to Telegram: {job['title']}")
                else:
                    print(f"  ! telegram failed: {job['title']}")
            else:
                print(f"  · queued (over per-run cap): {job['title']}")

        total_relevant += company_relevant
        total_new += company_new
        per_company_stats.append((name, fetched, company_relevant, company_new))
        print(f"[{name}] fetched={fetched} relevant={company_relevant} new={company_new}")

    print("\n=== Summary ===")
    print(f"Total fetched:  {total_fetched}")
    print(f"Total relevant: {total_relevant}")
    print(f"Total new:      {total_new}")
    print(f"Notified:       {notified}")

    if errors:
        msg = "⚠️ <b>Job hunter run had issues</b>\n\n"
        for n, f, r, nw in per_company_stats:
            msg += f"• {n}: fetched {f}, relevant {r}, new {nw}\n"
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
