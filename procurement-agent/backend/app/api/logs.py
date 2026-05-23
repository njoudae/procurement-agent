from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ExecutionLog
from app.schemas import ExecutionLogRead
from app.security import require_admin

router = APIRouter(prefix="/logs", tags=["logs"], dependencies=[Depends(require_admin)])


@router.get("/{request_id}", response_model=list[ExecutionLogRead])
def get_logs(request_id: int, db: Session = Depends(get_db)):
    logs = db.scalars(
        select(ExecutionLog).where(ExecutionLog.RequestID == request_id).order_by(ExecutionLog.CreatedAt.asc())
    ).all()
    return list(logs)
