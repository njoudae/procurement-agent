import functools
import logging
import time
from collections.abc import Callable
from typing import Any, TypeVar

from sqlalchemy.orm import Session

from app.database import session_scope
from app.exceptions import ApprovalRequiredError, DuplicateExecutionError, ProcurementError
from app.models import AgentAction
from app.tools.logging_tools import log_execution

F = TypeVar("F", bound=Callable[..., Any])
logger = logging.getLogger(__name__)


def measure_latency(func: F) -> F:
    if _is_coroutine(func):
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            try:
                return await func(*args, **kwargs)
            finally:
                logger.info("function=%s latency_ms=%.2f", func.__name__, (time.perf_counter() - start) * 1000)

        return async_wrapper  # type: ignore[return-value]

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            logger.info("function=%s latency_ms=%.2f", func.__name__, (time.perf_counter() - start) * 1000)

    return wrapper  # type: ignore[return-value]


def log_node_execution(node_name: str) -> Callable[[F], F]:
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(state: dict[str, Any], *args: Any, **kwargs: Any) -> Any:
            request_id = state.get("request_id")
            start = time.perf_counter()
            try:
                result = func(state, *args, **kwargs)
                latency_ms = (time.perf_counter() - start) * 1000
                with session_scope() as db:
                    log_execution(db, request_id, node_name, "Completed", f"{node_name} finished", latency_ms=latency_ms)
                return result
            except Exception as exc:
                latency_ms = (time.perf_counter() - start) * 1000
                with session_scope() as db:
                    log_execution(db, request_id, node_name, "Failed", str(exc), latency_ms=latency_ms)
                raise

        return wrapper  # type: ignore[return-value]

    return decorator


def handle_tool_errors(tool_name: str) -> Callable[[F], F]:
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except ProcurementError:
                raise
            except Exception as exc:
                logger.exception("tool=%s failed", tool_name)
                raise ProcurementError(f"{tool_name} failed safely") from exc

        return wrapper  # type: ignore[return-value]

    return decorator


def require_admin_approval(func: F) -> F:
    @functools.wraps(func)
    def wrapper(action_id: int, *args: Any, **kwargs: Any) -> Any:
        with session_scope() as db:
            action = db.get(AgentAction, action_id)
            if action and action.Status == "Executed":
                raise DuplicateExecutionError("Action already executed")
            if not action or action.Status != "Approved":
                raise ApprovalRequiredError("Action must be approved before execution")
        return func(action_id, *args, **kwargs)

    return wrapper  # type: ignore[return-value]


def require_permission(permission: str) -> Callable[[F], F]:
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            logger.debug("permission_check=%s function=%s", permission, func.__name__)
            return func(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator


def _is_coroutine(func: Callable[..., Any]) -> bool:
    return getattr(func, "__code__", None) is not None and bool(func.__code__.co_flags & 0x80)
