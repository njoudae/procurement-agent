from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Vendor(Base):
    __tablename__ = "Vendors"

    VendorID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    CompanyName: Mapped[str] = mapped_column(String(255), nullable=False)
    Category: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    Department: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    Email: Mapped[str] = mapped_column(String(255), nullable=False)
    Phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    Rating: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    IsActive: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    CreatedAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    UpdatedAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    email_logs: Mapped[list["EmailLog"]] = relationship(back_populates="vendor")


class PurchaseRequest(Base):
    __tablename__ = "PurchaseRequests"

    RequestID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    RequesterName: Mapped[str | None] = mapped_column(String(255), nullable=True)
    Department: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    ItemDescription: Mapped[str | None] = mapped_column(Text, nullable=True)
    Category: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    Quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    Budget: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    Urgency: Mapped[str | None] = mapped_column(String(20), nullable=True)
    RequiredDate: Mapped[date | None] = mapped_column(Date, nullable=True)
    OriginalText: Mapped[str] = mapped_column(Text, nullable=False)
    Status: Mapped[str] = mapped_column(String(40), default="New", nullable=False, index=True)
    CreatedAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    UpdatedAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    actions: Mapped[list["AgentAction"]] = relationship(back_populates="request")
    attachments: Mapped[list["RequestAttachment"]] = relationship(back_populates="request")
    document_extractions: Mapped[list["DocumentExtraction"]] = relationship(back_populates="request")
    email_logs: Mapped[list["EmailLog"]] = relationship(back_populates="request")
    execution_logs: Mapped[list["ExecutionLog"]] = relationship(back_populates="request")


class AgentAction(Base):
    __tablename__ = "AgentActions"

    ActionID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    RequestID: Mapped[int] = mapped_column(ForeignKey("PurchaseRequests.RequestID"), nullable=False, index=True)
    ActionType: Mapped[str] = mapped_column(String(80), nullable=False)
    ProposedOutput: Mapped[str] = mapped_column(Text, nullable=False)
    Status: Mapped[str] = mapped_column(String(40), default="PendingApproval", nullable=False, index=True)
    ConfidenceScore: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    IdempotencyKey: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    CreatedAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    UpdatedAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    request: Mapped[PurchaseRequest] = relationship(back_populates="actions")
    approvals: Mapped[list["Approval"]] = relationship(back_populates="action")


class RequestAttachment(Base):
    __tablename__ = "RequestAttachments"

    AttachmentID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    RequestID: Mapped[int] = mapped_column(ForeignKey("PurchaseRequests.RequestID"), nullable=False, index=True)
    OriginalFileName: Mapped[str] = mapped_column(String(255), nullable=False)
    StoredFileName: Mapped[str] = mapped_column(String(255), nullable=False)
    StoredPath: Mapped[str] = mapped_column(String(1000), nullable=False)
    MimeType: Mapped[str] = mapped_column(String(255), nullable=False)
    FileSize: Mapped[int] = mapped_column(Integer, nullable=False)
    FileHash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    SourceType: Mapped[str] = mapped_column(String(40), nullable=False)
    ExtractionStatus: Mapped[str] = mapped_column(String(40), default="Pending", nullable=False)
    UploadedAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    UpdatedAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    request: Mapped[PurchaseRequest] = relationship(back_populates="attachments")
    extraction: Mapped["DocumentExtraction | None"] = relationship(back_populates="attachment", uselist=False)


class DocumentExtraction(Base):
    __tablename__ = "DocumentExtractions"

    ExtractionID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    RequestID: Mapped[int] = mapped_column(ForeignKey("PurchaseRequests.RequestID"), nullable=False, index=True)
    AttachmentID: Mapped[int | None] = mapped_column(ForeignKey("RequestAttachments.AttachmentID"), nullable=True, index=True)
    SourceType: Mapped[str] = mapped_column(String(40), nullable=False)
    SourceFile: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ExtractedText: Mapped[str | None] = mapped_column(Text, nullable=True)
    ExtractedTables: Mapped[str | None] = mapped_column(Text, nullable=True)
    StructuredData: Mapped[str | None] = mapped_column(Text, nullable=True)
    ExtractionConfidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    ExtractionErrors: Mapped[str | None] = mapped_column(Text, nullable=True)
    RequiresReview: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    CreatedAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    UpdatedAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    request: Mapped[PurchaseRequest] = relationship(back_populates="document_extractions")
    attachment: Mapped[RequestAttachment | None] = relationship(back_populates="extraction")


class Approval(Base):
    __tablename__ = "Approvals"

    ApprovalID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ActionID: Mapped[int] = mapped_column(ForeignKey("AgentActions.ActionID"), nullable=False, index=True)
    Decision: Mapped[str] = mapped_column(String(40), nullable=False)
    AdminComment: Mapped[str | None] = mapped_column(Text, nullable=True)
    ApprovedBy: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ApprovedAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    action: Mapped[AgentAction] = relationship(back_populates="approvals")


class EmailLog(Base):
    __tablename__ = "EmailLogs"

    EmailLogID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    RequestID: Mapped[int] = mapped_column(ForeignKey("PurchaseRequests.RequestID"), nullable=False, index=True)
    ActionID: Mapped[int | None] = mapped_column(ForeignKey("AgentActions.ActionID"), nullable=True, index=True)
    VendorID: Mapped[int | None] = mapped_column(ForeignKey("Vendors.VendorID"), nullable=True, index=True)
    RecipientEmail: Mapped[str] = mapped_column(String(255), nullable=False)
    Subject: Mapped[str] = mapped_column(String(255), nullable=False)
    Body: Mapped[str] = mapped_column(Text, nullable=False)
    Direction: Mapped[str] = mapped_column(String(20), default="Outbound", nullable=False)
    Status: Mapped[str] = mapped_column(String(40), nullable=False)
    IdempotencyKey: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    CreatedAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    UpdatedAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    request: Mapped[PurchaseRequest] = relationship(back_populates="email_logs")
    vendor: Mapped[Vendor | None] = relationship(back_populates="email_logs")


class ExecutionLog(Base):
    __tablename__ = "ExecutionLogs"

    LogID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    RequestID: Mapped[int | None] = mapped_column(ForeignKey("PurchaseRequests.RequestID"), nullable=True, index=True)
    NodeName: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    Status: Mapped[str] = mapped_column(String(40), nullable=False)
    Message: Mapped[str] = mapped_column(Text, nullable=False)
    LatencyMs: Mapped[float | None] = mapped_column(Float, nullable=True)
    LlmPromptTokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    LlmCompletionTokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    LlmCostUsd: Mapped[float | None] = mapped_column(Float, nullable=True)
    CreatedAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    UpdatedAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    request: Mapped[PurchaseRequest | None] = relationship(back_populates="execution_logs")
