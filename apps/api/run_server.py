"""
Run the JobForge API in the background, for starting at Windows log-on.

Meant to be run with pythonw.exe (no console window). All output goes to
logs/api.log next to this file. Unlike `uvicorn --reload`, this runs a
single process, so the scheduler runs exactly once.

    .venv\\Scripts\\pythonw.exe run_server.py
"""

import os
import socket
import sys
from pathlib import Path

HOST = "127.0.0.1"
PORT = int(os.getenv("JOBFORGE_PORT", "8000"))

# Keep the log from growing without limit: start a new file at each launch
# once it passes this size, keeping one previous file.
MAX_LOG_BYTES = 5 * 1024 * 1024

API_DIR = Path(__file__).resolve().parent
LOG_DIR = API_DIR / "logs"
LOG_FILE = LOG_DIR / "api.log"


def port_in_use() -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        return sock.connect_ex((HOST, PORT)) == 0


def redirect_output() -> None:
    LOG_DIR.mkdir(exist_ok=True)

    if LOG_FILE.exists() and LOG_FILE.stat().st_size > MAX_LOG_BYTES:
        LOG_FILE.replace(LOG_FILE.with_suffix(".log.1"))

    log = open(LOG_FILE, "a", encoding="utf-8", buffering=1)

    # pythonw has no console, so stdout and stderr would be None.
    sys.stdout = log
    sys.stderr = log


def main() -> None:
    os.chdir(API_DIR)
    sys.path.insert(0, str(API_DIR))

    redirect_output()

    # Already running (another log-on, or a dev server): don't start a
    # second scheduler.
    if port_in_use():
        print(f"Port {PORT} is already in use; not starting.", flush=True)
        return

    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=HOST,
        port=PORT,
    )


if __name__ == "__main__":
    main()
