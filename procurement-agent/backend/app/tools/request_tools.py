import json
from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.idempotency import build_idempotency_key
from app.models import AgentAction, PurchaseRequest
from app.schemas import PurchaseRequestCreate
from app.state_machine import ACTION_TRANSITIONS, REQUEST_TRANSITIONS, validate_transition


def create_purchase_request(db: Session, payload: PurchaseRequestCreate) -> PurchaseRequest:
    request = PurchaseRequest(
        RequesterName=payload.requester_name,
        Department=payload.department,
        ItemDescription=payload.item_description,
        Category=payload.category,
        Quantity=payload.quantity,
        Budget=payload.budget,
        Urgency=payload.urgency.value if payload.urgency else None,
        RequiredDate=payload.required_date,
        OriginalText=payload.original_text,
        Status="New",
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return request


def update_request_extraction(db: Session, request_id: int, data: dict[str, Any], status: str) -> PurchaseRequest:
    request = db.get(PurchaseRequest, request_id)
    if not request:
        raise ValueError(f"Purchase request {request_id} not found")

    required_date_value = data.get("required_date")
    parsed_date = None
    if required_date_value:
        try:
            parsed_date = date.fromisoformat(required_date_value)
        except ValueError:
            parsed_date = None

    request.RequesterName = data.get("requester_name") or request.RequesterName
    request.Department = data.get("department") or request.Department
    request.ItemDescription = data.get("item_description") or request.ItemDescription
    request.Category = data.get("category") or request.Category
    request.Quantity = data.get("quantity") or request.Quantity
    request.Budget = data.get("budget") or request.Budget
    request.Urgency = data.get("urgency") or request.Urgency
    request.RequiredDate = parsed_date or request.RequiredDate
    validate_transition(request.Status, status, REQUEST_TRANSITIONS)
    request.Status = status
    db.commit()
    db.refresh(request)
    return request


def list_purchase_requests(db: Session) -> list[PurchaseRequest]:
    return list(db.scalars(select(PurchaseRequest).order_by(PurchaseRequest.CreatedAt.desc())).all())


def create_agent_action(
    db: Session,
    request_id: int,
    action_type: str,
    proposed_output: dict[str, Any] | list[Any],
    confidence_score: float,
) -> AgentAction:
    proposed_json = json.dumps(proposed_output, indent=2, default=str)
    idempotency_key = build_idempotency_key("agent_action", request_id, action_type, proposed_output)
    existing = db.scalar(select(AgentAction).where(AgentAction.IdempotencyKey == idempotency_key))
    if existing:
        return existing

    action = AgentAction(
        RequestID=request_id,
        ActionType=action_type,
        ProposedOutput=proposed_json,
        Status="PendingApproval",
        ConfidenceScore=confidence_score,
        IdempotencyKey=idempotency_key,
    )
    db.add(action)
    request = db.get(PurchaseRequest, request_id)
    if request:
        requires_review = False
        if isinstance(proposed_output, dict):
            requires_review = bool(
                proposed_output.get("requires_admin_review")
                or proposed_output.get("validation_errors")
                or proposed_output.get("errors")
                or proposed_output.get("conflicts")
            )
        target_status = "NeedsReview" if requires_review else "PendingApproval"
        validate_transition(request.Status, target_status, REQUEST_TRANSITIONS)
        request.Status = target_status
    db.commit()
    db.refresh(action)
    return action


def update_action_status(db: Session, action_id: int, status: str) -> AgentAction | None:
    action = db.get(AgentAction, action_id)
    if not action:
        return None
    validate_transition(action.Status, status, ACTION_TRANSITIONS)
    action.Status = status
    db.commit()
    db.refresh(action)
    return action
