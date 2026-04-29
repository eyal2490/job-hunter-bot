# Design — job-hunter-bot

This document explains how the bot is structured and why. It's the place to look first when something doesn't behave the way you expect, or when you want to extend it without breaking what's already there.

## The problem

A student looking for a part-time chip-design role in Israel needs to check ~30 companies' careers pages for new postings. Doing this manually means either checking everything daily (tedious, missed openings between checks) or checking nothing reliably (missed openings, period). Most of these careers pages are also painful to filter — student/intern is buried among thousands of senior roles.

A bot solves this by watching everything continuously, applying a tight filter, and only pinging when something genuinely matches.

## High-level design

```
┌──────────────────────────────────────────────────────────────────┐
│                     GitHub Actions, every 15 min                 │
│                                                                  │
│   ┌────────────┐                                                 │
│   │  main.py   │                                                 │
│   └─────┬──────┘                                                 │
│         │                                                        │
│         ▼                                                        │
│   ┌─────────────────────┐    ┌──────────────────────────┐        │
│   │  for company in     │───▶│  scrapers/<platform>.py  │        │
│   │  COMPANIES:         │    │  returns list of dicts   │        │
│   │  call its scraper   │    └──────────────────────────┘        │
│   └─────┬───────────────┘                                        │
│         │                                                        │
│         ▼                                                        │
│   ┌─────────────────────┐                                        │
│   │  fetch_linkedin_all │  (one call, returns all 28 cos)        │
│   └─────┬───────────────┘                                        │
│         │                                                        │
│         ▼                                                        │
│   ┌────────────────────────────────────────┐                     │
│   │  for each job:                         │                     │
│   │    is_relevant?  no → skip             │                     │
│   │    seen before?  yes → skip            │                     │
│   │    else: mark seen, send to Telegram   │                     │
│   └────────────────────────────────────────┘                     │
└──────────────────────────────────────────────────────────────────┘
```

Three things to notice from this diagram:

1. **Scrapers know nothing about filtering or deduplication.** Their only job is to fetch and normalize.
2. **Scrapers know nothing about each other.** Each company's scraper can fail without taking the others down (`main.py` wraps each call in `try/except`).
3. **The orchestrator (`main.py`) doesn't know what platform a company uses.** It just dispatches based on a `platform` string from `config.py`.

That separation is the only design rule that really matters. As long as every new scraper returns the standard dict shape and slots into the dispatcher, everything works.

## The standard job dict

Every scraper, regardless of platform, returns a list of dicts with this shape:

```python
{
    "title":       "WiFi Firmware PHY Engineering Student",
    "location":    "Israel, Petah-Tikva",
    "company":     "Intel",
    "url":         "https://intel.wd1.myworkdayjobs.com/...",
    "description": "",                    # optional, can be ""
    "posted_on":   "Posted 8 Days Ago",   # raw string from source, format varies
}
```

Anything outside this shape is the scraper's internal business and shouldn't leak. If a source provides interesting metadata (department, work type, salary), it stays in the scraper unless the filter actually needs it.

## Configuration model

`config.py` is the only place that knows which companies to monitor. Each entry in `COMPANIES` is a 3-tuple:

```python
(display_name, platform, platform_id_dict)
```

- **display_name** — user-facing string, used in logs and Telegram messages
- **platform** — string like `"workday"`, `"oracle_hcm"`, `"apple_direct"`. `main.py` uses this to dispatch to the right scraper.
- **platform_id_dict** — platform-specific configuration (Workday tenant, Oracle host, etc.). Empty dict `{}` for one-off scrapers that don't need it.

Companies on shared platforms (multiple Workday tenants) share a generic scraper. Companies with custom sites get their own.

`LINKEDIN_COMPANIES` is a separate flat list of names — LinkedIn's guest API takes a company name and returns whatever's posted under that name. Companies in `COMPANIES` may also appear in `LINKEDIN_COMPANIES`; that's intentional (see "Cross-source coverage" below).

## Filter model

`filters.is_relevant(job)` returns `(bool, reason_string)`. A job is relevant if:

1. The **title** contains a TIER 1 student-level keyword (`student`, `intern`, `סטודנט`, etc.), AND
2. The **title** OR **description** contains a TIER 2 field keyword (`verification`, `chip design`, `analog`, etc.), AND
3. The title contains no NEGATIVE keyword (`senior`, `principal`, `phd`, etc.), AND
4. The description contains no NEGATIVE phrase (`5+ years of experience`, `phd required`, etc.)

Rules 1 and 2 are AND-joined: a "Student" role in marketing isn't a match, and a "Senior Verification Engineer" isn't a match either. Rules 3 and 4 are belt-and-braces: a junior verification role posted as "Junior Verification Engineer" is filtered by the negative match on "junior" — that's intentional, the SIL is looking for student-grade roles only.

Keywords live in `config.py` and are easy to tune. See `docs/OPERATIONS.md` for advice on tuning.

## Deduplication

`storage.py` is a thin wrapper over a single SQLite file (`seen_jobs.db`) checked into the repo. The DB has one table with one row per "seen" job, keyed by a hash of `(company, url, title)`.

The file is committed to git on each run by the GitHub Action so dedup state persists across runs. (Workflow detail: `.github/workflows/...yml` does the commit.)

### Why URL is in the dedup key

It's a deliberate choice that the same job appearing in two sources (e.g. Apple direct AND LinkedIn) gets two notifications — one per source — because each source has a different URL and therefore a different hash. The trade-off:

- **Pro:** if a company posts two genuinely different openings with the exact same title (different team, different supervisor), each notifies separately. This happens with student roles more often than you'd think.
- **Con:** popular roles that show up in multiple sources produce multiple Telegram pings.

The SIL's preference was the pro outweighs the con. If you ever want to flip it, change `make_hash(company, url, title)` to `make_hash(company, "", title)` in `main.py`'s `_process_jobs`.

## Cross-source coverage

Many companies are scraped both from a direct source (their own careers page) and via LinkedIn. This isn't redundancy — it's deliberate hedging:

- **LinkedIn** sometimes has roles that don't show up on the company site (LinkedIn-only postings, syndication lag).
- **The company site** sometimes has roles LinkedIn hasn't picked up yet (newest postings are often on the company site first).
- **Either source can break independently** — a careers-site redesign or a LinkedIn API change shouldn't take out coverage for that company.

## Source classification (current state)

Each direct scraper falls into one of three categories. See `docs/SCRAPERS.md` for the per-company table.

- **Working.** Returns jobs reliably. Most scrapers are here.
- **Blocked but harmless.** Hits the source, gets a 403 from a CDN/anti-bot layer, returns 0 jobs and moves on. Mobileye (CloudFront on Phenom) and Qualcomm (Eightfold's PCSX block) are here. Kept in the config because the failure mode is silent — if the block ever relaxes, it'll just start working again. LinkedIn covers them in the meantime.
- **Removed.** A direct scraper was tried and didn't work in a way worth keeping. Google was here briefly — its careers site returns a JavaScript-only shell to non-Google bots. Removed entirely; LinkedIn-only.

## Failure modes and resilience

`main.py` wraps each scraper in a `try/except` block. If a scraper crashes — exception, network timeout, malformed JSON — `main.py` logs it, appends to an `errors` list, and continues to the next company. At the end of the run, if any errors occurred, a single status message is sent to Telegram (`send_status`) summarizing them.

Specific recoverable conditions:

- **Network timeout / DNS failure** → caught by `try/except`, logged, scraper returns empty list
- **HTTP 4xx/5xx** → scraper logs the status code and bails (returns whatever it had so far)
- **Non-JSON response when JSON expected** → logged, scraper returns empty list
- **Source structure changed (HTML scrapers)** → scraper returns 0 jobs but doesn't crash; you'll see "fetched 0 jobs" in logs and know to fix it

Scrapers individually never raise to the orchestrator. If they did, one bad source could take down the whole run.

## What's intentionally simple

A few places where a more sophisticated design was considered but rejected because the bot serves one user and runs free on GitHub Actions:

- **No retry logic.** If a source fails in this run, it'll be retried in the next run 15 minutes later. No point doing it in-process.
- **No caching.** Every run hits every source from scratch. Workday/etc. responses are cheap and the runs are infrequent.
- **No queue or worker pool.** Scrapers run sequentially. A single run completes in about 2.5 minutes — well under the 15-minute schedule interval.
- **No structured logging.** Plain `print()`. The logs go to GitHub Actions, which already has search/filter UI. Adding structured logging would be a maintenance burden for no real gain.
- **No tests.** The bot is small enough that running it is the test. Bugs surface as "fetched 0 jobs" or as Telegram silence; both are easy to spot.

## What's intentionally not simple

- **Scraper-per-platform is more code than scraper-per-company would be.** But it pays for itself the moment a second company joins the same platform — TI's scraper, for example, is a 5-line config addition rather than a new file.
- **Logging the raw "Israel jobs in this run" diagnostic to GitHub Actions output is more verbose than necessary.** But it's the single most valuable signal when something starts producing wrong results — you can see exactly which jobs the scraper saw, why each one passed or failed the filter, and whether the source structure changed.
