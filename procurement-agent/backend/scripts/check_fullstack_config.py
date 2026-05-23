from __future__ import annotations

import sys
from pathlib import Path

from dotenv import dotenv_values, load_dotenv


BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BACKEND_DIR.parent
FRONTEND_DIR = PROJECT_DIR / "frontend"


def main() -> int:
    sys.path.insert(0, str(BACKEND_DIR))
    load_dotenv(BACKEND_DIR / ".env")

    from app.config import LOCAL_DEV_CORS_ORIGINS, get_settings

    settings = get_settings()
    frontend_env = dotenv_values(FRONTEND_DIR / ".env")
    api_base_url = str(frontend_env.get("VITE_API_BASE_URL") or "http://127.0.0.1:8000")
    expected_frontend_url = "http://localhost:5173 or http://127.0.0.1:5173"

    print(f"Backend env file: {BACKEND_DIR / '.env'}")
    print(f"Frontend env file: {FRONTEND_DIR / '.env'}")
    print(f"Environment: {settings.environment}")
    print(f"Configured FRONTEND_ORIGIN: {settings.frontend_origin}")
    print("Backend allowed CORS origins:")
    for origin in settings.cors_origins:
        print(f"- {origin}")
    if settings.cors_origin_regex:
        print(f"Development CORS origin regex: {settings.cors_origin_regex}")
    print(f"Expected local frontend URL: {expected_frontend_url}")
    print(f"Frontend VITE_API_BASE_URL: {api_base_url}")
    print("Recommended frontend .env value: VITE_API_BASE_URL=http://127.0.0.1:8000")
    print("If Vite opens on a LAN address like http://192.168.x.x:5173, development CORS allows it.")

    warnings: list[str] = []
    if settings.environment.lower() == "development":
        missing = [origin for origin in LOCAL_DEV_CORS_ORIGINS if origin not in settings.cors_origins]
        if missing:
            warnings.append("Missing local development CORS origins: " + ", ".join(missing))
    if api_base_url.rstrip("/") not in {"http://127.0.0.1:8000", "http://localhost:8000"}:
        warnings.append("VITE_API_BASE_URL does not point to the expected local backend on port 8000.")
    if "localhost" in api_base_url and "http://127.0.0.1:5173" not in settings.cors_origins:
        warnings.append("Frontend/backend localhost vs 127.0.0.1 mismatch may break CORS.")

    if warnings:
        print("\nFull-stack config warnings:")
        for warning in warnings:
            print(f"- {warning}")
        return 1

    print("\nFull-stack config looks ready for local development.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
