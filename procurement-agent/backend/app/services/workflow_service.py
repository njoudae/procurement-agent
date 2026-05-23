import json
from typing import Any

from sqlalchemy.orm import Session

from app.agent.graph import procurement_graph
from app.decorators import measure_latency
from app.exceptions import InvalidStatusTransitionError, NotFoundError
from app.models import AgentAction, PurchaseRequest
from app.state_machine import ACTION_TRANSITIONS, REQUEST_TRANSITIONS, validate_transition
from app.tools.approval_tools import create_approval
from app.tools.logging_tools import log_execution


@measure_latency
def start_workflow(request_id: int, original_request_text: str, email_body: str | None = None) -> dict[str, Any]:
    state = {
        "request_id": request_id,
        "original_request_text": original_request_text,
        "email_body": email_body if email_body is not None else original_request_text,
        "input_source": "unknown",
        "has_email_text": bool((email_body if email_body is not None else original_request_text).strip()),
        "has_attachments": False,
        "attachments": [],
        "document_extractions": [],
        "merged_context": "",
        "source_traceability": {},
        "conflicts": [],
        "requires_admin_review": False,
        "attachment_extraction_failed": False,
        "field_extraction_failed": False,
        "validation_status": "NotStarted",
        "vendor_search_status": "NotStarted",
        "vendor_selection_status": "NotStarted",
        "guardrail_status": "NotStarted",
        "validation_errors": [],
        "matched_vendors": [],
        "selected_vendors": [],
        "proposed_emails": [],
        "approval_status": "NotCreated",
        "execution_status": "NotStarted",
        "errors": [],
        "logs": [],
    }
    return procurement_graph.invoke(state)


def approve_action(db: Session, action_id: int, admin_comment: str | None, approved_by: str | None) -> AgentAction:
    action = db.get(AgentAction, action_id)
    if not action:
        raise NotFoundError("Approval not found")
    if action.Status != "PendingApproval":
        raise InvalidStatusTransitionError(f"Action cannot be approved from status {action.Status}")
    validate_transition(action.Status, "Approved", ACTION_TRANSITIONS)
    action.Status = "Approved"
    create_approval(db, action_id, "Approved", admin_comment, approved_by)
    db.commit()
    db.refresh(action)
    log_execution(db, action.RequestID, "approval", "Approved", f"Action {action_id} approved")
    return action


def reject_action(db: Session, action_id: int, admin_comment: str | None, approved_by: str | None) -> AgentAction:
    action = db.get(AgentAction, action_id)
    if not action:
        raise NotFoundError("Approval not found")
    if action.Status != "PendingApproval":
        raise InvalidStatusTransitionError(f"Action cannot be rejected from status {action.Status}")
    validate_transition(action.Status, "Rejected", ACTION_TRANSITIONS)
    action.Status = "Rejected"
    request = db.get(PurchaseRequest, action.RequestID)
    if request:
        validate_transition(request.Status, "Rejected", REQUEST_TRANSITIONS)
        request.Status = "Rejected"
    create_approval(db, action_id, "Rejected", admin_comment, approved_by)
    db.commit()
    db.refresh(action)
    log_execution(db, action.RequestID, "approval", "Rejected", f"Action {action_id} rejected")
    return action


def edit_and_approve_action(
    db: Session,
    action_id: int,
    proposed_output: dict[str, Any] | list[Any] | str,
    admin_comment: str | None,
    approved_by: str | None,
) -> AgentAction:
    action = db.get(AgentAction, action_id)
    if not action:
        raise NotFoundError("Approval not found")
    if action.Status != "PendingApproval":
        raise InvalidStatusTransitionError(f"Action cannot be edited from status {action.Status}")
    if isinstance(proposed_output, str):
        json.loads(proposed_output)
        action.ProposedOutput = proposed_output
    else:
        action.ProposedOutput = json.dumps(proposed_output, indent=2, default=str)
    validate_transition(action.Status, "Approved", ACTION_TRANSITIONS)
    action.Status = "Approved"
    create_approval(db, action_id, "EditedApproved", admin_comment, approved_by)
    db.commit()
    db.refresh(action)
    log_execution(db, action.RequestID, "approval", "Approved", f"Action {action_id} edited and approved")
    return action
