import hashlib
import mimetypes
import re
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.config import get_settings


ALLOWED_EXTENSIONS = {
    ".pdf": "pdf",
    ".xlsx": "excel",
    ".xls": "excel",
    ".csv": "csv",
    ".docx": "docx",
    ".txt": "txt",
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
}

ALLOWED_MIME_PREFIXES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
    "text/csv",
    "text/plain",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "image/png",
    "image/jpeg",
}

EXECUTABLE_EXTENSIONS = {
    ".exe",
    ".bat",
    ".cmd",
    ".com",
    ".dll",
    ".js",
    ".msi",
    ".ps1",
    ".scr",
    ".sh",
    ".vbs",
    ".zip",
    ".rar",
    ".7z",
}


def sanitize_filename(filename: str) -> str:
    base = Path(filename or "attachment").name
    clean = re.sub(r"[^A-Za-z0-9._-]", "_", base)
    return clean[:180] or "attachment"


def classify_file(filename: str, mime_type: str | None) -> str:
    extension = Path(filename).suffix.lower()
    if extension in EXECUTABLE_EXTENSIONS:
        raise ValueError("Executable or archive attachments are not accepted")
    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {extension or 'missing extension'}")
    if mime_type and mime_type not in ALLOWED_MIME_PREFIXES:
        guessed, _ = mimetypes.guess_type(filename)
        if guessed not in ALLOWED_MIME_PREFIXES:
            raise ValueError(f"Unsupported MIME type: {mime_type}")
    return ALLOWED_EXTENSIONS[extension]


async def store_upload(request_id: int, upload: UploadFile) -> dict[str, object]:
    settings = get_settings()
    safe_name = sanitize_filename(upload.filename or "attachment")
    source_type = classify_file(safe_name, upload.content_type)

    data = await upload.read()
    if not data:
        raise ValueError(f"Attachment {safe_name} is empty")
    if len(data) > settings.max_upload_bytes:
        raise ValueError(f"Attachment {safe_name} exceeds max size of {settings.max_upload_bytes} bytes")

    digest = hashlib.sha256(data).hexdigest()
    storage_dir = Path(settings.upload_storage_dir).resolve() / str(request_id)
    storage_dir.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid4().hex}_{safe_name}"
    stored_path = (storage_dir / stored_name).resolve()
    if storage_dir not in stored_path.parents:
        raise ValueError("Unsafe upload path rejected")

    stored_path.write_bytes(data)
    return {
        "original_file_name": safe_name,
        "stored_file_name": stored_name,
        "stored_path": str(stored_path),
        "mime_type": upload.content_type or mimetypes.guess_type(safe_name)[0] or "application/octet-stream",
        "file_size": len(data),
        "file_hash": digest,
        "source_type": source_type,
    }
