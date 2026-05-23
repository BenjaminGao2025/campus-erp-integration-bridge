import hashlib
import json
import re
from typing import Any

from sqlalchemy.orm import Session

from app.models import AuditEvent


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))


def hash_payload(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def redact_text(text: str | None) -> tuple[str | None, dict]:
    if not text:
        return text, {"emails": 0, "phones": 0, "sin_like": 0, "id_like": 0}
    flags = {"emails": 0, "phones": 0, "sin_like": 0, "id_like": 0}

    def replace(pattern: str, label: str, value: str) -> str:
        matches = re.findall(pattern, value)
        flags[label] += len(matches)
        return re.sub(pattern, f"[REDACTED_{label.upper()}]", value)

    redacted = replace(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", "emails", text)
    redacted = replace(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b", "phones", redacted)
    redacted = replace(r"\b\d{3}-\d{3}-\d{3}\b", "sin_like", redacted)
    redacted = replace(r"\b\d{7,8}\b", "id_like", redacted)
    return redacted, flags


def write_audit_event(
    db: Session,
    *,
    request_id: str | None,
    correlation_id: str,
    actor_type: str,
    event_type: str,
    message: str,
    actor_id: str | None = None,
    before_state: dict | None = None,
    after_state: dict | None = None,
    payload_hash: str | None = None,
    validation_result: dict | None = None,
    error_code: str | None = None,
    error_message: str | None = None,
    redaction_flags: dict | None = None,
    metadata: dict | None = None,
) -> AuditEvent:
    event = AuditEvent(
        request_id=request_id,
        correlation_id=correlation_id,
        actor_type=actor_type,
        actor_id=actor_id,
        event_type=event_type,
        before_state=before_state,
        after_state=after_state,
        message=message,
        payload_hash=payload_hash,
        validation_result=validation_result,
        error_code=error_code,
        error_message=error_message,
        redaction_flags=redaction_flags,
        meta=metadata or {},
    )
    db.add(event)
    db.flush()
    return event
