from __future__ import annotations

import json
from typing import Any

from app.exceptions import ExecutionSafetyError
from app.models import AgentAction


def parse_proposed_output(proposed_output: str | dict[str, Any] | list[Any]) -> dict[str, Any]:
    if isinstance(proposed_output, str):
        try:
            parsed = json.loads(proposed_output)
        except json.JSONDecodeError as exc:
            raise ExecutionSafetyError("Proposed output is not valid JSON") from exc
    else:
        parsed = proposed_output

    if isinstance(parsed, list):
        return {"rfq_drafts": parsed}
    if isinstance(parsed, dict):
        return parsed
    raise ExecutionSafetyError("Proposed output must be a JSON object or RFQ draft list")


def validate_execution_safety(action: AgentAction) -> dict[str, Any]:
    output = parse_proposed_output(action.ProposedOutput)
    blockers: list[str] = []

    if output.get("requires_admin_review") is True:
        blockers.append("requires_admin_review is true")

    validation_errors = output.get("validation_errors") or []
    if validation_errors:
        blockers.append("validation errors exist")

    if _guardrail_failed(output):
        blockers.append("guardrail failed")

    if _extraction_failed(output):
        blockers.append("extraction failed")

    if not output.get("rfq_drafts"):
        blockers.append("no RFQ drafts available to execute")

    if blockers:
        raise ExecutionSafetyError("Execution rejected: " + "; ".join(blockers))

    return output


def _guardrail_failed(output: dict[str, Any]) -> bool:
    guardrail_status = str(output.get("guardrail_status") or "").lower()
    if guardrail_status in {"failed", "needsreview", "needs_review"}:
        return True
    return any("guardrail" in message.lower() or "unsafe rfq draft" in message.lower() for message in _messages(output))


def _extraction_failed(output: dict[str, Any]) -> bool:
    if output.get("field_extraction_failed") or output.get("attachment_extraction_failed"):
        return True
    for extraction in output.get("document_extractions") or []:
        if extraction.get("requires_review") or extraction.get("extraction_errors"):
            return True
    for message in _messages(output):
        lowered = message.lower()
        if "extraction" in lowered and any(term in lowered for term in ("failed", "error", "invalid")):
            return True
    return False


def _messages(output: dict[str, Any]) -> list[str]:
    messages: list[str] = []
    for key in ("errors", "validation_errors"):
        values = output.get(key) or []
        if isinstance(values, list):
            messages.extend(str(value) for value in values)
        elif values:
            messages.append(str(values))
    return messages
