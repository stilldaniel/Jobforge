# API endpoints

Base URL in development: `http://localhost:8000`. Interactive docs with
request and response schemas: `/docs`.

There is no authentication yet. Endpoints take the user's ID in the path
or body and trust it.

## Users

| Method | Path | Description |
| --- | --- | --- |
| GET | `/users/` | List users |
| POST | `/users/` | Create a user. `timezone` must be an IANA name such as `Africa/Lagos` |
| GET | `/users/{user_id}` | Get a user |
| PUT | `/users/{user_id}` | Replace email, name and timezone |
| DELETE | `/users/{user_id}` | Delete a user and everything that belongs to them |
| GET | `/users/{user_id}/notification-preferences` | Get the four notification switches |
| PATCH | `/users/{user_id}/notification-preferences` | Change only the switches sent |

Notification preferences:

| Field | When off |
| --- | --- |
| `job_alerts_enabled` | No notifications are created at all |
| `email_notifications_enabled` | Nothing is emailed; notifications still show in the app |
| `high_match_alerts_enabled` | Matches of 89%+ go into the daily digest instead of an instant email |
| `digest_notifications_enabled` | No daily digest email |

## Career profile

| Method | Path | Description |
| --- | --- | --- |
| POST | `/users/{user_id}/career-profile/` | Create the profile |
| GET | `/users/{user_id}/career-profile/` | Get the profile |
| PUT | `/users/{user_id}/career-profile/` | Replace the profile |

Creating or updating the profile re-scores all of the user's job matches
straight away, without sending notifications. `salary_currency` is a
3-letter code and `salary_period` is `month` or `year`.

## Jobs

| Method | Path | Description |
| --- | --- | --- |
| GET | `/jobs/` | List all jobs |
| POST | `/jobs/` | Add a job by hand. Skills and experience are read from the description; returns 409 for a duplicate |
| GET | `/jobs/{job_id}` | Get a job |
| PUT | `/jobs/{job_id}` | Replace a job |
| DELETE | `/jobs/{job_id}` | Delete a job and its matches |

## Job discovery

| Method | Path | Description |
| --- | --- | --- |
| POST | `/job-discovery/monitor` | Run one full scan now: fetch from `JOB_SOURCES`, match new jobs and create notifications |
| POST | `/job-discovery/run` | Import the built-in sample jobs only (development) |

## Matches

| Method | Path | Description |
| --- | --- | --- |
| GET | `/matches/{user_id}` | The user's matches, highest score first (empty list if none) |
| POST | `/matches/{user_id}/generate` | Re-score every job for the user |
| POST | `/matches/{user_id}/notifications` | Create notifications for existing matches that qualify |

## Notifications

| Method | Path | Description |
| --- | --- | --- |
| GET | `/notifications/{user_id}` | The user's notifications, newest first |
| PATCH | `/notifications/{notification_id}/read` | Mark as read |
| POST | `/notifications/digest/process` | Send every pending digest now, ignoring the schedule |

Notification `status` is `pending`, `sent`, `failed` (after
`NOTIFICATION_MAX_ATTEMPTS` failed deliveries) or `skipped` (not emailed
because of the user's preferences).

## Saved jobs

| Method | Path | Description |
| --- | --- | --- |
| POST | `/saved-jobs/` | Save a job (`user_id`, `job_id`); 409 if already saved |
| GET | `/saved-jobs/{user_id}` | The user's saved jobs |
| GET | `/saved-jobs/{user_id}/{job_id}` | Whether a job is saved (404 if not) |
| DELETE | `/saved-jobs/{user_id}/{job_id}` | Unsave a job |

## Applications

| Method | Path | Description |
| --- | --- | --- |
| POST | `/applications/` | Track an application (`user_id`, `job_id`, optional `notes`) |
| GET | `/applications/{user_id}` | The user's applications |
| GET | `/applications/{user_id}/{job_id}` | One application |
| PATCH | `/applications/{user_id}/{job_id}` | Update `status` (`applied`, `interview`, `offer`, `rejected`, `withdrawn`) or `notes` |
| DELETE | `/applications/{user_id}/{job_id}` | Stop tracking |

## Health

| Method | Path | Description |
| --- | --- | --- |
| GET | `/health` | Liveness check |
