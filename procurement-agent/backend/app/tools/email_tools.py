import json
import smtplib
from email.message import EmailMessage
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.idempotency import build_idempotency_key
from app.models import EmailLog, Vendor


def generate_rfq_email(vendor: Vendor, request_data: dict[str, Any]) -> dict[str, Any]:
    item = request_data.get("item_description", "requested item")
    quantity = request_data.get("quantity") or "the required quantity"
    required_date = request_data.get("required_date") or "your earliest available delivery date"
    subject = f"RFQ: {item}"
    body = (
        f"Dear {vendor.CompanyName} team,\n\n"
        "We are requesting a quotation for the following procurement need:\n\n"
        f"- Item: {item}\n"
        f"- Category: {request_data.get('category', vendor.Category)}\n"
        f"- Quantity: {quantity}\n"
        f"- Required date: {required_date}\n"
        f"- Department: {request_data.get('department') or 'Not specified'}\n\n"
        "Please include pricing, availability, delivery timeline, payment terms, and any relevant warranty details.\n\n"
        "Regards,\nProcurement Team"
    )
    return {
        "vendor_id": vendor.VendorID,
        "vendor_name": vendor.CompanyName,
        "recipient_email": vendor.Email,
        "subject": subject[:255],
        "body": body,
        "confidence_score": 0.82,
        "reasoning": f"Vendor is active, matches category '{vendor.Category}', and has rating {vendor.Rating}.",
    }


def optional_send_email_after_approval(db: Session, request_id: int, proposed_output: str, action_id: int) -> list[EmailLog]:
    settings = get_settings()
    output = json.loads(proposed_output) if isinstance(proposed_output, str) else proposed_output
    drafts = output.get("rfq_drafts", output if isinstance(output, list) else [])
    logs: list[EmailLog] = []

    for draft in drafts:
        idempotency_key = build_idempotency_key(
            "email_log",
            action_id,
            draft.get("vendor_id"),
            draft.get("recipient_email"),
            draft.get("subject"),
        )
        existing = db.scalar(select(EmailLog).where(EmailLog.IdempotencyKey == idempotency_key))
        if existing:
            logs.append(existing)
            continue

        status = "ReadyToSend"
        if settings.enable_real_email_send:
            _send_smtp_message(
                recipient=draft["recipient_email"],
                subject=draft["subject"],
                body=draft["body"],
            )
            status = "Sent"

        log = EmailLog(
            RequestID=request_id,
            ActionID=action_id,
            VendorID=draft.get("vendor_id"),
            RecipientEmail=draft["recipient_email"],
            Subject=draft["subject"],
            Body=draft["body"],
            Direction="Outbound",
            Status=status,
            IdempotencyKey=idempotency_key,
        )
        db.add(log)
        logs.append(log)

    db.commit()
    for log in logs:
        db.refresh(log)
    return logs


def _send_smtp_message(recipient: str, subject: str, body: str) -> None:
    settings = get_settings()
    if not all([settings.smtp_host, settings.smtp_user, settings.smtp_password, settings.smtp_from_email]):
        raise RuntimeError("SMTP settings are incomplete; email was not sent")

    message = EmailMessage()
    message["From"] = settings.smtp_from_email
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as server:
        server.starttls()
        server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(message)
