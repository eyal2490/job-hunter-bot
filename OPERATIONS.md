# Operations — job-hunter-bot

The "how do I actually run / debug / extend this without breaking anything" guide.

## Running

The bot runs automatically every 15 minutes via GitHub Actions. To trigger a run manually:

1. Go to the **Actions** tab in the GitHub repo
2. Click the workflow on the left side (probably "Run job hunter" or similar)
3. Click **Run workflow** in the upper right
4. Click the green **Run workflow** button

The run takes about 2.5 minutes. Watch live by clicking the in-progress run in the Actions list.

## Reading the logs

The output of every scraper is the line `[Company] fetched N jobs total`. If `N` is roughly what you'd expect, the scraper works. If it's 0 or much lower than expected, something's wrong.

The block below the fetch line shows the diagnostic:

```
[Texas Instruments] 11 jobs in Israel:
    ✓ [2026-04-22] RF System Validation intern @ Texas Instruments - Ra'anana, Israel
    ✗ [2026-04-16] AVV Engineering Intern @ Texas Instruments - Israel
    ✗ [2026-04-15] Experienced Design Verification Engineer @ Texas Instruments - Ra'anana, Israel
    ...
```

`✓` = passed the filter, will be sent (if not already seen). `✗` = filtered out. Sample is capped at 10 per source.

The diagnostic only lists jobs whose `location` string contains "Israel". Some scrapers (Apple, Workday for some companies) use locations like "Herzliya" or "Yokneam" without "Israel" — these jobs still pass through to the filter and notification path correctly, they just don't appear in the diagnostic. Trust the `+ sent: ...` line at the bottom of each section as the source of truth on what was notified.

## When things go wrong

### "ModuleNotFoundError: No module named 'scrapers.X'"

The file isn't in the repo, or the filename has wrong casing.

- Linux is case-sensitive on filenames. `Apple.py` and `apple.py` are different files.
- The file must be inside `scrapers/`, not the repo root.
- Double-check the filename has no extra suffix like `.py.txt` (some browsers add this on download).

### A scraper returns 0 jobs when the site clearly has openings

Most likely the site changed structure. Check the scraper's CSS selectors / regexes against the current page source.

For HTML scrapers (Apple, Innoviz, Valens, Altair, Google attempt): open the company's careers page, view source, search for a job title you can see. Check whether the link to the job, the location field, etc. still match what the scraper expects.

For JSON API scrapers (Workday, Oracle HCM, Amazon, Eightfold, Phenom): open browser dev tools → Network tab, refresh the careers page, find the API request, compare its URL parameters and response shape against what the scraper sends and parses.

### A scraper returns a 403 / 401

CDN or anti-bot system. Usually no fix without a headless browser or a paid scraping API. See `docs/SCRAPERS.md` for known cases (Mobileye, Qualcomm).

### Bot stops sending Telegram messages but logs say "+ sent: ..."

Check the Telegram bot token and chat ID secrets in repo Settings. The sender's `send_job` function returns `True/False` — if it logs `! telegram failed: ...`, that's the symptom; the secrets are likely wrong or expired.

### `seen_jobs.db` gets out of control

It grows unbounded — every notified job gets a row. After months of operation, this might accumulate thousands of rows. There's no cleanup currently. If it ever becomes a problem, `storage.py` is the place to add a TTL or row cap; an "older than 90 days" cleanup is the right shape.

## Tuning the filter

Filter keywords live in `config.py`. The four lists:

- **`STUDENT_LEVEL_TITLE_KEYWORDS`** — TIER 1, must be in title
- **`FIELD_RELEVANCE_KEYWORDS`** — TIER 2, must be in title or description
- **`NEGATIVE_TITLE_KEYWORDS`** — exclusions in title
- **`NEGATIVE_DESCRIPTION_PHRASES`** — exclusions in description

A few practical scenarios:

### "I'm getting too many irrelevant pings"

Look at the recent Telegram messages. Pick the worst offender. What keyword caused it to match? Tighten by either adding to the negative lists or removing an over-broad TIER 2 keyword.

### "I'm clearly missing roles I'd want"

Open the careers diagnostic in a recent log. Find the role you wish had been notified. Look at why it failed:

- Title doesn't have "student" / "intern" → if it's a different title format, add it to `STUDENT_LEVEL_TITLE_KEYWORDS` (e.g. some Israeli companies post as "התמחות" or "Working Student")
- Title doesn't mention the field → add the field's keyword to `FIELD_RELEVANCE_KEYWORDS` if it's missing (e.g. `"AVV"` for analog validation, `"DFT"` for design-for-test)
- Title has a negative keyword that shouldn't apply → remove it from the negatives, or make it more specific (e.g. `"senior"` is general but might be tightened to `"senior engineer"`)

### "A specific company is too noisy"

The simplest tightener is removing it from `LINKEDIN_COMPANIES` and/or `COMPANIES`, but that loses coverage entirely. A middle ground: add company-specific negative keywords. The current filter doesn't support this; if it becomes important, `filters.py` would grow a per-company branch — small change.

## Tuning the location list

`LOCATION_KEYWORDS` in `config.py` is used for matching when a job's location field doesn't contain the literal string "Israel" (e.g. just "Herzliya"). If you're seeing real Israel jobs not being recognized, add the missing city to that list.

The diagnostic block in `main.py` (`if "israel" in (j.get("location") ...)`) currently doesn't use this list — it only looks for the literal string "Israel". This is cosmetic only and was deferred. If you want the diagnostic to be more useful, the change is in `_process_jobs` in `main.py` — replace the substring check with a check against `LOCATION_KEYWORDS`.

## Schedule changes

The cron schedule lives in `.github/workflows/<workflow>.yml`. Currently every 15 minutes:

```yaml
on:
  schedule:
    - cron: '*/15 * * * *'
```

If you want it less frequent (cheaper, slower to surface new roles), edit that line. GitHub Actions has a free quota for public repos and a generous one for private — every-15-minutes for a job that takes 2.5 minutes is about 240 minutes/day, well within free tier.

## What to monitor

In daily use, check:

1. **Telegram channel for new pings.** This is the actual product. If new student/intern roles in Israel are being posted at relevant companies and you're not getting pings, something's wrong.
2. **Latest GitHub Actions run for ⚠ status messages.** If `main.py` catches scraper errors, it sends a `⚠️ Job hunter run had issues` Telegram status. That tells you a scraper is broken without you needing to read logs.
3. **Per-source job counts in logs over time.** If a count drops to 0 unexpectedly, the source structure changed.

You don't need to read every log. The bot is designed to be self-reporting on failures.
