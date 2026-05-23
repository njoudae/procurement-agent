import json

import pytest

from app.exceptions import ExecutionSafetyError, InvalidStatusTransitionError
from app.models import AgentAction, EmailLog, PurchaseRequest
from app.services.execution_safety import validate_execution_safety
from app.services.workflow_service import approve_action
from app.state_machine import ACTION_TRANSITIONS, validate_transition
from app.tools.email_tools import optional_send_email_after_approval
from app.tools.request_tools import create_agent_action, update_action_status


def _request(db_session):
    request = PurchaseRequest(OriginalText="Need 10 laptops for IT", Status="New")
    db_session.add(request)
    db_session.commit()
    db_session.refresh(request)
    return request


def test_invalid_status_transition_is_blocked():
    with pytest.raises(InvalidStatusTransitionError):
        validate_transition("Rejected", "Executed", ACTION_TRANSITIONS)
    with pytest.raises(InvalidStatusTransitionError):
        validate_transition("Approved", "Executed", ACTION_TRANSITIONS)


def test_duplicate_action_insert_is_idempotent(db_session):
    request = _request(db_session)
    output = {"rfq_drafts": [], "requires_admin_review": False}

    first = create_agent_action(db_session, request.RequestID, "DraftRFQEmails", output, 0.8)
    second = create_agent_action(db_session, request.RequestID, "DraftRFQEmails", output, 0.8)

    assert first.ActionID == second.ActionID


def test_duplicate_email_execution_is_prevented(db_session):
    request = _request(db_session)
    action = AgentAction(
        RequestID=request.RequestID,
        ActionType="DraftRFQEmails",
        ProposedOutput=json.dumps(
            {
                "rfq_drafts": [
                    {
                        "vendor_id": 1,
                        "recipient_email": "vendor@example.com",
                        "subject": "RFQ",
                        "body": "Please quote.",
                    }
                ]
            }
        ),
        Status="Approved",
        ConfidenceScore=0.9,
        IdempotencyKey="action-test",
    )
    db_session.add(action)
    db_session.commit()
    db_session.refresh(action)

    first = optional_send_email_after_approval(db_session, request.RequestID, action.ProposedOutput, action.ActionID)
    second = optional_send_email_after_approval(db_session, request.RequestID, action.ProposedOutput, action.ActionID)

    assert len(first) == 1
    assert len(second) == 1
    assert first[0].EmailLogID == second[0].EmailLogID


def test_approved_action_transitions_through_executing_before_executed(db_session):
    request = _request(db_session)
    action = AgentAction(
        RequestID=request.RequestID,
        ActionType="DraftRFQEmails",
        ProposedOutput="{}",
        Status="Approved",
        ConfidenceScore=0.9,
        IdempotencyKey="transition-test",
    )
    db_session.add(action)
    db_session.commit()

    executing = update_action_status(db_session, action.ActionID, "Executing")
    assert executing.Status == "Executing"
    updated = update_action_status(db_session, action.ActionID, "Executed")
    assert updated.Status == "Executed"
    with pytest.raises(InvalidStatusTransitionError):
        update_action_status(db_session, action.ActionID, "Executing")


def test_approval_does_not_execute_action(db_session):
    request = _request(db_session)
    action = AgentAction(
        RequestID=request.RequestID,
        ActionType="DraftRFQEmails",
        ProposedOutput=json.dumps(_safe_output()),
        Status="PendingApproval",
        ConfidenceScore=0.9,
        IdempotencyKey="approval-only-test",
    )
    db_session.add(action)
    db_session.commit()

    approved = approve_action(db_session, action.ActionID, "ok", "admin")

    assert approved.Status == "Approved"
    assert db_session.query(EmailLog).count() == 0


@pytest.mark.parametrize(
    "unsafe_update",
    [
        {"requires_admin_review": True},
        {"guardrail_status": "Failed"},
        {"validation_errors": ["Missing required field: category"]},
        {"field_extraction_failed": True},
        {"attachment_extraction_failed": True},
        {"document_extractions": [{"requires_review": True, "extraction_errors": ["OCR_REQUIRED"]}]},
    ],
)
def test_execution_safety_gate_rejects_unsafe_outputs(unsafe_update):
    output = _safe_output()
    output.update(unsafe_update)
    action = AgentAction(
        RequestID=1,
        ActionType="DraftRFQEmails",
        ProposedOutput=json.dumps(output),
        Status="Approved",
        ConfidenceScore=0.9,
        IdempotencyKey="unsafe-test",
    )

    with pytest.raises(ExecutionSafetyError):
        validate_execution_safety(action)


def _safe_output():
    return {
        "requires_admin_review": False,
        "guardrail_status": "Passed",
        "validation_errors": [],
        "field_extraction_failed": False,
        "attachment_extraction_failed": False,
        "document_extractions": [],
        "rfq_drafts": [
            {
                "vendor_id": 1,
                "recipient_email": "vendor@example.com",
                "subject": "RFQ",
                "body": "Please quote.",
            }
        ],
    }
