import logging
import json

from sqlalchemy.orm import Session

from app.models import ExecutionLog

logger = logging.getLogger(__name__)


def scrub_message(message: str) -> str:
    redacted_terms = ["OPENAI_API_KEY", "DB_PASSWORD", "SMTP_PASSWORD"]
    safe = message
    for term in redacted_terms:
        safe = safe.replace(term, "[REDACTED]")
    return safe[:4000]


def log_execution(
    db: Session,
    request_id: int | None,
    node_name: str,
    status: str,
    message: str,
    latency_ms: float | None = None,
    llm_prompt_tokens: int | None = None,
    llm_completion_tokens: int | None = None,
    llm_cost_usd: float | None = None,
) -> ExecutionLog:
    safe_message = scrub_message(message)
    entry = ExecutionLog(
        RequestID=request_id,
        NodeName=node_name,
        Status=status,
        Message=safe_message,
        LatencyMs=latency_ms,
        LlmPromptTokens=llm_prompt_tokens,
        LlmCompletionTokens=llm_completion_tokens,
        LlmCostUsd=llm_cost_usd,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    log_method = logger.error if status.lower() in {"error", "failed"} else logger.info
    log_method(
        json.dumps(
            {
                "request_id": request_id,
                "node": node_name,
                "status": status,
                "latency_ms": latency_ms,
                "llm_prompt_tokens": llm_prompt_tokens,
                "llm_completion_tokens": llm_completion_tokens,
                "llm_cost_usd": llm_cost_usd,
                "message": safe_message,
            },
            default=str,
        )
    )
    return entry
