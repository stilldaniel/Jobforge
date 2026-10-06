# Frontend

Next.js 16 app (App Router) in `apps/web`, written in TypeScript with CSS
modules and lucide icons. Pages are client components that call the
backend API directly.

## Pages

| Route | Page |
| --- | --- |
| `/` | Dashboard: stats, application pipeline, high-quality matches, recent notifications |
| `/jobs` | All jobs with search, filters and sorting by match score |
| `/jobs/[id]` | Job details, match reasons, save and track application |
| `/saved-jobs` | Saved jobs |
| `/applications` | Tracked applications and their status |
| `/notifications` | All notifications, mark as read |
| `/profile` | Career profile; saving re-scores all matches |
| `/settings` | Account details and notification preferences |

## Layout

```
app/                   Routes (see above); layout.tsx sets fonts and metadata
components/layout/     AppShell: sidebar, header, unread notification badge
components/dashboard/  Dashboard cards and sections
lib/api/               One module per API resource, built on client.ts
lib/config.ts          DEV_USER_ID and HIGH_MATCH_SCORE
lib/format.ts          Salary and job source formatting
types/api.ts           Types mirroring the API's response models
```

## API client

`lib/api/client.ts` wraps `fetch` with JSON handling and turns API errors
into `Error`s carrying the API's `detail` message. The base URL comes from
`NEXT_PUBLIC_API_URL` (default `/api`).

`next.config.js` forwards `/api/*` to the backend (`JOBFORGE_API_URL`,
default `http://127.0.0.1:8000`), so the browser never calls the backend
directly. It keeps trailing slashes (`skipTrailingSlashRedirect`) and has
a separate rule for slash-ending paths, because FastAPI routes such as
`/jobs/` would otherwise redirect to the backend's own address.

## Current user

There is no login yet. Every page acts as `DEV_USER_ID` from
`lib/config.ts`, set with `NEXT_PUBLIC_DEV_USER_ID`.

## Conventions

- Match score thresholds come from `HIGH_MATCH_SCORE` in `lib/config.ts`,
  which must equal the API's `IMMEDIATE_NOTIFICATION_SCORE`.
- Show salaries with `formatSalary` and job sources with `formatSource`
  from `lib/format.ts`. Several platforms require their name to be shown.
- `pnpm --filter web lint` runs with `--max-warnings 0`.
