from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import RequestAttachment


def create_attachment_record(db: Session, request_id: int, metadata: dict[str, object]) -> RequestAttachment:
    attachment = RequestAttachment(
        RequestID=request_id,
        OriginalFileName=str(metadata["original_file_name"]),
        StoredFileName=str(metadata["stored_file_name"]),
        StoredPath=str(metadata["stored_path"]),
        MimeType=str(metadata["mime_type"]),
        FileSize=int(metadata["file_size"]),
        FileHash=str(metadata["file_hash"]),
        SourceType=str(metadata["source_type"]),
        ExtractionStatus="Pending",
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return attachment


def list_attachments(db: Session, request_id: int) -> list[RequestAttachment]:
    return list(
        db.scalars(
            select(RequestAttachment).where(RequestAttachment.RequestID == request_id).order_by(RequestAttachment.UploadedAt.asc())
        ).all()
    )
