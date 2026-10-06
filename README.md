# JobForge

JobForge finds jobs for you. It scans job boards every 15 minutes, scores
each new job against your career profile, and emails you about the ones
worth your time:

- **89% or higher:** an email straight away. Several strong matches found
  in the same scan share one email.
- **60–88%:** one digest email each morning, at 08:00 in your timezone.
- **Below 60%, or outside your field:** shown in the app only.

The web app shows your matches, lets you save jobs and track applications,
and holds your career profile and notification preferences.

## How it works

1. **Discover.** The scheduler fetches jobs from the configured platforms
   (Remotive, Remote OK, Arbeitnow, Jobicy, Himalayas, We Work Remotely,
   and optionally Greenhouse, Lever and Ashby company boards or Adzuna).
   Searches use the job titles in users' career profiles, and broad feeds
   are filtered to jobs relevant to at least one profile.
2. **Deduplicate.** A job already imported from another platform is
   skipped.
3. **Score.** Each new job is scored from 0 to 100 on job title, skills,
   experience, work type and location. Only what the job states is
   scored, so a post that omits experience isn't penalised. Jobs the
   candidate can't take (wrong country, unpaid or volunteer) are capped at
   49. Salary is shown for reference but never changes the score.
4. **Notify.** Matches in the candidate's field that score 60 or more
   create a notification, delivered by email through
   [Resend](https://resend.com) according to the user's preferences.

## Tech stack

| Part | Stack |
| --- | --- |
| Monorepo | Turborepo, pnpm workspaces |
| Frontend (`apps/web`) | Next.js 16, React 19, TypeScript, CSS modules |
| Backend (`apps/api`) | FastAPI, SQLAlchemy 2, Alembic, APScheduler |
| Database | PostgreSQL |
| Email | Resend |

## Getting started

### Requirements

- Node.js 18+ and pnpm 9
- Python 3.14
- PostgreSQL

### Backend

```bash
cd apps/api
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # then fill in the values
alembic upgrade head
uvicorn app.main:app --reload
```

The API runs at http://localhost:8000, with interactive docs at
http://localhost:8000/docs. The scheduler starts with the server and runs
its first scan straight away.

### Frontend

```bash
pnpm install
pnpm --filter web dev
```

The app runs at http://localhost:3000. Create `apps/web/.env.local` with:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_DEV_USER_ID=5
```

There is no login yet: every page acts as the user in
`NEXT_PUBLIC_DEV_USER_ID`.

## Configuration

Backend settings live in `apps/api/.env`. See
[`apps/api/.env.example`](apps/api/.env.example) for the full list.

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | PostgreSQL connection string |
| `JOB_SOURCES` | Platforms to scan, comma separated |
| `RESEND_API_KEY`, `RESEND_FROM_EMAIL` | Email delivery |
| `DIGEST_ENABLED`, `DIGEST_HOUR`, `DIGEST_MINUTE` | Daily digest, in each user's timezone |
| `NOTIFICATION_MIN_SCORE` | Lowest score that notifies (default 60) |
| `NOTIFICATION_MAX_ATTEMPTS` | Email delivery retries (default 3) |
| `GREENHOUSE_BOARDS`, `LEVER_COMPANIES`, `ASHBY_BOARDS` | Company career pages to scan |
| `ADZUNA_APP_ID`, `ADZUNA_APP_KEY`, `ADZUNA_COUNTRY` | Adzuna (one country per search) |
| `LOG_LEVEL` | Server log level (default INFO) |

## Tests

```bash
cd apps/api
pytest
```

Tests run against an in-memory SQLite database and never call real job
platforms or send email.

```bash
pnpm --filter web lint
pnpm --filter web check-types
```

## Job platform terms

Most platforms require a link back to the original listing and a credit
to the platform; the app links to each job's source URL and shows the
platform's name. Remotive allows at most 4 requests a day (JobForge fetches
it every 6 hours) and does not allow its jobs to be shown behind a sign-up
without its paid API, so remove it before a public launch or arrange
access.

## Documentation

- [System design](docs/architecture/system-design.md)
- [Backend](docs/architecture/backend.md)
- [Frontend](docs/architecture/frontend.md)
- [API endpoints](docs/api/endpoints.md)
- [Database schema](docs/database/schema.md) and [ERD](docs/database/erd.md)
- [MVP](docs/product/mvp.md) and [Roadmap](docs/product/roadmap.md)
- [Engineering principles](docs/engineering-principles.md)
