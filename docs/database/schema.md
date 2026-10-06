# Database schema

PostgreSQL, managed with Alembic migrations in `apps/api/migrations`.
Deleting a user or a job deletes everything that refers to it (all foreign
keys use `ON DELETE CASCADE`).

## users

| Column | Type | Notes |
| --- | --- | --- |
| id | integer | Primary key |
| email | varchar(255) | Unique |
| full_name | varchar(255) | Optional |
| timezone | varchar(100) | IANA name, e.g. `Africa/Lagos`; sets the daily digest time |
| job_alerts_enabled | boolean | Default true |
| high_match_alerts_enabled | boolean | Default true |
| digest_notifications_enabled | boolean | Default true |
| email_notifications_enabled | boolean | Default true |
| last_digest_at | timestamptz | When the user's last digest was processed; one digest a day |
| created_at, updated_at | timestamptz | |

## career_profiles

One per user.

| Column | Type | Notes |
| --- | --- | --- |
| id | integer | Primary key |
| user_id | integer | → users, unique |
| professional_title | varchar(255) | Used for search queries and title scoring |
| skills | text | JSON array of strings, e.g. `["React", "TypeScript"]` |
| years_of_experience | integer | Default 0 |
| summary | text | |
| candidate_location | varchar(255) | Where the candidate lives; decides remote eligibility |
| preferred_work_type | varchar(50) | `remote`, `hybrid` or `onsite` |
| preferred_location | varchar(255) | |
| minimum_salary, maximum_salary | integer | Shown against job pay; never affects the score |
| salary_currency | varchar(3) | ISO 4217 code |
| salary_period | varchar(10) | `month` or `year` |
| created_at, updated_at | timestamptz | |

## jobs

| Column | Type | Notes |
| --- | --- | --- |
| id | integer | Primary key |
| title, company | varchar(255) | |
| description | text | Plain text, one paragraph per line |
| required_skills | text | JSON array extracted from the title and description |
| required_experience | integer | Minimum years, extracted from the description |
| location | varchar(255) | |
| remote_eligibility | varchar(255) | Countries or regions a remote job accepts, e.g. `Worldwide`, `United States` |
| work_type | varchar(50) | `remote`, `hybrid`, `on-site` or empty |
| salary_min, salary_max | integer | Yearly amounts for imported jobs |
| salary_currency | varchar(3) | |
| salary_period | varchar(20) | `year` for imported jobs |
| application_url | varchar(1000) | Link to the original listing |
| source | varchar(100) | Platform, e.g. `himalayas`, `remoteok`, `manual` |
| fingerprint | varchar(64) | Unique. Identifies one listing: the platform's ID where available, otherwise title + company + URL |
| dedupe_key | varchar(64) | Indexed. Normalised title + company, to spot the same job on another platform |
| posted_at | timestamptz | |
| created_at, updated_at | timestamptz | |

## job_matches

One per user and job.

| Column | Type | Notes |
| --- | --- | --- |
| id | integer | Primary key |
| user_id | integer | → users |
| job_id | integer | → jobs |
| score | integer | 0–100 |
| match_reasons | text | Reasons joined with `; ` |
| created_at, updated_at | timestamptz | |

## notifications

| Column | Type | Notes |
| --- | --- | --- |
| id | integer | Primary key |
| user_id | integer | → users |
| job_match_id | integer | → job_matches |
| notification_type | varchar(50) | `immediate` (89%+) or `digest` |
| channel | varchar(50) | `email` |
| status | varchar(50) | `pending`, `sent`, `failed` or `skipped` |
| title, message | varchar(255), text | |
| attempts | integer | Delivery attempts so far |
| last_error | text | |
| created_at | timestamptz | |
| sent_at, read_at | timestamptz | |

## saved_jobs

| Column | Type | Notes |
| --- | --- | --- |
| id | integer | Primary key |
| user_id | integer | → users |
| job_id | integer | → jobs; unique together with user_id |
| created_at | timestamptz | |

## applications

| Column | Type | Notes |
| --- | --- | --- |
| id | integer | Primary key |
| user_id | integer | → users |
| job_id | integer | → jobs |
| status | varchar(30) | `applied`, `interview`, `offer`, `rejected` or `withdrawn` |
| applied_at | timestamptz | |
| notes | text | |
