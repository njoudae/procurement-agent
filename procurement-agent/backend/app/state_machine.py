from app.exceptions import InvalidStatusTransitionError


ACTION_TRANSITIONS: dict[str, set[str]] = {
    "Draft": {"PendingApproval"},
    "PendingApproval": {"Approved", "Rejected", "NeedsReview", "Failed"},
    "NeedsReview": {"PendingApproval", "Rejected", "Failed"},
    "Approved": {"Executing", "Failed"},
    "Executing": {"Executed", "Failed"},
    "Executed": set(),
    "Rejected": set(),
    "Failed": set(),
}

REQUEST_TRANSITIONS: dict[str, set[str]] = {
    "New": {"Processing", "NeedsReview", "PendingApproval", "Failed"},
    "Processing": {"NeedsReview", "PendingApproval", "Completed", "Failed"},
    "NeedsReview": {"PendingApproval", "Rejected", "Completed", "Failed"},
    "PendingApproval": {"Approved", "Rejected", "Completed", "NeedsReview", "Failed"},
    "Approved": {"Completed", "Failed"},
    "Rejected": set(),
    "Completed": set(),
    "Failed": {"NeedsReview"},
}


def validate_transition(current: str, target: str, transitions: dict[str, set[str]]) -> None:
    if current == target:
        return
    allowed = transitions.get(current, set())
    if target not in allowed:
        raise InvalidStatusTransitionError(f"Invalid status transition: {current} -> {target}")
