# job-hunter-bot

A scheduled bot that watches semiconductor / hardware company careers pages for student and intern roles in Israel and pings a Telegram channel when relevant new postings appear.

Built specifically for an electrical engineering student looking for chip design, verification, analog, or board design roles, but the patterns generalize.

## What it does

Every 15 minutes, a GitHub Actions workflow runs `main.py`, which:

1. Fetches all currently-posted jobs from a list of companies' careers sites (NVIDIA, Intel, Apple, Amazon, Texas Instruments, and so on — see `docs/SCRAPERS.md` for the full list)
2. Filters them down to roles that are
   - in Israel,
   - student-level (title contains "student" / "intern" / "internship" / Hebrew equivalents), and
   - in the right field (chip design / verification / analog / board / firmware / etc.)
3. Skips anything already seen in past runs (deduplicated in a SQLite file checked into the repo)
4. Sends new matches to a Telegram group via a bot

The same job listing site is checked from multiple angles where possible — e.g. Apple is scraped both directly from `jobs.apple.com` and via LinkedIn — because no single source has complete coverage. The dedup avoids most duplicate notifications without erasing genuinely-distinct same-titled openings (a real scenario for student roles).

## Status

Healthy as of writing. Scraping ~3,700 job listings per run across all sources, surfacing 2–10 student/intern matches in any typical week.

See `docs/SCRAPERS.md` for the per-company status table (which sources work, which are blocked, why).

## Setup

This repo is private. To run a fresh deployment:

1. Create a Telegram bot via @BotFather and get the bot token
2. Create a Telegram group, add the bot, get the chat ID
3. In repo Settings → Secrets and variables → Actions, add:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
4. The workflow at `.github/workflows/run.yml` (or whatever it's named) handles the rest

## Documentation

- **`docs/DESIGN.md`** — architecture, dataflow, design choices and trade-offs
- **`docs/SCRAPERS.md`** — per-company reference: which platform, current status, how to add new ones
- **`docs/OPERATIONS.md`** — running, debugging, tuning filters, common errors

## Key files

```
main.py                  # Orchestrator: loops scrapers, dedupes, notifies
config.py                # COMPANIES list, LinkedIn list, filter keywords
filters.py               # is_relevant() — student-level + field check
storage.py               # SQLite seen-jobs DB
notifier.py              # Telegram sender
scrapers/
  workday.py             # Generic Workday scraper (NVIDIA, Intel, ...)
  oracle_hcm.py          # Generic Oracle Recruiting Cloud (TI)
  apple.py               # Apple-specific HTML scraper
  amazon.py              # Amazon-specific JSON API
  innoviz.py             # Innoviz HTML scraper
  valens.py              # Valens HTML scraper
  altair.py              # Altair Semiconductor HTML scraper
  phenom.py              # Generic Phenom (Mobileye — currently 403s)
  eightfold.py           # Generic Eightfold (Qualcomm — currently 403s)
  linkedin_scraper.py    # LinkedIn guest API for many companies
seen_jobs.db             # SQLite file checked in, tracks notified jobs
```
