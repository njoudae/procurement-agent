from __future__ import annotations

import importlib
import os
import socket
import sys
from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BACKEND_DIR.parent
REQUIRED_TABLES = {
    "Vendors",
    "PurchaseRequests",
    "AgentActions",
    "Approvals",
    "EmailLogs",
    "ExecutionLogs",
    "RequestAttachments",
    "DocumentExtractions",
}
REQUIRED_PACKAGES = {
    "fastapi": "fastapi",
    "sqlalchemy": "sqlalchemy",
    "pyodbc": "pyodbc",
    "langgraph": "langgraph",
    "openai": "openai",
    "pdfplumber": "pdfplumber",
    "fitz": "pymupdf",
    "pypdf": "pypdf",
    "pandas": "pandas",
    "openpyxl": "openpyxl",
    "docx": "python-docx",
}


def main() -> int:
    sys.path.insert(0, str(BACKEND_DIR))
    load_dotenv(BACKEND_DIR / ".env")

    from app.config import installed_odbc_drivers, select_sql_server_driver

    errors: list[str] = []
    warnings: list[str] = []

    print(f"Project: {PROJECT_DIR}")
    print(f"Backend: {BACKEND_DIR}")
    print(f"Python: {sys.version.split()[0]}")
    if sys.version_info < (3, 12) or sys.version_info >= (3, 13):
        errors.append("Python 3.12 is required. Run uv sync from the repo root, then run from procurement-agent/backend: uv run python scripts/check_environment.py")

    for import_name, package_name in REQUIRED_PACKAGES.items():
        try:
            importlib.import_module(import_name)
            print(f"OK package: {package_name}")
        except ImportError:
            errors.append(f"Missing package: {package_name}. Run from the repo root: uv sync")

    environment = os.getenv("ENVIRONMENT", "development").lower()
    database_url = os.getenv("DATABASE_URL", "")
    if database_url.lower().startswith("sqlite"):
        if environment == "test":
            warnings.append("ENVIRONMENT=test with SQLite DATABASE_URL is allowed for automated tests only.")
        else:
            errors.append("DATABASE_URL points to SQLite. Remove it for normal runtime and configure SQL Server.")

    required_env = ["DB_SERVER", "DB_NAME", "DB_USER", "DB_PASSWORD"]
    for name in required_env:
        value = os.getenv(name)
        if not value:
            errors.append(f"Missing required environment variable: {name}")
        elif value.strip().lower() in {"change-me", "changeme", "your_sql_password", "password"}:
            errors.append(f"{name} still contains a placeholder value.")

    installed_drivers = installed_odbc_drivers()
    sql_server_drivers = [driver for driver in installed_drivers if "SQL Server" in driver]
    print("Installed SQL Server ODBC drivers: " + (", ".join(sql_server_drivers) if sql_server_drivers else "none"))

    selected_driver = None
    try:
        selected_driver = select_sql_server_driver(os.getenv("DB_DRIVER"))
        print(f"Selected SQL Server ODBC driver: {selected_driver}")
    except RuntimeError as exc:
        errors.append(str(exc))

    server = os.getenv("DB_SERVER", "")
    host, port = parse_server_host_port(server)
    if host and port:
        try:
            with socket.create_connection((host, port), timeout=5):
                print(f"OK TCP: {host}:{port} is reachable")
        except OSError as exc:
            errors.append(
                f"SQL Server TCP check failed for {host}:{port}. "
                "Verify SQL Server is running, TCP/IP is enabled, firewall allows the port, "
                f"and DB_SERVER is correct. Detail: {exc}"
            )
    elif server:
        warnings.append(
            "Could not infer a TCP port from DB_SERVER. For reliable local checks, use host,port "
            "format such as localhost,1433."
        )

    if selected_driver and not errors:
        try:
            import pyodbc

            connection = pyodbc.connect(build_pyodbc_connection_string(selected_driver), timeout=8)
            try:
                print("OK pyodbc: SQL Server login succeeded")
                existing_tables = fetch_existing_tables(connection)
                missing_tables = sorted(REQUIRED_TABLES - existing_tables)
                if missing_tables:
                    errors.append(
                        "Database connection succeeded, but required tables are missing: "
                        + ", ".join(missing_tables)
                    )
                else:
                    print("OK schema: required tables exist")
            finally:
                connection.close()
        except Exception as exc:
            errors.append(f"pyodbc SQL Server connection failed: {exc}")

    for warning in warnings:
        print(f"WARNING: {warning}")
    if errors:
        print("\nEnvironment check failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("\nEnvironment check passed.")
    return 0


def parse_server_host_port(server: str) -> tuple[str | None, int | None]:
    server = server.strip()
    if not server or server.lower().startswith("(localdb)"):
        return None, None
    if "," in server:
        host, raw_port = server.rsplit(",", 1)
        try:
            return normalize_local_host(host), int(raw_port)
        except ValueError:
            return normalize_local_host(host), None
    if "\\" in server:
        return None, None
    return normalize_local_host(server), 1433


def normalize_local_host(host: str) -> str:
    host = host.strip()
    return "127.0.0.1" if host.lower() in {"localhost", "."} else host


def build_pyodbc_connection_string(driver: str) -> str:
    trust = "yes" if os.getenv("DB_TRUST_SERVER_CERTIFICATE", "true").lower() in {"1", "true", "yes"} else "no"
    encrypt = os.getenv("DB_ENCRYPT", "no")
    return (
        f"DRIVER={{{driver}}};"
        f"SERVER={os.getenv('DB_SERVER')};"
        f"DATABASE={os.getenv('DB_NAME')};"
        f"UID={os.getenv('DB_USER')};"
        f"PWD={os.getenv('DB_PASSWORD')};"
        f"TrustServerCertificate={trust};"
        f"Encrypt={encrypt};"
    )


def fetch_existing_tables(connection) -> set[str]:
    cursor = connection.cursor()
    rows = cursor.execute(
        """
        SELECT TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_TYPE = 'BASE TABLE'
        """
    ).fetchall()
    return {row[0] for row in rows}


if __name__ == "__main__":
    raise SystemExit(main())
