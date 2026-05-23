from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from sqlalchemy import Boolean, Date, DateTime, Float, Integer, Numeric, String, Text, inspect, text


BACKEND_DIR = Path(__file__).resolve().parents[1]
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


def main() -> int:
    sys.path.insert(0, str(BACKEND_DIR))
    load_dotenv(BACKEND_DIR / ".env")

    try:
        from app.config import BACKEND_ENV_FILE, get_sanitized_database_target

        print_database_target(BACKEND_ENV_FILE, get_sanitized_database_target())
        from app import models  # noqa: F401
        from app.database import Base, engine
    except Exception as exc:
        print("Database initialization failed during import.")
        print(f"Error: {exc}")
        print("Run: uv run python scripts/check_environment.py")
        return 1

    try:
        print("Creating missing database tables safely. Existing tables are not dropped.")
        before_inspector = inspect(engine)
        existing_before = set(before_inspector.get_table_names())
        Base.metadata.create_all(bind=engine)
        inspector = inspect(engine)
        existing_tables = set(inspector.get_table_names())

        for table_name in sorted(REQUIRED_TABLES):
            if table_name in existing_before:
                print(f"table exists: {table_name}")
            elif table_name in existing_tables:
                print(f"table created: {table_name}")

        missing = sorted(REQUIRED_TABLES - existing_tables)
        if missing:
            print("Initialization incomplete. Missing tables:")
            for table in missing:
                print(f"- {table}")
            return 1

        synchronize_missing_columns(engine, Base.metadata.sorted_tables)
    except Exception as exc:
        print("Database initialization failed.")
        print(f"Error: {exc}")
        print("Verify SQL Server is running, credentials are correct, and the database exists.")
        return 1

    print("Database initialization passed.")
    print("Required tables exist:")
    for table in sorted(REQUIRED_TABLES):
        print(f"- {table}")
    return 0


def print_database_target(env_file: Path, target: dict[str, str]) -> None:
    print(f"Environment file: {env_file}")
    print(f"Effective DB_SERVER: {target['DB_SERVER']}")
    print(f"Effective DB_NAME: {target['DB_NAME']}")
    print(f"Effective DB_DRIVER: {target['DB_DRIVER']}")


def synchronize_missing_columns(engine: Any, tables: list[Any]) -> None:
    inspector = inspect(engine)
    for table in tables:
        schema = resolve_schema(inspector, table.name)
        existing_columns = {
            column["name"].lower()
            for column in inspector.get_columns(table.name, schema=schema)
        }
        for column in table.columns:
            if column.name.lower() in existing_columns:
                print(f"column exists: {table.name}.{column.name}")
                continue
            add_column(engine, table.name, schema, column)
            print(f"column added: {table.name}.{column.name}")


def resolve_schema(inspector: Any, table_name: str) -> str | None:
    if table_name in inspector.get_table_names(schema="dbo"):
        return "dbo"
    return None


def add_column(engine: Any, table_name: str, schema: str | None, column: Any) -> None:
    if column.primary_key:
        raise RuntimeError(
            f"Missing primary key column {table_name}.{column.name}; refusing unsafe automatic migration."
        )

    column_sql = render_column_sql(table_name, column)
    qualified_table = render_table_name(schema, table_name)
    with engine.begin() as connection:
        connection.execute(text(f"ALTER TABLE {qualified_table} ADD {column_sql}"))


def render_column_sql(table_name: str, column: Any) -> str:
    type_sql = render_type_sql(column)
    default_sql = render_default_sql(column)
    null_sql = "NULL"
    constraint_sql = ""

    if not column.nullable and default_sql:
        null_sql = "NOT NULL"
        constraint_sql = f" CONSTRAINT {quote_identifier(default_constraint_name(table_name, column.name))} DEFAULT {default_sql} WITH VALUES"
    elif not column.nullable:
        print(
            f"warning: {table_name}.{column.name} is non-nullable in the model but has no safe default; "
            "adding as NULL to preserve existing data."
        )

    return f"{quote_identifier(column.name)} {type_sql} {null_sql}{constraint_sql}"


def render_type_sql(column: Any) -> str:
    column_type = column.type
    if isinstance(column_type, Text):
        return "NVARCHAR(MAX)"
    if isinstance(column_type, String):
        length = column_type.length or 255
        return f"NVARCHAR({length})"
    if isinstance(column_type, Boolean):
        return "BIT"
    if isinstance(column_type, Integer):
        return "INT"
    if isinstance(column_type, Float):
        return "FLOAT"
    if isinstance(column_type, Numeric):
        precision = column_type.precision or 18
        scale = column_type.scale or 2
        return f"DECIMAL({precision},{scale})"
    if isinstance(column_type, DateTime):
        return "DATETIME2"
    if isinstance(column_type, Date):
        return "DATE"
    return column_type.compile(dialect=None)


def render_default_sql(column: Any) -> str | None:
    if column.name in {"CreatedAt", "UpdatedAt", "UploadedAt", "ApprovedAt"}:
        return "SYSUTCDATETIME()"

    default = column.default.arg if column.default is not None else None
    if callable(default):
        return None
    if isinstance(column.type, Boolean):
        if default is None:
            return "0"
        return "1" if bool(default) else "0"
    if isinstance(default, str):
        return "N'" + default.replace("'", "''") + "'"
    if isinstance(default, (int, float)):
        return str(default)
    return None


def default_constraint_name(table_name: str, column_name: str) -> str:
    return f"DF_{table_name}_{column_name}"


def render_table_name(schema: str | None, table_name: str) -> str:
    if schema:
        return f"{quote_identifier(schema)}.{quote_identifier(table_name)}"
    return quote_identifier(table_name)


def quote_identifier(identifier: str) -> str:
    return "[" + identifier.replace("]", "]]") + "]"


if __name__ == "__main__":
    raise SystemExit(main())
