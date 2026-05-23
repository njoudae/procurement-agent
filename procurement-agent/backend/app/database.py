from contextlib import contextmanager
from typing import Generator
from urllib.parse import quote_plus

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings, select_sql_server_driver


class Base(DeclarativeBase):
    pass


def build_database_url() -> str:
    settings = get_settings()
    if settings.database_url and settings.database_url.lower().startswith("sqlite"):
        if settings.is_test_environment:
            return settings.database_url
        raise RuntimeError("SQLite DATABASE_URL is only allowed when ENVIRONMENT=test. Configure SQL Server for runtime.")

    if settings.database_url:
        return settings.database_url

    missing = [
        env_name
        for env_name, value in {
            "DB_SERVER": settings.db_server,
            "DB_NAME": settings.db_name,
            "DB_USER": settings.db_user,
            "DB_PASSWORD": settings.db_password,
        }.items()
        if not value
    ]
    if missing:
        raise RuntimeError(f"Missing required SQL Server environment variables: {', '.join(missing)}")

    driver = select_sql_server_driver(settings.db_driver)
    trust = "yes" if settings.db_trust_server_certificate else "no"
    odbc_connection = (
        f"DRIVER={{{driver}}};"
        f"SERVER={settings.db_server};"
        f"DATABASE={settings.db_name};"
        f"UID={settings.db_user};"
        f"PWD={settings.db_password};"
        f"TrustServerCertificate={trust};"
        f"Encrypt={settings.db_encrypt};"
    )
    return f"mssql+pyodbc:///?odbc_connect={quote_plus(odbc_connection)}"


database_url = build_database_url()
engine_options = {"pool_pre_ping": True, "future": True}
if not database_url.lower().startswith("sqlite"):
    engine_options.update({"pool_size": 5, "max_overflow": 10})

engine = create_engine(database_url, **engine_options)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db() -> None:
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
