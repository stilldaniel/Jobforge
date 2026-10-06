# Guide for AI coding agents

This is the single source of truth for AI-assisted development on
JobForge (Claude Code, Cursor, and other coding agents). Read it before
changing code. `CLAUDE.md` and `AGENTS.md` at the repo root point here.

**Keep it current.** When a change makes anything here wrong (a command,
a threshold, a file, a rule), update this file in the same commit.

---

## 1. What JobForge is

A **personal job-search tool** for one user, running on their Windows
laptop. Every 15 minutes it pulls jobs from job boards, scores each new
job 0–100 against the user's career profile, and emails strong matches.
There is no login: the app acts as one development user (ID 5). It may
become a multi-user product later, so don't make choices that rule that
out, but don't build multi-user features unless asked.

The user is based in **Lagos, Nigeria**, which shapes several rules:
remote-job eligibility matters a lot, and country-specific boards (e.g.
Adzuna UK) are useless to them.

## 2. Repository map

```
apps/
  api/                         FastAPI backend (Python 3.14, venv at apps/api/.venv)
    app/
      main.py                  App, CORS (localhost:3000 only), logging, scheduler lifespan
      api/                     Routers, one per resource
      models/                  SQLAlchemy 2 models
      schemas/                 Pydantic v2 schemas (model_config = ConfigDict(...))
      job_sources/             One module per job platform + base.py, common.py, registry.py
      services/                Business logic (see section 5)
      db/database.py           Engine, SessionLocal, get_db
    migrations/versions/       Alembic migrations (linear chain)
    tests/                     pytest, in-memory SQLite
    run_server.py              Background launcher (Task Scheduler)
    backup_database.py         Nightly pg_dump (Task Scheduler)
    .env                       SECRETS - never print, never commit
  web/                         Next.js 16 frontend (React 19, TypeScript, CSS modules)
    app/                       Routes: /, /jobs, /jobs/[id], /saved-jobs, /applications,
                               /notifications, /profile, /settings
    components/                layout/AppShell, dashboard/*
    lib/api/                   One client module per API resource, built on client.ts
    lib/config.ts              DEV_USER_ID, HIGH_MATCH_SCORE
    lib/format.ts              formatSalary, formatSource
    types/api.ts               Mirrors the API's Pydantic response models
    run_web.py                 Background launcher (Task Scheduler)
packages/                      Shared eslint/typescript config, unused @repo/ui
docs/                          Architecture, API, database, product docs
```

Ignore: `__pycache__/`, `.next/`, `node_modules/`, `apps/*/logs/`.
Empty folders such as `app/(auth)` and `components/profile` are the
user's placeholders; leave them.

## 3. Commands

All commands are for **Windows** (PowerShell or Git Bash).

| Task | Command (from) |
| --- | --- |
| Backend tests | `pytest` (apps/api, venv active); run with `DATABASE_URL=sqlite://` if no `.env` |
| Backend dev server | `uvicorn app.main:app --reload` (apps/api) |
| Migrations | `alembic upgrade head` / `alembic revision --autogenerate -m "..."` (apps/api) |
| Frontend dev server | `pnpm --filter web dev` (repo root) |
| Frontend type check | `npx tsc --noEmit` (apps/web) |
| Frontend lint | `npx eslint --max-warnings 0 app components lib types` (apps/web) |

**The app normally runs in the background** through three Task Scheduler
tasks: **JobForge API** (port 8000), **JobForge Web** (port 3000) and
**JobForge Backup** (02:00 nightly). See the README section "Running in
the background on Windows". Before starting a dev server, stop the
matching task (`Stop-ScheduledTask -TaskName "JobForge API"`), and start
it again afterwards. Next.js also allows only one dev server per folder.

## 4. How it works

```
Scheduler (APScheduler, in the API process, UTC)
  every 15 min  -> job_monitor.monitor_jobs
                     build_search_criteria(profiles)        search_criteria.py
                     for each due source: fetch_jobs()      job_sources/*
                       drop irrelevant jobs (feeds only)    search_criteria.is_relevant
                       ingest_jobs()                        job_ingestion.py
                     score new jobs x profiles              matching.calculate_match_score
                     create_notification_for_match()       notification_service.py
                 -> digest_service.process_immediate_notifications
  every 15 min  -> digest_service.process_digest_notifications(only_due=True)
```

Details: [system-design.md](system-design.md), [backend.md](backend.md),
[frontend.md](frontend.md), [../api/endpoints.md](../api/endpoints.md),
[../database/schema.md](../database/schema.md).

## 5. Domain rules

These are deliberate product decisions. Don't change them without being
asked.

### Scoring (`services/matching.py`)

- Factors and weights: title 25, skills 30, experience 15, work type 10,
  location 10. **Only factors the job states are scored**, then scaled to
  100. Unknown information returns `None` points and is left out; it must
  never count as 0.
- **Salary never affects the score or eligibility.** It's shown in the
  reasons only, compared in the profile's `salary_currency` (monthly
  preferences converted to yearly; no exchange rates).
- **Cap at 49** (hard ineligible, reason "Job has an eligibility
  mismatch"): the candidate's location isn't accepted, or the role is
  unpaid or volunteer (`_is_unpaid_role`).
- **Cap at 89:** remote with unstated geography, or no recognisable
  skills.
- Profile work type values are `remote`, `hybrid`, `onsite`; job sources
  write `on-site`. Compare without hyphens or spaces.

### Notifications

| Constant | Value | Where |
| --- | --- | --- |
| `DEFAULT_MIN_NOTIFICATION_SCORE` | 60 (env `NOTIFICATION_MIN_SCORE`) | `services/notification_service.py` |
| `IMMEDIATE_NOTIFICATION_SCORE` | 89 | `services/notification_service.py` |
| `HIGH_MATCH_SCORE` | 89, **must equal the line above** | `apps/web/lib/config.ts` |

- A notification is created only if score >= 60 **and**
  `has_field_fit(profile, job)` (a specific title word or a skill
  overlaps; generic words like "developer" don't count).
- 89+ means `immediate`, otherwise `digest`. All of a user's immediate
  notifications from one cycle go in **one email**.
- Preferences on `users`: `job_alerts_enabled` (master switch),
  `email_notifications_enabled`, `high_match_alerts_enabled` (off means
  89+ goes to the digest), `digest_notifications_enabled`. Email
  preferences are checked **at send time**.
- Status: `pending`, `sent`, `failed` (after `NOTIFICATION_MAX_ATTEMPTS`),
  `skipped` (not emailed because of preferences; never retried).
- Each job in an email links to its page in the app (`APP_BASE_URL`,
  default `http://localhost:3000`) and to the original listing,
  credited to its platform.
- Digest: at `DIGEST_HOUR:DIGEST_MINUTE` in **each user's timezone**, at
  most once a day, tracked by `users.last_digest_at`. Profile edits
  re-score matches but **never** send notifications.

### Jobs and sources

- `fingerprint` (unique) identifies one listing: the platform's
  `external_id` when set, otherwise title + company + URL. Set
  `external_id` for any platform whose URLs change between requests
  (Adzuna adds a tracking code; forgetting this caused 1,600 duplicates).
- `dedupe_key` (normalised title + company) skips the same job arriving
  from a *different* platform.
- Descriptions are stored as **plain text with one paragraph per line**;
  the frontend splits on `\n`. Use `common.html_to_text`.
- Imported salaries are yearly with a currency (`common.normalize_salary`).
- Enabled sources come from `JOB_SOURCES` in `.env`. Currently:
  remotive, remoteok, arbeitnow, jobicy, himalayas, weworkremotely.
  Adzuna is implemented but disabled (it doesn't cover Nigeria, and its
  UK pages are blocked outside the UK). `mock` is test data only.
- Platform terms: credit the platform (`formatSource`) and link to the
  original listing. **Remotive allows at most 4 requests a day**
  (`min_interval_minutes = 360`) and forbids showing its jobs behind a
  sign-up without its paid API.

## 6. Rules and gotchas

**Data and secrets**

- `apps/api/.env` holds the database password and API keys. Never print
  it, log it, or commit it. Read single variables only when needed.
- The PostgreSQL database is the user's **real data**. Before any
  migration or destructive operation, take a backup:
  `python backup_database.py` (apps/api). Ask the user before deleting
  rows.

**Backend**

- The scheduler must run in **exactly one process**. Never add workers
  or a second scheduler.
- New migrations go after the current head (`alembic heads`). Give new
  non-null columns a `server_default`. The older migrations use
  Postgres-only SQL, so the full chain can't run on SQLite. Test a new
  migration on its own against a SQLite table (`alembic.operations` with
  `MigrationContext`).
- User-facing validation errors the UI must show: raise
  `HTTPException(400, detail="...")` with a string. The frontend client
  only displays string `detail`s, not Pydantic's 422 lists.
- Timezones must be IANA names (`Africa/Lagos`); `users.py` validates them.
- Logging: use `logging.getLogger(__name__)`. `main.py` configures
  `LOG_LEVEL` (default INFO). Don't use `print` in app code.

**Tests**

- In-memory SQLite (`tests/conftest.py` `db` fixture). Never call real
  job platforms or send email.
- Mock HTTP with `patch("app.job_sources.common.httpx.get", ...)`
  (Adzuna: `app.job_sources.adzuna.httpx.get`).
- Replace email with a fake class via
  `monkeypatch.setattr(digest_service, "EmailDelivery", Fake)`.
- API tests: override `get_db` and use `TestClient(app)` **without** a
  `with` block, so the scheduler doesn't start.

**Frontend**

- Pages are `"use client"` components that call `lib/api/*`. Add the
  matching type to `types/api.ts` whenever an API response changes.
- The browser reaches the API only through the `/api/*` proxy in
  `next.config.js`. Never point frontend code at `localhost:8000`
  directly.
- The user opens the app from their phone over Tailscale
  (`tailscale serve` shares port 3000 as
  `https://desktop-8o15rqo.tail895113.ts.net`; `APP_BASE_URL` points
  there). Keep both servers bound to `127.0.0.1`: binding to `0.0.0.0`
  would expose the unauthenticated API on any Wi-Fi network.
- Show salaries with `formatSalary` and sources with `formatSource`; never
  hardcode `$` or a score threshold.
- **Demo mode** (`NEXT_PUBLIC_DEMO_MODE=true`, the public portfolio demo
  on Vercel): `lib/api/client.ts` sends every request to
  `lib/demo/api.ts`, which serves `lib/demo/data.ts`. When you add or
  change an API call the frontend uses, add or update its demo route
  too, or that page breaks in the demo. Keep demo companies invented and
  demo scores consistent with the real matching rules. Build the demo
  with `NEXT_DIST_DIR=.next-demo` locally so it doesn't replace the
  laptop's real build in `.next`.
- Lint runs with `--max-warnings 0`. Escape apostrophes in JSX
  (`&apos;`).

**Environment**

- Windows. Run commands in PowerShell, or use Git Bash with Windows-style
  paths in quotes. Files use LF line endings.
- When generating files with scripts, watch backslash escaping: `\b`,
  `\t`, `\a` inside Python strings have produced invisible control
  characters in this repo before. Prefer writing files directly.

## 7. Code style

- **Python:** match the surrounding code: multi-line calls with one
  argument per line, `# ====` section banners in long modules, type
  hints, and docstrings that explain *why*. Pydantic v2 style.
- **TypeScript:** one CSS module per page or component, `lucide-react`
  icons, the purple palette already in the CSS (`#7b34a3`, `#6d28d9`).
- **Commits:** Conventional Commits (`feat:`, `fix:`, `chore:`,
  `docs:`), with a body explaining the change.

## 8. Recipes

**Add a job source**

1. `app/job_sources/<name>.py`: a class extending `JobSource` that
   returns `DiscoveredJob`s, built with the helpers in `common.py`.
2. Set `filter_by_relevance`, `min_interval_minutes`, use
   `self.search_queries` if the platform can search, and `external_id`
   if its URLs aren't stable.
3. Register it in `registry.py`; add tests with mocked HTTP; add it to
   `formatSource` in `apps/web/lib/format.ts`, to `.env.example`, and to
   the docs.

**Add an API endpoint**

Schema (`schemas/`) → router function (`api/`, registered in `main.py`)
→ tests → client function (`apps/web/lib/api/`) → type
(`types/api.ts`) → `docs/api/endpoints.md`.

**Add a database column**

Model → migration with `server_default` if non-null → schema → frontend
type → `docs/database/schema.md` → back up, then `alembic upgrade head`.

**Change a score threshold**

Update the constant, its frontend twin if there is one (section 5), the
tests that pin it, and the docs (README, system-design, this file).

## 9. Definition of done

- [ ] `pytest` passes (160+ tests)
- [ ] `npx tsc --noEmit` and `npx eslint --max-warnings 0 ...` pass if
      the frontend changed
- [ ] New migrations tested on their own; applied only after a backup
- [ ] Docs updated: endpoints, schema, README, and this file
- [ ] A Conventional Commit message, given to the user (the user commits)

## 10. Known gaps

See [../product/roadmap.md](../product/roadmap.md). In short: no
authentication, nothing hosted (it runs on the laptop),
`POST /job-discovery/run` always imports sample jobs, and
`app/test-api` is a leftover development page.
