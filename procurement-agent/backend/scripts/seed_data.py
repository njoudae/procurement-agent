from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import select


BACKEND_DIR = Path(__file__).resolve().parents[1]

SEED_VENDORS = [
    {
        "CompanyName": "Example Nexus IT Supply",
        "Category": "IT Hardware",
        "Department": "IT",
        "Email": "rfq-it@example.com",
        "Phone": "+1-555-0101",
        "Rating": 4.8,
        "IsActive": True,
    },
    {
        "CompanyName": "Example BrightOffice Solutions",
        "Category": "Office Supplies",
        "Department": "Operations",
        "Email": "rfq-office@example.com",
        "Phone": "+1-555-0102",
        "Rating": 4.4,
        "IsActive": True,
    },
    {
        "CompanyName": "Example CloudWorks Licensing",
        "Category": "Software",
        "Department": "IT",
        "Email": "rfq-software@example.com",
        "Phone": "+1-555-0103",
        "Rating": 4.6,
        "IsActive": True,
    },
]

SAMPLE_REQUEST_TEXT = (
    "Sarah from IT needs 12 business laptops for onboarding next month. "
    "Budget is around 18000 USD. Please request quotes from approved IT hardware vendors."
)


def main() -> int:
    sys.path.insert(0, str(BACKEND_DIR))
    load_dotenv(BACKEND_DIR / ".env")

    try:
        from app.config import BACKEND_ENV_FILE, get_sanitized_database_target

        print_database_target(BACKEND_ENV_FILE, get_sanitized_database_target())
        from app.database import session_scope
        from app.models import PurchaseRequest, Vendor, utc_now
    except Exception as exc:
        print("Seed import failed.")
        print(f"Error: {exc}")
        print("Run first: uv run python scripts/check_environment.py")
        return 1

    try:
        with session_scope() as db:
            inserted_vendors = 0
            for seed in SEED_VENDORS:
                existing = db.scalar(select(Vendor).where(Vendor.CompanyName == seed["CompanyName"]))
                if existing:
                    continue
                now = utc_now()
                db.add(Vendor(**seed, CreatedAt=now, UpdatedAt=now))
                inserted_vendors += 1

            existing_request = db.scalar(select(PurchaseRequest).where(PurchaseRequest.OriginalText == SAMPLE_REQUEST_TEXT))
            if not existing_request:
                now = utc_now()
                db.add(
                    PurchaseRequest(
                        RequesterName="Sarah Ahmed",
                        Department="IT",
                        ItemDescription="Business laptops for onboarding",
                        Category="IT Hardware",
                        Quantity=12,
                        Budget=18000.00,
                        Urgency="medium",
                        OriginalText=SAMPLE_REQUEST_TEXT,
                        Status="New",
                        CreatedAt=now,
                        UpdatedAt=now,
                    )
                )
                inserted_request = True
            else:
                inserted_request = False
    except Exception as exc:
        print("Seed data failed.")
        print(f"Error: {exc}")
        print("Verify tables exist with: uv run python scripts/init_db.py")
        return 1

    print("Seed data completed safely.")
    print(f"Inserted vendors: {inserted_vendors}")
    print(f"Inserted sample purchase request: {'yes' if inserted_request else 'already existed'}")
    return 0


def print_database_target(env_file: Path, target: dict[str, str]) -> None:
    print(f"Environment file: {env_file}")
    print(f"Effective DB_SERVER: {target['DB_SERVER']}")
    print(f"Effective DB_NAME: {target['DB_NAME']}")
    print(f"Effective DB_DRIVER: {target['DB_DRIVER']}")


if __name__ == "__main__":
    raise SystemExit(main())
