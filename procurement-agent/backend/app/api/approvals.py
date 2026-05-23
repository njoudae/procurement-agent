from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.exceptions import ProcurementError
from app.models import AgentAction
from app.schemas import AgentActionRead, ApprovalDecision, ApprovalQueueItem, EditApproveDecision
from app.security import require_admin
from app.services.execution_queue import enqueue_execution
from app.services.workflow_service import approve_action, edit_and_approve_action, reject_action
from app.tools.approval_tools import pending_approvals

router = APIRouter(prefix="/approvals", tags=["approvals"], dependencies=[Depends(require_admin)])


@router.get("/pending", response_model=list[ApprovalQueueItem])
def list_pending(db: Session = Depends(get_db)):
    return [ApprovalQueueItem(action=action, request=request) for action, request in pending_approvals(db)]


@router.post("/{action_id}/approve", response_model=AgentActionRead)
def approve(action_id: int, payload: ApprovalDecision, db: Session = Depends(get_db)):
    try:
        return approve_action(db, action_id, payload.admin_comment, payload.approved_by)
    except ProcurementError:
        raise


@router.post("/{action_id}/reject", response_model=AgentActionRead)
def reject(action_id: int, payload: ApprovalDecision, db: Session = Depends(get_db)):
    try:
        return reject_action(db, action_id, payload.admin_comment, payload.approved_by)
    except ProcurementError:
        raise


@router.post("/{action_id}/edit-approve", response_model=AgentActionRead)
def edit_approve(action_id: int, payload: EditApproveDecision, db: Session = Depends(get_db)):
    try:
        return edit_and_approve_action(
            db,
            action_id,
            payload.proposed_output,
            payload.admin_comment,
            payload.approved_by,
        )
    except ProcurementError:
        raise


@router.post("/{action_id}/execute", response_model=AgentActionRead)
def execute(action_id: int, db: Session = Depends(get_db)):
    try:
        enqueue_execution(action_id)
        action = db.get(AgentAction, action_id)
        if not action:
            raise HTTPException(status_code=404, detail="Approval not found")
        db.refresh(action)
        return action
    except ProcurementError:
        raise
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Execution failed; see execution logs") from exc
