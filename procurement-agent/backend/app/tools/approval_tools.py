from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AgentAction, Approval, PurchaseRequest


def create_approval(
    db: Session,
    action_id: int,
    decision: str,
    admin_comment: str | None,
    approved_by: str | None,
) -> Approval:
    approval = Approval(
        ActionID=action_id,
        Decision=decision,
        AdminComment=admin_comment,
        ApprovedBy=approved_by,
    )
    db.add(approval)
    return approval


def pending_approvals(db: Session) -> list[tuple[AgentAction, PurchaseRequest]]:
    statement = (
        select(AgentAction, PurchaseRequest)
        .join(PurchaseRequest, AgentAction.RequestID == PurchaseRequest.RequestID)
        .where(AgentAction.Status == "PendingApproval")
        .order_by(AgentAction.CreatedAt.asc())
    )
    return list(db.execute(statement).all())
