# Backend

FastAPI application in `apps/api`. See [system-design.md](system-design.md)
for how the pieces work together.

## Layout

```
app/
  main.py              App, CORS, logging, scheduler start/stop
  api/                 One router per resource (users, jobs, matches, ...)
  models/              SQLAlchemy models
  schemas/             Pydantic request/response models
  db/database.py       Engine, session factory, get_db dependency
  job_sources/         One module per job platform
  services/            Business logic
  scripts/             One-off maintenance scripts
migrations/            Alembic migrations
tests/                 pytest suite (in-memory SQLite)
```

## Services

| Module | Responsibility |
| --- | --- |
| `scheduler.py` | Registers the monitoring and digest jobs |
| `job_monitor.py` | One monitoring cycle: fetch, filter, ingest, match, notify |
| `job_ingestion.py` | Stores discovered jobs; updates repeats, skips cross-platform duplicates |
| `job_fingerprint.py` | Listing fingerprint and cross-platform dedupe key |
| `job_requirements.py` | Extracts required skills and years of experience from job text |
| `search_criteria.py` | Search queries and relevance keywords from profiles; the field-fit check |
| `matching.py` | The 0–100 score and its reasons |
| `match_jobs.py` | Re-scores every job for one user (used on profile save) |
| `notification_service.py` | Creates notifications from matches (score, field fit, preferences) |
| `digest_service.py` | Sends instant and digest emails; retries; per-timezone digest timing |
| `email_delivery.py` | Resend integration and email templates |

## Adding a job source

1. Create `app/job_sources/<name>.py` with a class extending `JobSource`
   whose `fetch_jobs()` returns `DiscoveredJob`s. Use the helpers in
   `job_sources/common.py` for HTTP, HTML-to-text, dates and salaries.
2. Set the class options:
   - `filter_by_relevance = True` if the platform returns everything
     rather than search results.
   - `min_interval_minutes` if the platform limits how often it may be
     called.
   - Read `self.search_queries` if the platform has a search API.
   - Set `external_id` on each job if the platform's URLs change between
     requests.
3. Register it in `job_sources/registry.py` and add tests that mock
   `httpx.get`.

## Migrations

```bash
alembic revision --autogenerate -m "describe the change"
alembic upgrade head
```

Give new non-nullable columns a `server_default` so the migration works on
tables that already have rows.

## Tests

```bash
pytest
```

Tests use an in-memory SQLite database (`tests/conftest.py`), mock all
HTTP calls to job platforms, and replace email delivery with fakes.
