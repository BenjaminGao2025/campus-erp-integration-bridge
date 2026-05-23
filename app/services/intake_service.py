from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit import hash_payload, redact_text, write_audit_event
from app.enums import (
    EVENT_AI_SUMMARY_GENERATED,
    EVENT_BUSINESS_RULES_EVALUATED,
    EVENT_CANONICAL_MAPPING_CREATED,
    EVENT_APPROVAL_REQUESTED,
    EVENT_REQUEST_RECEIVED,
    EVENT_SCHEMA_VALIDATION_FAILED,
    EVENT_SCHEMA_VALIDATION_PASSED,
    REQUEST_PAYROLL_CORRECTION,
    REQUEST_WORKER_CHANGE,
)
from app.models import ApprovalTask, Request, RequestPayload, SupportNote
from app.services.ai_assist_service import summarize_request
from app.validation.business_rules import evaluate_business_rules
from app.validation.json_schema_validator import validate_payload


def create_request(
    db: Session,
    *,
    request_type: str,
    submitted_by: str,
    submitted_by_email: str,
    payload: dict,
    free_text: str | None,
    correlation_id: str | None,
    idempotency_key: str | None,
) -> tuple[Request, bool]:
    body_hash = hash_payload({"request_type": request_type, "payload": payload, "free_text": free_text})
    if idempotency_key:
        existing = db.execute(select(Request).where(Request.idempotency_key == idempotency_key)).scalar_one_or_none()
        if existing:
            existing_payload = existing.payloads[0]
            if existing_payload.payload_hash != body_hash:
                raise HTTPException(status_code=409, detail="Idempotency-Key already used with a different payload")
            return existing, False

    corr = correlation_id or f"corr-{uuid4()}"
    request = Request(
        request_type=request_type,
        submitted_by=submitted_by,
        submitted_by_email=submitted_by_email,
        status="received",
        correlation_id=corr,
        idempotency_key=idempotency_key,
    )
    db.add(request)
    db.flush()
    db.add(RequestPayload(request_id=request.id, raw_payload=payload, payload_hash=body_hash, schema_version="2026-05-demo"))
    _, flags = redact_text(free_text)
    write_audit_event(
        db,
        request_id=request.id,
        correlation_id=corr,
        actor_type="user",
        actor_id=submitted_by_email,
        event_type=EVENT_REQUEST_RECEIVED,
        message="Synthetic request received from mock service portal.",
        payload_hash=body_hash,
        redaction_flags=flags,
    )
    ai = summarize_request(request_type, free_text, payload)
    db.add(
        SupportNote(
            request_id=request.id,
            note_type="ai_summary",
            content=ai["summary"],
            created_by="mock_ai_assist_service",
            is_ai_generated=True,
        )
    )
    write_audit_event(
        db,
        request_id=request.id,
        correlation_id=corr,
        actor_type="ai_assistant",
        actor_id="mock_ai_assist_service",
        event_type=EVENT_AI_SUMMARY_GENERATED,
        message="AI assistive summary generated; no operational state changed by AI.",
        redaction_flags=ai["redaction_flags"],
        metadata={"limitations": ai["limitations"]},
    )
    db.commit()
    db.refresh(request)
    return request, True


def build_canonical_event(request: Request, payload: dict, rules: dict) -> dict:
    domain = "hcm" if request.request_type == REQUEST_WORKER_CHANGE else "payroll"
    operation = payload.get("change_type") or payload.get("correction_type")
    effective_date = payload.get("effective_date") or payload.get("pay_period_end")
    return {
        "canonical_event_id": f"EVT-{uuid4()}",
        "request_id": request.id,
        "request_type": request.request_type,
        "subject": {"worker_id": payload["worker_id"], "synthetic_worker_ref": payload["worker_id"]},
        "effective_date": effective_date,
        "domain": domain,
        "operation": operation,
        "risk": {
            "priority": rules["priority"],
            "requires_approval": rules["requires_approval"],
            "approval_roles": rules["approval_roles"],
        },
        "data": payload,
        "metadata": {
            "schema_version": "2026-05-demo",
            "correlation_id": request.correlation_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    }


def submit_request(db: Session, request_id: str) -> tuple[Request, bool, dict | None]:
    request = db.get(Request, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="request not found")
    payload_row = request.payloads[0]
    payload = payload_row.raw_payload
    schema_result = validate_payload(request.request_type, payload)
    if not schema_result["valid"]:
        before = {"status": request.status}
        request.status = "validation_failed"
        write_audit_event(
            db,
            request_id=request.id,
            correlation_id=request.correlation_id,
            actor_type="system",
            event_type=EVENT_SCHEMA_VALIDATION_FAILED,
            message="JSON Schema validation failed.",
            before_state=before,
            after_state={"status": request.status},
            validation_result=schema_result,
        )
        db.commit()
        return request, False, schema_result

    write_audit_event(
        db,
        request_id=request.id,
        correlation_id=request.correlation_id,
        actor_type="system",
        event_type=EVENT_SCHEMA_VALIDATION_PASSED,
        message="JSON Schema validation passed.",
        validation_result=schema_result,
    )
    rules = evaluate_business_rules(db, request.request_type, payload)
    write_audit_event(
        db,
        request_id=request.id,
        correlation_id=request.correlation_id,
        actor_type="system",
        event_type=EVENT_BUSINESS_RULES_EVALUATED,
        message="Business rules evaluated deterministically.",
        validation_result=rules,
    )
    if not rules["valid"]:
        before = {"status": request.status}
        request.status = "validation_failed"
        write_audit_event(
            db,
            request_id=request.id,
            correlation_id=request.correlation_id,
            actor_type="system",
            event_type=EVENT_SCHEMA_VALIDATION_FAILED,
            message="Business rule validation failed.",
            before_state=before,
            after_state={"status": request.status},
            validation_result=rules,
        )
        db.commit()
        return request, False, rules

    canonical = build_canonical_event(request, payload, rules)
    payload_row.normalized_payload = canonical
    request.priority = rules["priority"]
    before = {"status": request.status}
    request.status = "pending_approval" if rules["requires_approval"] else "ready_for_integration"
    write_audit_event(
        db,
        request_id=request.id,
        correlation_id=request.correlation_id,
        actor_type="system",
        event_type=EVENT_CANONICAL_MAPPING_CREATED,
        message="Canonical event model created.",
        before_state=before,
        after_state={"status": request.status},
    )
    for role in rules["approval_roles"]:
        db.add(ApprovalTask(request_id=request.id, approver_role=role))
        write_audit_event(
            db,
            request_id=request.id,
            correlation_id=request.correlation_id,
            actor_type="system",
            event_type=EVENT_APPROVAL_REQUESTED,
            message=f"Approval requested from {role}.",
            metadata={"approver_role": role},
        )
    db.commit()
    db.refresh(request)
    return request, True, None
