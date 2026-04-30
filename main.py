"""
Main orchestrator.

Fetches jobs from:
  1. Workday-based careers pages (NVIDIA, Intel, Marvell, Broadcom,
     Samsung, Motorola, ...)
  2. Oracle Recruiting Cloud HCM-based careers pages (Texas Instruments, ...)
  3. Apple direct careers HTML scraping (Apple)
  4. Amazon direct careers JSON API (Amazon)
  5. Small-Israel-company custom HTML scrapers (Innoviz, Valens, Altair)
  6. Phenom-hosted careers pages (Mobileye - currently 403s behind
     CloudFront but kept in case bot detection is relaxed)
  7. Eightfold AI-hosted careers pages (Qualcomm - currently 403s,
     kept for the same reason)
  8. LinkedIn guest API for many companies at once

Filters for relevance, deduplicates against SQLite store,
and sends Telegram notifications for new matches.

Dedup note: the dedup hash uses (company, url, title). This means the
same job appearing on a company's direct careers site AND on LinkedIn
will be notified twice (different URLs -> different hashes). That's
intentional - we'd rather get a duplicate ping than miss a genuinely
distinct opening that happens to share a title with another posting,
which is a real scenario for student/intern roles.
"""
import sys
import traceback

from config import COMPANIES, MAX_JOBS_PER_RUN
from filters import is_relevant
from storage import init_db, is_seen, mark_seen, make_hash, count_seen
from notifier import send_job, send_status

from scrapers.workday import fetch_workday
from scrapers.oracle_hcm import fetch_oracle_hcm
from scrapers.apple import fetch_apple
from scrapers.amazon import fetch_amazon
from scrapers.innoviz import fetch_innoviz
from scrapers.valens import fetch_valens
from scrapers.altair import fetch_altair
from scrapers.phenom import fetch_phenom
from scrapers.eightfold import fetch_eightfold
from scrapers.linkedin_scraper import fetch_linkedin_all


def fetch_company(name, platform, platform_id):
    if platform == "workday":
        return fetch_workday(name, platform_id)
    if platform == "oracle_hcm":
        return fetch_oracle_hcm(name, platform_id)
    if platform == "apple_direct":
        return fetch_apple(name)
    if platform == "amazon_direct":
        return fetch_amazon(name)
    if platform == "innoviz_direct":
        return fetch_innoviz(name)
    if platform == "valens_direct":
        return fetch_valens(name)
    if platform == "altair_direct":
        return fetch_altair(name)
    if platform == "phenom":
        return fetch_phenom(name, platform_id)
    if platform == "eightfold":
        return fetch_eightfold(name, platform_id)
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

    # ----- Per-company scrapers -----
    for name, platform, platform_id in COMPANIES:
        print(f"\n=== {name} ({platform}) ===")
        try:
            jobs = fetch_company(name, platform, platform_id)
        except Exception as e:
            print(f"[{name}] crashed: {e}")
            traceback.print_exc()
            errors.append(f"{name}: {e}")
            continue
        notified += _process_jobs(name, jobs, notified)
        total_fetched += len(jobs)

    # ----- LinkedIn (all configured companies) -----
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
            url = j.get("url", "")
            print(f"    {marker} [{posted}] {j.get('title', '?')} @ {j.get('company', '?')} - {j.get('location', '?')}")
            print(f"        {url}")

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
