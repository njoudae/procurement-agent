from __future__ import annotations

from typing import Protocol

from app.agent.nodes import execute_approved_action


class ExecutionQueue(Protocol):
    def enqueue(self, action_id: int) -> dict[str, object]:
        ...


class InlineExecutionQueue:
    """Synchronous queue adapter for local development.

    Swap this implementation for Celery/RQ later without changing API handlers.
    """

    def enqueue(self, action_id: int) -> dict[str, object]:
        return execute_approved_action(action_id)


execution_queue: ExecutionQueue = InlineExecutionQueue()


def enqueue_execution(action_id: int) -> dict[str, object]:
    return execution_queue.enqueue(action_id)
