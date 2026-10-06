# JobForge: instructions for AI coding agents

Read **[docs/architecture/ai-agents.md](docs/architecture/ai-agents.md)**
before changing code. It's the single source of truth for this project's
structure, commands, domain rules and conventions. Update it in the same
change whenever something it says stops being true.

Rules that must never be missed:

1. `apps/api/.env` holds secrets. Never print, log or commit it.
2. The PostgreSQL database is the user's real data. Back it up
   (`python backup_database.py` in `apps/api`) before migrations or
   deletions, and ask before deleting rows.
3. The scheduler must run in exactly one process. The app normally runs
   through the Windows tasks "JobForge API" and "JobForge Web"; stop the
   matching task before starting a dev server on port 8000 or 3000.
4. Tests use in-memory SQLite and must never call real job platforms or
   send email.
5. The instant-alert threshold (89) exists in two places that must match:
   `IMMEDIATE_NOTIFICATION_SCORE` in the API and `HIGH_MATCH_SCORE` in
   `apps/web/lib/config.ts`.
