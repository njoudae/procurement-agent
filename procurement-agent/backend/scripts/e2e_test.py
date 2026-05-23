from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import select


BACKEND_DIR = Path(__file__).resolve().parents[1]
REQUEST_TEXT = (
    "Sarah from IT needs 12 business laptops for onboarding next month. "
    "Budget is around 18000 USD. Please request quotes from approved IT hardware vendors."
)


def main() -> int:
    sys.path.insert(0, str(BACKEND_DIR))
    load_dotenv(BACKEND_DIR / ".env")

    try:
        from app.agent import nodes
        from app.database import session_scope
        from app.models import AgentAction, EmailLog, ExecutionLog, Vendor
        from app.schemas import PurchaseRequestCreate, PurchaseRequestExtraction
        from app.services.execution_queue import enqueue_execution
        from app.services.workflow_service import approve_action, start_workflow
        from app.tools.request_tools import create_purchase_request
    except Exception as exc:
        print("E2E import failed.")
        print(f"Error: {exc}")
        print("Run first: uv run python scripts/check_environment.py")
        return 1

    class DeterministicLLMService:
        def extract_purchase_request(self, _: str) -> PurchaseRequestExtraction:
            return PurchaseRequestExtraction(
                requester_name="Sarah Ahmed",
                department="IT",
                item_description="Business laptops for onboarding",
                category="IT Hardware",
                quantity=12,
                urgency="medium",
                budget=18000,
                required_date=None,
                confidence_score=0.94,
                missing_fields=[],
            )

    try:
        with session_scope() as db:
            vendor_count = db.scalar(
                select(Vendor).where(Vendor.Category == "IT Hardware", Vendor.IsActive == True).limit(1)  # noqa: E712
            )
            if not vendor_count:
                print("E2E preflight failed: no active IT Hardware vendor found.")
                print("Run: uv run python scripts/seed_data.py")
                return 1

            request = create_purchase_request(
                db,
                PurchaseRequestCreate(
                    original_text=REQUEST_TEXT,
                    requester_name="Sarah Ahmed",
                    department="IT",
                ),
            )
            request_id = request.RequestID
            print(f"Step 1 OK: created request #{request_id}")

        nodes.LLMService = DeterministicLLMService
        state = start_workflow(request_id, REQUEST_TEXT)
        action_id = state.get("action_id")
        if not action_id:
            print("E2E failed: workflow did not create a pending approval action.")
            return 1
        print(f"Steps 2-6 OK: workflow extracted fields, searched vendors, drafted RFQs, ran guardrail, action #{action_id} pending")

        with session_scope() as db:
            action = db.get(AgentAction, action_id)
            if not action or action.Status != "PendingApproval":
                print(f"E2E failed: expected PendingApproval, got {action.Status if action else 'missing action'}.")
                return 1
            approve_action(db, action_id, "Approved by local e2e script", "local-e2e")
            print("Step 7 OK: approved action without executing it")

        enqueue_execution(action_id)
        print("Step 8 OK: executed approved action through execution queue")

        with session_scope() as db:
            action = db.get(AgentAction, action_id)
            email_logs = db.scalars(select(EmailLog).where(EmailLog.ActionID == action_id)).all()
            execution_logs = db.scalars(select(ExecutionLog).where(ExecutionLog.RequestID == request_id)).all()
            if not action or action.Status != "Executed":
                print(f"E2E failed: expected Executed action, got {action.Status if action else 'missing action'}.")
                return 1
            if not email_logs:
                print("E2E failed: no email logs were created.")
                return 1
            if not execution_logs:
                print("E2E failed: no execution logs were created.")
                return 1
            print(f"Step 9 OK: verified {len(email_logs)} email log(s) and {len(execution_logs)} execution log(s)")

    except Exception as exc:
        print("E2E workflow failed.")
        print(f"Error: {exc}")
        return 1

    print("\nE2E workflow passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
