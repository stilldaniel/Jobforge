"""
Back up the JobForge database with pg_dump, keeping the newest backups.

Run nightly by the "JobForge Backup" scheduled task (with pythonw.exe), or
by hand:

    .venv\\Scripts\\python.exe backup_database.py

Settings (from the environment or apps/api/.env):
    DATABASE_URL         The database to back up
    BACKUP_DIR           Where to write backups
                         (default: Documents\\JobForge Backups)
    BACKUP_KEEP          How many backups to keep (default: 7)
    PG_DUMP_PATH         Full path to pg_dump.exe, if it isn't found
                         automatically

Restore a backup with:

    pg_restore --clean --if-exists --dbname <database url> <backup file>
"""

import glob
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine import make_url

API_DIR = Path(__file__).resolve().parent
LOG_FILE = API_DIR / "logs" / "backup.log"

BACKUP_PREFIX = "jobforge-"
BACKUP_SUFFIX = ".dump"


def log(message: str) -> None:
    LOG_FILE.parent.mkdir(exist_ok=True)

    line = f"{datetime.now():%Y-%m-%d %H:%M:%S} {message}"

    with open(LOG_FILE, "a", encoding="utf-8") as file:
        file.write(line + "\n")

    if sys.stdout:
        print(line)


def find_pg_dump() -> str:
    configured = os.getenv("PG_DUMP_PATH")

    if configured:
        return configured

    on_path = shutil.which("pg_dump")

    if on_path:
        return on_path

    # The PostgreSQL installer doesn't add itself to PATH; use the
    # newest installed version.
    installed = sorted(
        glob.glob(r"C:\Program Files\PostgreSQL\*\bin\pg_dump.exe"),
        key=lambda path: int(Path(path).parents[1].name.split(".")[0]),
    )

    if installed:
        return installed[-1]

    raise FileNotFoundError(
        "pg_dump not found. Set PG_DUMP_PATH in apps/api/.env."
    )


def backup_dir() -> Path:
    configured = os.getenv("BACKUP_DIR")

    if configured:
        return Path(configured)

    return Path.home() / "Documents" / "JobForge Backups"


def keep_count() -> int:
    try:
        return max(int(os.getenv("BACKUP_KEEP", "7")), 1)
    except ValueError:
        return 7


def main() -> int:
    load_dotenv(API_DIR / ".env")

    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        log("FAILED: DATABASE_URL is not set")
        return 1

    url = make_url(database_url)

    target_dir = backup_dir()
    target_dir.mkdir(parents=True, exist_ok=True)

    target = target_dir / (
        f"{BACKUP_PREFIX}{datetime.now():%Y-%m-%d_%H%M}{BACKUP_SUFFIX}"
    )
    partial = target.with_suffix(".partial")

    # Pass the password through the environment, not the command line,
    # so it doesn't appear in the process list.
    env = dict(os.environ)

    if url.password:
        env["PGPASSWORD"] = url.password

    command = [
        find_pg_dump(),
        "--format=custom",
        f"--file={partial}",
        f"--host={url.host or 'localhost'}",
        f"--port={url.port or 5432}",
        f"--username={url.username or 'postgres'}",
        "--no-password",
        url.database,
    ]

    result = subprocess.run(
        command,
        env=env,
        capture_output=True,
        text=True,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )

    if result.returncode != 0:
        partial.unlink(missing_ok=True)
        log(f"FAILED: pg_dump exited with {result.returncode}: "
            f"{result.stderr.strip()}")
        return 1

    partial.replace(target)

    log(f"Backed up to {target} ({target.stat().st_size:,} bytes)")

    backups = sorted(
        target_dir.glob(f"{BACKUP_PREFIX}*{BACKUP_SUFFIX}"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )

    for old in backups[keep_count():]:
        old.unlink()
        log(f"Removed old backup {old.name}")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        log(f"FAILED: {exc}")
        sys.exit(1)
