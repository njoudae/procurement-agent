IF DB_ID(N'ProcurementAgent') IS NULL
BEGIN
    CREATE DATABASE ProcurementAgent;
END
GO

USE ProcurementAgent;
GO

IF OBJECT_ID(N'dbo.EmailLogs', N'U') IS NOT NULL DROP TABLE dbo.EmailLogs;
IF OBJECT_ID(N'dbo.ExecutionLogs', N'U') IS NOT NULL DROP TABLE dbo.ExecutionLogs;
IF OBJECT_ID(N'dbo.DocumentExtractions', N'U') IS NOT NULL DROP TABLE dbo.DocumentExtractions;
IF OBJECT_ID(N'dbo.RequestAttachments', N'U') IS NOT NULL DROP TABLE dbo.RequestAttachments;
IF OBJECT_ID(N'dbo.Approvals', N'U') IS NOT NULL DROP TABLE dbo.Approvals;
IF OBJECT_ID(N'dbo.AgentActions', N'U') IS NOT NULL DROP TABLE dbo.AgentActions;
IF OBJECT_ID(N'dbo.PurchaseRequests', N'U') IS NOT NULL DROP TABLE dbo.PurchaseRequests;
IF OBJECT_ID(N'dbo.Vendors', N'U') IS NOT NULL DROP TABLE dbo.Vendors;
GO

CREATE TABLE dbo.Vendors (
    VendorID INT IDENTITY(1,1) PRIMARY KEY,
    CompanyName NVARCHAR(255) NOT NULL,
    Category NVARCHAR(120) NOT NULL,
    Department NVARCHAR(120) NULL,
    Email NVARCHAR(255) NOT NULL,
    Phone NVARCHAR(50) NULL,
    Rating FLOAT NOT NULL CONSTRAINT DF_Vendors_Rating DEFAULT 0,
    IsActive BIT NOT NULL CONSTRAINT DF_Vendors_IsActive DEFAULT 1,
    CreatedAt DATETIME2 NOT NULL CONSTRAINT DF_Vendors_CreatedAt DEFAULT SYSUTCDATETIME(),
    UpdatedAt DATETIME2 NOT NULL CONSTRAINT DF_Vendors_UpdatedAt DEFAULT SYSUTCDATETIME()
);

CREATE TABLE dbo.PurchaseRequests (
    RequestID INT IDENTITY(1,1) PRIMARY KEY,
    RequesterName NVARCHAR(255) NULL,
    Department NVARCHAR(120) NULL,
    ItemDescription NVARCHAR(MAX) NULL,
    Category NVARCHAR(120) NULL,
    Quantity INT NULL,
    Budget DECIMAL(18,2) NULL,
    Urgency NVARCHAR(20) NULL,
    RequiredDate DATE NULL,
    OriginalText NVARCHAR(MAX) NOT NULL,
    Status NVARCHAR(40) NOT NULL CONSTRAINT DF_PurchaseRequests_Status DEFAULT 'New',
    CreatedAt DATETIME2 NOT NULL CONSTRAINT DF_PurchaseRequests_CreatedAt DEFAULT SYSUTCDATETIME(),
    UpdatedAt DATETIME2 NOT NULL CONSTRAINT DF_PurchaseRequests_UpdatedAt DEFAULT SYSUTCDATETIME()
);

CREATE TABLE dbo.AgentActions (
    ActionID INT IDENTITY(1,1) PRIMARY KEY,
    RequestID INT NOT NULL,
    ActionType NVARCHAR(80) NOT NULL,
    ProposedOutput NVARCHAR(MAX) NOT NULL,
    Status NVARCHAR(40) NOT NULL CONSTRAINT DF_AgentActions_Status DEFAULT 'PendingApproval',
    ConfidenceScore FLOAT NOT NULL CONSTRAINT DF_AgentActions_Confidence DEFAULT 0,
    IdempotencyKey NVARCHAR(128) NOT NULL,
    CreatedAt DATETIME2 NOT NULL CONSTRAINT DF_AgentActions_CreatedAt DEFAULT SYSUTCDATETIME(),
    UpdatedAt DATETIME2 NOT NULL CONSTRAINT DF_AgentActions_UpdatedAt DEFAULT SYSUTCDATETIME(),
    CONSTRAINT FK_AgentActions_PurchaseRequests FOREIGN KEY (RequestID) REFERENCES dbo.PurchaseRequests(RequestID)
);

CREATE TABLE dbo.RequestAttachments (
    AttachmentID INT IDENTITY(1,1) PRIMARY KEY,
    RequestID INT NOT NULL,
    OriginalFileName NVARCHAR(255) NOT NULL,
    StoredFileName NVARCHAR(255) NOT NULL,
    StoredPath NVARCHAR(1000) NOT NULL,
    MimeType NVARCHAR(255) NOT NULL,
    FileSize INT NOT NULL,
    FileHash NVARCHAR(128) NOT NULL,
    SourceType NVARCHAR(40) NOT NULL,
    ExtractionStatus NVARCHAR(40) NOT NULL CONSTRAINT DF_RequestAttachments_Status DEFAULT 'Pending',
    UploadedAt DATETIME2 NOT NULL CONSTRAINT DF_RequestAttachments_UploadedAt DEFAULT SYSUTCDATETIME(),
    UpdatedAt DATETIME2 NOT NULL CONSTRAINT DF_RequestAttachments_UpdatedAt DEFAULT SYSUTCDATETIME(),
    CONSTRAINT FK_RequestAttachments_PurchaseRequests FOREIGN KEY (RequestID) REFERENCES dbo.PurchaseRequests(RequestID)
);

CREATE TABLE dbo.DocumentExtractions (
    ExtractionID INT IDENTITY(1,1) PRIMARY KEY,
    RequestID INT NOT NULL,
    AttachmentID INT NULL,
    SourceType NVARCHAR(40) NOT NULL,
    SourceFile NVARCHAR(255) NULL,
    ExtractedText NVARCHAR(MAX) NULL,
    ExtractedTables NVARCHAR(MAX) NULL,
    StructuredData NVARCHAR(MAX) NULL,
    ExtractionConfidence FLOAT NOT NULL CONSTRAINT DF_DocumentExtractions_Confidence DEFAULT 0,
    ExtractionErrors NVARCHAR(MAX) NULL,
    RequiresReview BIT NOT NULL CONSTRAINT DF_DocumentExtractions_RequiresReview DEFAULT 0,
    CreatedAt DATETIME2 NOT NULL CONSTRAINT DF_DocumentExtractions_CreatedAt DEFAULT SYSUTCDATETIME(),
    UpdatedAt DATETIME2 NOT NULL CONSTRAINT DF_DocumentExtractions_UpdatedAt DEFAULT SYSUTCDATETIME(),
    CONSTRAINT FK_DocumentExtractions_PurchaseRequests FOREIGN KEY (RequestID) REFERENCES dbo.PurchaseRequests(RequestID),
    CONSTRAINT FK_DocumentExtractions_RequestAttachments FOREIGN KEY (AttachmentID) REFERENCES dbo.RequestAttachments(AttachmentID)
);

CREATE TABLE dbo.Approvals (
    ApprovalID INT IDENTITY(1,1) PRIMARY KEY,
    ActionID INT NOT NULL,
    Decision NVARCHAR(40) NOT NULL,
    AdminComment NVARCHAR(MAX) NULL,
    ApprovedBy NVARCHAR(255) NULL,
    ApprovedAt DATETIME2 NOT NULL CONSTRAINT DF_Approvals_ApprovedAt DEFAULT SYSUTCDATETIME(),
    CONSTRAINT FK_Approvals_AgentActions FOREIGN KEY (ActionID) REFERENCES dbo.AgentActions(ActionID)
);

CREATE TABLE dbo.EmailLogs (
    EmailLogID INT IDENTITY(1,1) PRIMARY KEY,
    RequestID INT NOT NULL,
    ActionID INT NULL,
    VendorID INT NULL,
    RecipientEmail NVARCHAR(255) NOT NULL,
    Subject NVARCHAR(255) NOT NULL,
    Body NVARCHAR(MAX) NOT NULL,
    Direction NVARCHAR(20) NOT NULL,
    Status NVARCHAR(40) NOT NULL,
    IdempotencyKey NVARCHAR(128) NOT NULL,
    CreatedAt DATETIME2 NOT NULL CONSTRAINT DF_EmailLogs_CreatedAt DEFAULT SYSUTCDATETIME(),
    UpdatedAt DATETIME2 NOT NULL CONSTRAINT DF_EmailLogs_UpdatedAt DEFAULT SYSUTCDATETIME(),
    CONSTRAINT FK_EmailLogs_PurchaseRequests FOREIGN KEY (RequestID) REFERENCES dbo.PurchaseRequests(RequestID),
    CONSTRAINT FK_EmailLogs_AgentActions FOREIGN KEY (ActionID) REFERENCES dbo.AgentActions(ActionID),
    CONSTRAINT FK_EmailLogs_Vendors FOREIGN KEY (VendorID) REFERENCES dbo.Vendors(VendorID)
);

CREATE TABLE dbo.ExecutionLogs (
    LogID INT IDENTITY(1,1) PRIMARY KEY,
    RequestID INT NULL,
    NodeName NVARCHAR(120) NOT NULL,
    Status NVARCHAR(40) NOT NULL,
    Message NVARCHAR(MAX) NOT NULL,
    LatencyMs FLOAT NULL,
    LlmPromptTokens INT NULL,
    LlmCompletionTokens INT NULL,
    LlmCostUsd FLOAT NULL,
    CreatedAt DATETIME2 NOT NULL CONSTRAINT DF_ExecutionLogs_CreatedAt DEFAULT SYSUTCDATETIME(),
    UpdatedAt DATETIME2 NOT NULL CONSTRAINT DF_ExecutionLogs_UpdatedAt DEFAULT SYSUTCDATETIME(),
    CONSTRAINT FK_ExecutionLogs_PurchaseRequests FOREIGN KEY (RequestID) REFERENCES dbo.PurchaseRequests(RequestID)
);
GO

CREATE INDEX IX_Vendors_Category ON dbo.Vendors(Category);
CREATE INDEX IX_Vendors_Department ON dbo.Vendors(Department);
CREATE INDEX IX_PurchaseRequests_Status ON dbo.PurchaseRequests(Status);
CREATE INDEX IX_AgentActions_Status ON dbo.AgentActions(Status);
CREATE INDEX IX_AgentActions_RequestID ON dbo.AgentActions(RequestID);
CREATE UNIQUE INDEX UX_AgentActions_IdempotencyKey ON dbo.AgentActions(IdempotencyKey);
CREATE INDEX IX_RequestAttachments_RequestID ON dbo.RequestAttachments(RequestID);
CREATE INDEX IX_RequestAttachments_FileHash ON dbo.RequestAttachments(FileHash);
CREATE INDEX IX_DocumentExtractions_RequestID ON dbo.DocumentExtractions(RequestID);
CREATE INDEX IX_DocumentExtractions_AttachmentID ON dbo.DocumentExtractions(AttachmentID);
CREATE INDEX IX_EmailLogs_ActionID ON dbo.EmailLogs(ActionID);
CREATE UNIQUE INDEX UX_EmailLogs_IdempotencyKey ON dbo.EmailLogs(IdempotencyKey);
CREATE INDEX IX_ExecutionLogs_RequestID ON dbo.ExecutionLogs(RequestID);
CREATE INDEX IX_ExecutionLogs_CreatedAt ON dbo.ExecutionLogs(CreatedAt);
CREATE INDEX IX_Vendors_CreatedAt ON dbo.Vendors(CreatedAt);
CREATE INDEX IX_PurchaseRequests_CreatedAt ON dbo.PurchaseRequests(CreatedAt);
CREATE INDEX IX_AgentActions_CreatedAt ON dbo.AgentActions(CreatedAt);
GO
