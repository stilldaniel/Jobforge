"""
Run the JobForge web app in the background, for starting at Windows log-on.

Meant to be run with the API's pythonw.exe (no console window):

    ..\\api\\.venv\\Scripts\\pythonw.exe run_web.py [--port 3000]

Serves a production build with `next start` on http://localhost:3000,
rebuilding first whenever the source has changed since the last build.
Output goes to logs/web.log next to this file.
"""

import os
import shutil
import socket
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HOST = "127.0.0.1"


def configured_port() -> int:
    if "--port" in sys.argv:
        return int(sys.argv[sys.argv.index("--port") + 1])

    return int(os.getenv("JOBFORGE_WEB_PORT", "3000"))


PORT = configured_port()

WEB_DIR = Path(__file__).resolve().parent
LOG_DIR = WEB_DIR / "logs"
LOG_FILE = LOG_DIR / "web.log"
MAX_LOG_BYTES = 5 * 1024 * 1024

NEXT_BIN = WEB_DIR / "node_modules" / "next" / "dist" / "bin" / "next"
BUILD_ID = WEB_DIR / ".next" / "BUILD_ID"

# Anything that changes the built app.
SOURCES = [
    "app",
    "components",
    "lib",
    "types",
    "public",
    "package.json",
    "next.config.js",
    "tsconfig.json",
    ".env.local",
]

NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def log(message: str) -> None:
    print(f"{datetime.now():%Y-%m-%d %H:%M:%S} {message}", flush=True)


def redirect_output() -> None:
    LOG_DIR.mkdir(exist_ok=True)

    if LOG_FILE.exists() and LOG_FILE.stat().st_size > MAX_LOG_BYTES:
        LOG_FILE.replace(LOG_FILE.with_suffix(".log.1"))

    log_file = open(LOG_FILE, "a", encoding="utf-8", buffering=1)

    # pythonw has no console, so stdout and stderr would be None.
    sys.stdout = log_file
    sys.stderr = log_file


def port_in_use() -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        return sock.connect_ex((HOST, PORT)) == 0


def find_node() -> str:
    return (
        shutil.which("node")
        or r"C:\Program Files\nodejs\node.exe"
    )


def newest_source_change() -> float:
    newest = 0.0

    for name in SOURCES:
        path = WEB_DIR / name

        if path.is_file():
            newest = max(newest, path.stat().st_mtime)
        elif path.is_dir():
            for file in path.rglob("*"):
                if file.is_file():
                    newest = max(newest, file.stat().st_mtime)

    return newest


def build_is_stale() -> bool:
    if not BUILD_ID.exists():
        return True

    return newest_source_change() > BUILD_ID.stat().st_mtime


def kill_with_this_process(process: subprocess.Popen) -> None:
    """
    Put the child in a Windows job object that is closed, killing the
    child, when this launcher exits for any reason. Without it, stopping
    the scheduled task would end the launcher but leave Node running.
    """

    if os.name != "nt":
        return

    import ctypes
    from ctypes import wintypes

    class IoCounters(ctypes.Structure):
        _fields_ = [
            (name, ctypes.c_ulonglong)
            for name in (
                "ReadOperationCount",
                "WriteOperationCount",
                "OtherOperationCount",
                "ReadTransferCount",
                "WriteTransferCount",
                "OtherTransferCount",
            )
        ]

    class BasicLimitInformation(ctypes.Structure):
        _fields_ = [
            ("PerProcessUserTimeLimit", ctypes.c_int64),
            ("PerJobUserTimeLimit", ctypes.c_int64),
            ("LimitFlags", wintypes.DWORD),
            ("MinimumWorkingSetSize", ctypes.c_size_t),
            ("MaximumWorkingSetSize", ctypes.c_size_t),
            ("ActiveProcessLimit", wintypes.DWORD),
            ("Affinity", ctypes.c_size_t),
            ("PriorityClass", wintypes.DWORD),
            ("SchedulingClass", wintypes.DWORD),
        ]

    class ExtendedLimitInformation(ctypes.Structure):
        _fields_ = [
            ("BasicLimitInformation", BasicLimitInformation),
            ("IoInfo", IoCounters),
            ("ProcessMemoryLimit", ctypes.c_size_t),
            ("JobMemoryLimit", ctypes.c_size_t),
            ("PeakProcessMemoryUsed", ctypes.c_size_t),
            ("PeakJobMemoryUsed", ctypes.c_size_t),
        ]

    job_object_extended_limit_information = 9
    job_object_limit_kill_on_job_close = 0x2000

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateJobObjectW.restype = wintypes.HANDLE
    kernel32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    kernel32.SetInformationJobObject.argtypes = [
        wintypes.HANDLE,
        ctypes.c_int,
        ctypes.c_void_p,
        wintypes.DWORD,
    ]
    kernel32.AssignProcessToJobObject.argtypes = [
        wintypes.HANDLE,
        wintypes.HANDLE,
    ]

    job = kernel32.CreateJobObjectW(None, None)

    info = ExtendedLimitInformation()
    info.BasicLimitInformation.LimitFlags = (
        job_object_limit_kill_on_job_close
    )

    configured = kernel32.SetInformationJobObject(
        job,
        job_object_extended_limit_information,
        ctypes.byref(info),
        ctypes.sizeof(info),
    )
    assigned = kernel32.AssignProcessToJobObject(
        job,
        wintypes.HANDLE(int(process._handle)),
    )

    if not (job and configured and assigned):
        log(
            "Warning: couldn't tie Node to this launcher "
            f"(error {ctypes.get_last_error()}); stopping the task "
            "may leave it running."
        )

    # The job handle is deliberately never closed: it closes when this
    # process exits, which is what kills the child.


def run_next(*args: str) -> int:
    command = [find_node(), str(NEXT_BIN), *args]

    process = subprocess.Popen(
        command,
        cwd=WEB_DIR,
        stdout=sys.stdout,
        stderr=subprocess.STDOUT,
        creationflags=NO_WINDOW,
    )

    kill_with_this_process(process)

    return process.wait()


def main() -> int:
    os.chdir(WEB_DIR)
    redirect_output()

    # Already running, or the dev server is using the port.
    if port_in_use():
        log(f"Port {PORT} is already in use; not starting.")
        return 0

    if build_is_stale():
        log("Source changed since the last build; building.")

        if run_next("build") != 0:
            log("Build failed; not starting. See the output above.")
            return 1

    log(f"Starting on http://localhost:{PORT}")

    return run_next(
        "start",
        "--hostname",
        HOST,
        "--port",
        str(PORT),
    )


if __name__ == "__main__":
    sys.exit(main())
