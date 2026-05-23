from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AgentAction, DocumentExtraction, EmailLog, ExecutionLog, PurchaseRequest, RequestAttachment
from app.schemas import OverviewStats, PurchaseRequestCreate, PurchaseRequestRead, RequestDetails
from app.security import require_admin
from app.services.storage_service import store_upload
from app.services.workflow_service import start_workflow
from app.tools.attachment_tools import create_attachment_record
from app.tools.logging_tools import log_execution
from app.tools.request_tools import create_purchase_request, list_purchase_requests

router = APIRouter(prefix="/requests", tags=["requests"], dependencies=[Depends(require_admin)])


def _run_workflow_safely(request_id: int, text: str, email_body: str | None = None) -> None:
    try:
        start_workflow(request_id, text, email_body)
    except Exception as exc:
        from app.database import session_scope

        with session_scope() as db:
            request = db.get(PurchaseRequest, request_id)
            if request:
                request.Status = "Failed"
                db.commit()
            log_execution(db, request_id, "workflow", "Failed", str(exc))


@router.post("", response_model=PurchaseRequestRead)
def create_request(payload: PurchaseRequestCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    request = create_purchase_request(db, payload)
    log_execution(db, request.RequestID, "api.create_request", "Completed", "Purchase request stored")
    background_tasks.add_task(_run_workflow_safely, request.RequestID, request.OriginalText)
    return request


@router.post("/email", response_model=PurchaseRequestRead)
async def create_email_request(
    background_tasks: BackgroundTasks,
    email_body: str = Form(default=""),
    requester_name: str | None = Form(default=None),
    department: str | None = Form(default=None),
    files: list[UploadFile] = File(default=[]),
    db: Session = Depends(get_db),
):
    if not email_body.strip() and not files:
        raise HTTPException(status_code=422, detail="Provide email body text or at least one supported attachment")

    original_text = email_body.strip() or "[Attachment-only purchase request]"
    request = create_purchase_request(
        db,
        PurchaseRequestCreate(
            original_text=original_text,
            requester_name=requester_name,
            department=department,
        ),
    )

    for upload in files:
        try:
            metadata = await store_upload(request.RequestID, upload)
            create_attachment_record(db, request.RequestID, metadata)
            log_execution(db, request.RequestID, "api.store_attachment", "Completed", f"Stored {metadata['original_file_name']}")
        except Exception as exc:
            log_execution(db, request.RequestID, "api.store_attachment", "Failed", str(exc))
            request.Status = "NeedsReview"
            db.commit()

    log_execution(db, request.RequestID, "api.create_email_request", "Completed", "Email request stored")
    background_tasks.add_task(_run_workflow_safely, request.RequestID, request.OriginalText, email_body)
    return request


@router.get("", response_model=list[PurchaseRequestRead])
def get_requests(db: Session = Depends(get_db)):
    return list_purchase_requests(db)


@router.get("/overview", response_model=OverviewStats)
def get_overview(db: Session = Depends(get_db)):
    total = db.scalar(select(func.count()).select_from(PurchaseRequest)) or 0
    pending = db.scalar(select(func.count()).select_from(AgentAction).where(AgentAction.Status == "PendingApproval")) or 0
    completed = db.scalar(select(func.count()).select_from(AgentAction).where(AgentAction.Status == "Executed")) or 0
    failed = db.scalar(select(func.count()).select_from(AgentAction).where(AgentAction.Status == "Failed")) or 0
    return OverviewStats(
        total_requests=total,
        pending_approvals=pending,
        completed_actions=completed,
        failed_actions=failed,
    )


@router.get("/{request_id}", response_model=RequestDetails)
def get_request_details(request_id: int, db: Session = Depends(get_db)):
    request = db.get(PurchaseRequest, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Purchase request not found")
    actions = db.scalars(select(AgentAction).where(AgentAction.RequestID == request_id)).all()
    attachments = db.scalars(select(RequestAttachment).where(RequestAttachment.RequestID == request_id)).all()
    document_extractions = db.scalars(select(DocumentExtraction).where(DocumentExtraction.RequestID == request_id)).all()
    email_logs = db.scalars(select(EmailLog).where(EmailLog.RequestID == request_id)).all()
    execution_logs = db.scalars(
        select(ExecutionLog).where(ExecutionLog.RequestID == request_id).order_by(ExecutionLog.CreatedAt.asc())
    ).all()
    return RequestDetails(
        request=request,
        actions=list(actions),
        attachments=list(attachments),
        document_extractions=list(document_extractions),
        email_logs=list(email_logs),
        execution_logs=list(execution_logs),
    )
