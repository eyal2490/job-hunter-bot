"""
Main orchestrator.
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

        # Diagnostic: scan ALL jobs for early-career indicators (broader than just student/intern)
        # This helps discover what naming conventions the company uses
        early_career_patterns = [
            "student", "intern", "סטודנט", "מתמחה",
            "junior", "graduate", "entry", "early career", "early-career",
            "new grad", "rotation", "trainee", "associate",
            "i ",       # for "Engineer I"
            " i,", " i ", " i)",  # patterns like "Engineer I,"
        ]
        early_jobs = []
        for j in jobs:
            t = (j.get("title", "") or "").lower()
            if any(p in t for p in early_career_patterns):
                early_jobs.append(j)

        if early_jobs:
            print(f"[{name}] {len(early_jobs)} jobs match early-career patterns:")
            for j in early_jobs[:30]:
                rel, reason = is_relevant(j)
                marker = "✓" if rel else "✗"
                print(f"    {marker} {j.get('title', '?')} @ {j.get('location', '?')}  ({reason})")
        else:
            print(f"[{name}] NO jobs matched any early-career pattern")
            print(f"[{name}] sample 10 random titles for context:")
            for j in jobs[:10]:
                print(f"    - {j.get('title', '?')} @ {j.get('location', '?')}")

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
                    print(f"  + sent: {job['title']}")
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
