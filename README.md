# Job Hunter Bot

Auto-monitors EE-relevant student/junior job postings from selected hi-tech companies' careers pages and sends new matches to Telegram.

## How it works

1. GitHub Actions runs `main.py` every 15 minutes.
2. The script queries each company's careers API (NVIDIA, Apple, Intel, Mobileye, Qualcomm, ARM).
3. Each job is filtered:
   - Must be in Israel
   - Must contain at least one positive keyword (student/intern/hardware/FPGA/etc.)
   - Must NOT contain rejection signals (senior/manager/5+ years/etc.)
4. New matches (not seen before) are sent to a Telegram bot, which forwards them to you.
5. The list of seen jobs is committed back to the repo so the next run remembers.

## Setup

### 1. Configure Telegram

In GitHub: **Settings → Secrets and variables → Actions → New repository secret**

Add two secrets:

- `TELEGRAM_BOT_TOKEN` — the token from @BotFather
- `TELEGRAM_CHAT_ID` — your numeric Telegram ID (from @userinfobot)

### 2. First run

Go to **Actions → Job Hunter → Run workflow** to trigger manually. Watch the logs.
The first run notifies on every match (up to 20). Subsequent runs only on truly new postings.

## Customizing

All tuning is in `config.py`:

- `COMPANIES` — add/remove companies
- `POSITIVE_KEYWORDS` — what jobs to *consider* relevant
- `NEGATIVE_TITLE_KEYWORDS` — what to reject outright
- `MAX_JOBS_PER_RUN` — safety cap on Telegram messages per run

## Files

```
config.py            # all settings & filter rules
filters.py           # relevance logic
storage.py           # SQLite dedup
notifier.py          # Telegram sender
main.py              # orchestrator
scrapers/
  workday.py         # NVIDIA, Apple, Qualcomm, ARM
  intel.py           # Intel custom API
  mobileye.py        # Mobileye via Comeet
.github/workflows/
  job-hunter.yml     # runs every 15 min
```

## When something breaks

If a company's careers site changes its API, the run summary will show 0 jobs for that company and you'll get a Telegram alert. The fix is usually 1-2 lines in the relevant scraper file.
