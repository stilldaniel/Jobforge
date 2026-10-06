# Roadmap

## Before other people can use it

1. **Accounts and login.** Every page currently acts as one development
   user and the API trusts the user ID it's given.
2. **Hosting.** API, PostgreSQL database and frontend online, so scans run
   around the clock. The scheduler must run in a single process.
3. **Email sending domain.** Verify a domain in Resend so emails can be
   delivered to any address.
4. **Remotive terms.** Remotive doesn't allow its jobs behind a sign-up
   without its paid API. Remove it from `JOB_SOURCES` or arrange access.

## Improvements

- Show salary in the profile's currency using exchange rates.
- More job sources, especially ones covering Nigeria and Africa.
- Re-scoring and notifying when a job's details change on its platform.
- Retire the development-only `POST /job-discovery/run` endpoint, which
  always imports the sample jobs.
