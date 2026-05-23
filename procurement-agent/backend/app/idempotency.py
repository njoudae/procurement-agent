import hashlib
import json
from typing import Any


def build_idempotency_key(prefix: str, *parts: Any) -> str:
    normalized = json.dumps(parts, sort_keys=True, default=str, separators=(",", ":"))
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return f"{prefix}:{digest}"
