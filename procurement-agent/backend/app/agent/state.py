from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    request_id: int
    original_request_text: str
    email_body: str
    input_source: str
    has_email_text: bool
    has_attachments: bool
    attachments: list[dict[str, Any]]
    document_extractions: list[dict[str, Any]]
    merged_context: str
    source_traceability: dict[str, dict[str, Any]]
    conflicts: list[dict[str, Any]]
    requires_admin_review: bool
    attachment_extraction_failed: bool
    field_extraction_failed: bool
    validation_status: str
    vendor_search_status: str
    vendor_selection_status: str
    guardrail_status: str
    extracted_fields: dict[str, Any]
    validation_errors: list[str]
    matched_vendors: list[dict[str, Any]]
    selected_vendors: list[dict[str, Any]]
    proposed_emails: list[dict[str, Any]]
    approval_status: str
    admin_feedback: str | None
    execution_status: str
    errors: list[str]
    logs: list[str]
    action_id: int | None
