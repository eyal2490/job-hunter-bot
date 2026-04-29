# Scrapers — job-hunter-bot

Per-source reference: which platform each company sits on, current status, known issues, and how to add new ones.

## Sources at a glance

| Company             | Platform     | File                       | Status     |
|---------------------|--------------|----------------------------|------------|
| NVIDIA              | Workday      | `scrapers/workday.py`      | ✅ working |
| Intel               | Workday      | `scrapers/workday.py`      | ✅ working |
| Marvell             | Workday      | `scrapers/workday.py`      | ✅ working |
| Broadcom            | Workday      | `scrapers/workday.py`      | ✅ working |
| Samsung             | Workday      | `scrapers/workday.py`      | ✅ working |
| Motorola            | Workday      | `scrapers/workday.py`      | ✅ working |
| Texas Instruments   | Oracle HCM   | `scrapers/oracle_hcm.py`   | ✅ working |
| Apple               | custom HTML  | `scrapers/apple.py`        | ✅ working |
| Amazon              | custom JSON  | `scrapers/amazon.py`       | ✅ working |
| Innoviz             | custom HTML  | `scrapers/innoviz.py`      | ✅ working |
| Valens              | custom HTML  | `scrapers/valens.py`       | ✅ working |
| Altair Semiconductor| custom HTML  | `scrapers/altair.py`       | ✅ working |
| Mobileye            | Phenom       | `scrapers/phenom.py`       | ⚠️ 403 (CloudFront) |
| Qualcomm            | Eightfold    | `scrapers/eightfold.py`    | ⚠️ 403 (PCSX) |
| Google              | (none)       | —                          | ❌ removed (JS-only careers site) |
| 28 LinkedIn cos     | LinkedIn API | `scrapers/linkedin_scraper.py` | ✅ working |

## Platform notes

### Workday

Generic scraper at `scrapers/workday.py`. Adding a new Workday-based company is a one-line config change — no code change needed. The platform_id requires three fields:

```python
{"tenant": "<tenant>", "site": "<site>", "host": "<host>"}
```

To find these, visit the company's Workday careers URL. If it looks like:

```
https://acme.wd1.myworkdayjobs.com/en-US/AcmeExternal
                  ↓                            ↓
              host                            site
```

then `tenant` is the leftmost subdomain segment (`acme`).

The scraper paginates through up to 500 jobs newest-first. Workday tenants typically host 400–2000 jobs total but only a few dozen in Israel; fetching newest-first avoids needing to filter on the server.

### Oracle Recruiting Cloud HCM

Generic scraper at `scrapers/oracle_hcm.py`. Texas Instruments uses this, and adding others is a one-line config change. Required platform_id:

```python
{"host": "<oracle pod host>", "site": "<site code>"}
```

The pod host is what shows in the URL when you click "Search Jobs" from the company's marketing-page careers link — it's hosted on Oracle infrastructure (`*.fa.us2.oraclecloud.com` etc.), not the company domain. The site code is usually `CX` but verify in the URL.

A few non-obvious requirements baked into this scraper that took several rounds to get right:

- The `finder` query parameter format is `findReqs;param=val,param=val,...` — semicolon between the finder name and the first param, commas between subsequent params. Comma everywhere fails with a 400.
- `expand=requisitionList` is required. Without it, the response includes the metadata wrapper but the actual job rows are empty.
- Pagination should use `TotalJobsCount` (which Oracle puts on the wrapper) to decide when to stop. There's a `hasMore` field on the outer response that means something different and isn't reliable for ending pagination.

### Apple

Custom HTML scraper at `scrapers/apple.py`. Apple's careers site at `jobs.apple.com` is server-side rendered with all job cards in the HTML — no JavaScript needed. We use the `?location=israel-ISR` URL parameter so the Israel filter is applied at fetch time, not after.

Pagination via `?page=N` (1-indexed). Stops when a page returns no cards (Apple doesn't 404 past the last page).

### Amazon

Custom JSON scraper at `scrapers/amazon.py`. Amazon's careers site has a public JSON endpoint at `amazon.jobs/en/search.json` with the same query parameters as the user-facing search page. Use `country=ISR` for the Israel filter.

Returns up to 100 results per page; we paginate through all results sorted newest-first.

### Innoviz, Valens, Altair Semiconductor

Each has its own HTML scraper because their site structures don't share enough to make a generic scraper worthwhile. All three are server-side rendered.

- **Innoviz** (`innoviz.tech/careers-3`) — job links match `/careers-3/co/<country>/<id>/<slug>/all`. ~14 jobs total.
- **Valens** (`valens.com/positions/`) — job links match `/position/<slug>/`. ~5 jobs total, all Hod HaSharon.
- **Altair** (`altairsemi.com/careers/`) — job links match `/careers/<id>` where id is a `XX.XXX` hex pattern. ~6 jobs total.

These small-company HTML scrapers are the most fragile parts of the bot. If a site redesign happens, the scraper will return 0 jobs (no crash). Spot it via `[Company] fetched 0 jobs total` in the logs.

### Phenom (Mobileye)

Generic scraper at `scrapers/phenom.py`. Phenom hosts careers sites at the company's own domain (e.g. `careers.mobileye.com`) but typically behind CloudFront. CloudFront's bot detection rejects our requests with a 403, even with full browser-mimicking headers and a warmup GET.

The scraper is kept in the config because (a) the failure mode is harmless — it logs the 403 and returns 0 jobs — and (b) if CloudFront's rules ever relax it'll just start working. LinkedIn covers Mobileye in the meantime.

To bypass the 403 reliably, the realistic options are a headless browser (Playwright/Selenium) or a paid scraping API. Both add infrastructure complexity that isn't worth it for one source.

### Eightfold (Qualcomm)

Generic scraper at `scrapers/eightfold.py`. Eightfold's standard public endpoint at `<tenant>.eightfold.ai/api/apply/v2/jobs` works for many companies but Qualcomm's deployment returns:

```
403 {"message": "Not authorized for PCSX"}
```

That's a tenant-specific access control we haven't bypassed. Same status as Mobileye: kept in the config, harmless when blocked, LinkedIn covers Qualcomm in the meantime.

### Google (removed)

We tried scraping `google.com/about/careers/applications/jobs/results` directly. The page renders fine for Google's own crawlers but returns a JavaScript-only shell to plain HTTP requests — there are no job cards in the raw HTML.

Bypassing this reliably needs a headless browser. Removed from `COMPANIES` in `config.py`. Google is covered by LinkedIn.

### LinkedIn

`scrapers/linkedin_scraper.py` (existing, not described in detail here) hits LinkedIn's guest API for the 28 companies in `LINKEDIN_COMPANIES`. The guest API returns short job cards without authentication. It's the most consistent breadth-coverage tool in the bot — if a direct scraper for any company breaks, LinkedIn usually still has it.

LinkedIn occasionally tightens the guest API. If `[LinkedIn] crashed` shows up in the logs, that's the canary.

## Adding a new company

### Easy case: company is on a platform we already support

Just add a line to `COMPANIES` in `config.py`. For example, adding another Workday-hosted company:

```python
("Some Other Co", "workday", {"tenant": "someotherco", "site": "External", "host": "someotherco.wd5.myworkdayjobs.com"}),
```

No other code changes needed. Push, run, see it in the next log.

### Medium case: new shared platform (e.g. a Greenhouse-based company)

1. Write `scrapers/<platform>.py` that exposes `fetch_<platform>(company_name, platform_id)` and returns the standard job dict list
2. Add an `import` and a dispatch branch in `main.py`'s `fetch_company()`
3. Add the company to `COMPANIES` in `config.py` with the new platform name

Use one of the existing generic scrapers (`workday.py`, `oracle_hcm.py`, `phenom.py`) as a template.

### Hard case: company has a fully custom careers site

1. Open the careers page in a browser, view source, work out where the job data lives
2. If it's in the HTML → copy `scrapers/innoviz.py` (or apple.py, valens.py, altair.py) as a starting template
3. If it's a JSON API call → check Network tab in browser dev tools for the request; copy `scrapers/amazon.py` as a template
4. If it's JavaScript-rendered with no API → consider whether it's worth the trouble. LinkedIn coverage is usually enough.
5. Wire it in: `from scrapers.<company> import fetch_<company>`, dispatch branch in `main.py`, entry in `COMPANIES`

## Removing or disabling a company

Just delete the line from `COMPANIES` in `config.py`. The scraper file can stay (it's an orphan but harmless) or be deleted from the repo.

If you want to keep the company in monitoring but stop the direct scraper (e.g. it's flapping), delete from `COMPANIES` and ensure it's in `LINKEDIN_COMPANIES`.
