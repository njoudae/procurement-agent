from datetime import date, datetime
from enum import Enum
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator


EmailAddress = Annotated[str, StringConstraints(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")]


class Urgency(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class RequestStatus(str, Enum):
    new = "New"
    processing = "Processing"
    needs_review = "NeedsReview"
    pending_approval = "PendingApproval"
    approved = "Approved"
    rejected = "Rejected"
    completed = "Completed"
    failed = "Failed"


class ActionStatus(str, Enum):
    pending_approval = "PendingApproval"
    approved = "Approved"
    executing = "Executing"
    rejected = "Rejected"
    executed = "Executed"
    failed = "Failed"


class PurchaseRequestExtraction(BaseModel):
    requester_name: str | None = None
    department: str | None = None
    item_description: str
    category: str
    quantity: int | None = Field(default=None, ge=1)
    urgency: Urgency = Urgency.medium
    budget: float | None = Field(default=None, ge=0)
    required_date: str | None = None
    confidence_score: float = Field(ge=0, le=1)
    missing_fields: list[str] = Field(default_factory=list)
    field_sources: dict[str, dict[str, Any]] = Field(default_factory=dict)

    @field_validator("item_description", "category")
    @classmethod
    def required_text(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("field must not be empty")
        return value.strip()


class RFQDraft(BaseModel):
    vendor_id: int
    vendor_name: str
    recipient_email: EmailAddress
    subject: str
    body: str
    confidence_score: float = Field(ge=0, le=1)
    reasoning: str


class PurchaseRequestCreate(BaseModel):
    original_text: str = Field(min_length=10)
    requester_name: str | None = None
    department: str | None = None
    item_description: str | None = None
    category: str | None = None
    quantity: int | None = Field(default=None, ge=1)
    budget: float | None = Field(default=None, ge=0)
    urgency: Urgency | None = None
    required_date: date | None = None


class PurchaseRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    RequestID: int
    RequesterName: str | None
    Department: str | None
    ItemDescription: str | None
    Category: str | None
    Quantity: int | None
    Budget: float | None
    Urgency: str | None
    RequiredDate: date | None
    OriginalText: str
    Status: str
    CreatedAt: datetime
    UpdatedAt: datetime


class VendorCreate(BaseModel):
    company_name: str = Field(min_length=2)
    category: str = Field(min_length=2)
    department: str | None = None
    email: EmailAddress
    phone: str | None = None
    rating: float = Field(default=0, ge=0, le=5)
    is_active: bool = True


class VendorUpdate(BaseModel):
    company_name: str | None = Field(default=None, min_length=2)
    category: str | None = Field(default=None, min_length=2)
    department: str | None = None
    email: EmailAddress | None = None
    phone: str | None = None
    rating: float | None = Field(default=None, ge=0, le=5)
    is_active: bool | None = None


class VendorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    VendorID: int
    CompanyName: str
    Category: str
    Department: str | None
    Email: EmailAddress
    Phone: str | None
    Rating: float
    IsActive: bool
    CreatedAt: datetime
    UpdatedAt: datetime


class AgentActionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ActionID: int
    RequestID: int
    ActionType: str
    ProposedOutput: str
    Status: str
    ConfidenceScore: float
    IdempotencyKey: str
    CreatedAt: datetime
    UpdatedAt: datetime


class ApprovalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ApprovalID: int
    ActionID: int
    Decision: str
    AdminComment: str | None
    ApprovedBy: str | None
    ApprovedAt: datetime


class ApprovalDecision(BaseModel):
    admin_comment: str | None = None
    approved_by: str | None = "admin"


class EditApproveDecision(ApprovalDecision):
    proposed_output: dict[str, Any] | list[Any] | str


class EmailLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    EmailLogID: int
    RequestID: int
    ActionID: int | None
    VendorID: int | None
    RecipientEmail: EmailAddress
    Subject: str
    Body: str
    Direction: str
    Status: str
    IdempotencyKey: str
    CreatedAt: datetime
    UpdatedAt: datetime


class ExecutionLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    LogID: int
    RequestID: int | None
    NodeName: str
    Status: str
    Message: str
    LatencyMs: float | None
    LlmPromptTokens: int | None
    LlmCompletionTokens: int | None
    LlmCostUsd: float | None
    CreatedAt: datetime
    UpdatedAt: datetime


class AttachmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    AttachmentID: int
    RequestID: int
    OriginalFileName: str
    MimeType: str
    FileSize: int
    SourceType: str
    ExtractionStatus: str
    UploadedAt: datetime
    UpdatedAt: datetime


class DocumentExtractionResult(BaseModel):
    source_type: str
    extracted_text: str = ""
    extracted_tables: list[list[dict[str, Any]]] = Field(default_factory=list)
    detected_vendor_name: str | None = None
    detected_quotation_number: str | None = None
    detected_total_amount: float | None = None
    detected_delivery_date: str | None = None
    detected_validity_period: str | None = None
    extracted_items: list[dict[str, Any]] = Field(default_factory=list)
    extracted_prices: list[dict[str, Any]] = Field(default_factory=list)
    extraction_confidence: float = Field(default=0, ge=0, le=1)
    extraction_errors: list[str] = Field(default_factory=list)
    requires_review: bool = False
    source_file: str | None = None


class DocumentExtractionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ExtractionID: int
    RequestID: int
    AttachmentID: int | None
    SourceType: str
    SourceFile: str | None
    ExtractedText: str | None
    ExtractedTables: str | None
    StructuredData: str | None
    ExtractionConfidence: float
    ExtractionErrors: str | None
    RequiresReview: bool
    CreatedAt: datetime
    UpdatedAt: datetime


class RequestDetails(BaseModel):
    request: PurchaseRequestRead
    actions: list[AgentActionRead]
    attachments: list[AttachmentRead]
    document_extractions: list[DocumentExtractionRead]
    email_logs: list[EmailLogRead]
    execution_logs: list[ExecutionLogRead]


class OverviewStats(BaseModel):
    total_requests: int
    pending_approvals: int
    completed_actions: int
    failed_actions: int


class ApprovalQueueItem(BaseModel):
    action: AgentActionRead
    request: PurchaseRequestRead


class StatusResponse(BaseModel):
    status: Literal["ok"]
    message: str
