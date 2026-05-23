from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[1]
BACKEND_ENV_FILE = BACKEND_DIR / ".env"
PREFERRED_SQL_SERVER_DRIVERS = ("ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server")
LOCAL_DEV_CORS_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
)
LOCAL_DEV_CORS_ORIGIN_REGEX = (
    r"^http://("
    r"localhost|127\.0\.0\.1|"
    r"10\.\d{1,3}\.\d{1,3}\.\d{1,3}|"
    r"172\.(1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3}|"
    r"192\.168\.\d{1,3}\.\d{1,3}"
    r"):(5173|3000)$"
)


def installed_odbc_drivers() -> list[str]:
    try:
        import pyodbc
    except ImportError:
        return []
    return list(pyodbc.drivers())


def select_sql_server_driver(configured_driver: str | None = None) -> str:
    installed = installed_odbc_drivers()
    if configured_driver and configured_driver.strip():
        driver = configured_driver.strip()
        if driver not in installed:
            raise RuntimeError(
                f"Configured DB_DRIVER '{driver}' is not installed. "
                f"Installed SQL Server drivers: {', '.join(_sql_server_drivers(installed)) or 'none'}"
            )
        return driver

    for driver in PREFERRED_SQL_SERVER_DRIVERS:
        if driver in installed:
            return driver

    raise RuntimeError(
        "No supported SQL Server ODBC driver is installed. Install ODBC Driver 18 for SQL Server "
        "or ODBC Driver 17 for SQL Server, then rerun the backend."
    )


def _sql_server_drivers(drivers: list[str]) -> list[str]:
    return [driver for driver in drivers if "SQL Server" in driver]


class Settings(BaseSettings):
    app_name: str = "Procurement Agent"
    environment: str = "development"
    log_level: str = "INFO"

    db_server: str | None = Field(None, alias="DB_SERVER")
    db_name: str | None = Field(None, alias="DB_NAME")
    db_user: str | None = Field(None, alias="DB_USER")
    db_password: str | None = Field(None, alias="DB_PASSWORD")
    database_url: str | None = Field(None, alias="DATABASE_URL")
    db_driver: str | None = Field(None, alias="DB_DRIVER")
    db_trust_server_certificate: bool = Field(True, alias="DB_TRUST_SERVER_CERTIFICATE")
    db_encrypt: str = Field("no", alias="DB_ENCRYPT")

    openai_api_key: str | None = Field(None, alias="OPENAI_API_KEY")
    openai_model: str = Field("gpt-4.1-mini", alias="OPENAI_MODEL")

    frontend_origin: str = Field("http://localhost:5173", alias="FRONTEND_ORIGIN")
    admin_api_token: str | None = Field(None, alias="ADMIN_API_TOKEN")
    upload_storage_dir: str = Field("storage/uploads", alias="UPLOAD_STORAGE_DIR")
    max_upload_bytes: int = Field(10 * 1024 * 1024, alias="MAX_UPLOAD_BYTES")
    max_document_chars: int = Field(24000, alias="MAX_DOCUMENT_CHARS")

    smtp_host: str | None = Field(None, alias="SMTP_HOST")
    smtp_port: int = Field(587, alias="SMTP_PORT")
    smtp_user: str | None = Field(None, alias="SMTP_USER")
    smtp_password: str | None = Field(None, alias="SMTP_PASSWORD")
    smtp_from_email: str | None = Field(None, alias="SMTP_FROM_EMAIL")
    enable_real_email_send: bool = Field(False, alias="ENABLE_REAL_EMAIL_SEND")

    model_config = SettingsConfigDict(env_file=str(BACKEND_ENV_FILE), env_file_encoding="utf-8", populate_by_name=True)

    @property
    def cors_origins(self) -> List[str]:
        configured = [origin.strip().rstrip("/") for origin in self.frontend_origin.split(",") if origin.strip()]
        origins = list(dict.fromkeys(configured))
        if self.environment.lower() == "development":
            origins = list(dict.fromkeys([*origins, *LOCAL_DEV_CORS_ORIGINS]))
        if self.environment.lower() == "production" and "*" in origins:
            raise RuntimeError("Wildcard CORS origins are not allowed in production. Set FRONTEND_ORIGIN explicitly.")
        return origins

    @property
    def cors_origin_regex(self) -> str | None:
        if self.environment.lower() == "development":
            return LOCAL_DEV_CORS_ORIGIN_REGEX
        return None

    @property
    def is_test_environment(self) -> bool:
        return self.environment.lower() == "test"


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_sanitized_database_target() -> dict[str, str]:
    settings = get_settings()
    driver = "sqlite/test" if settings.database_url and settings.database_url.lower().startswith("sqlite") else select_sql_server_driver(settings.db_driver)
    return {
        "DB_SERVER": settings.db_server or "",
        "DB_NAME": settings.db_name or "",
        "DB_DRIVER": driver,
    }
