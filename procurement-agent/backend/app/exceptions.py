class ProcurementError(Exception):
    status_code = 400
    user_message = "The request could not be completed"

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.user_message)
        self.user_message = message or self.user_message


class NotFoundError(ProcurementError):
    status_code = 404
    user_message = "Resource not found"


class InvalidStatusTransitionError(ProcurementError):
    status_code = 409
    user_message = "Invalid status transition"


class ApprovalRequiredError(ProcurementError):
    status_code = 409
    user_message = "Admin approval is required before execution"


class DuplicateExecutionError(ProcurementError):
    status_code = 409
    user_message = "This action has already been executed"


class ExecutionSafetyError(ProcurementError):
    status_code = 409
    user_message = "Action failed execution safety checks"


class DocumentProcessingError(ProcurementError):
    status_code = 422
    user_message = "Document could not be processed"


class PermissionDeniedError(ProcurementError):
    status_code = 403
    user_message = "Permission denied"
