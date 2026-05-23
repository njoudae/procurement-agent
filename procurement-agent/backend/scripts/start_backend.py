from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run backend after local environment checks.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default="8000")
    parser.add_argument("--no-reload", action="store_true")
    parser.add_argument("--skip-check", action="store_true")
    args = parser.parse_args()

    load_dotenv(BACKEND_DIR / ".env")

    if not args.skip_check:
        print("Running environment check before backend startup...")
        check = subprocess.run([sys.executable, str(BACKEND_DIR / "scripts" / "check_environment.py")], cwd=BACKEND_DIR)
        if check.returncode != 0:
            print("Backend not started because environment check failed.")
            print("Fix the errors above or run with --skip-check for debugging only.")
            return check.returncode

    command = [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        args.host,
        "--port",
        str(args.port),
    ]
    if not args.no_reload:
        command.append("--reload")

    print("Starting backend:")
    print(" ".join(command))
    return subprocess.run(command, cwd=BACKEND_DIR).returncode


if __name__ == "__main__":
    raise SystemExit(main())
