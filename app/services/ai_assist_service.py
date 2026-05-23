from app.audit import redact_text
from app.enums import REQUEST_PAYROLL_CORRECTION, REQUEST_WORKER_CHANGE


def summarize_request(request_type: str | None, free_text: str | None, payload: dict) -> dict:
    redacted_text, flags = redact_text(free_text or "")
    text = (redacted_text or "").lower()
    suggested = request_type
    if not suggested:
        if any(word in text for word in ["pay", "payroll", "underpaid", "overpaid", "deduction"]):
            suggested = REQUEST_PAYROLL_CORRECTION
        elif any(word in text for word in ["department", "manager", "location", "employment status"]):
            suggested = REQUEST_WORKER_CHANGE
        else:
            suggested = REQUEST_WORKER_CHANGE

    required = {
        REQUEST_WORKER_CHANGE: [
            "worker_id",
            "change_type",
            "effective_date",
            "current_value",
            "proposed_value",
            "reason",
            "requested_by_role",
        ],
        REQUEST_PAYROLL_CORRECTION: [
            "worker_id",
            "pay_period_start",
            "pay_period_end",
            "correction_type",
            "amount",
            "currency",
            "reason",
            "requested_by_role",
        ],
    }
    missing = [field for field in required.get(suggested, []) if field not in payload]
    return {
        "suggested_request_type": suggested,
        "summary": f"Synthetic {suggested.replace('_', ' ')} request requiring deterministic validation and human approval.",
        "missing_fields_hint": missing,
        "next_action_draft": "Review required fields, submit for validation, then route to the required approval role.",
        "confidence": 0.82 if suggested else 0.3,
        "limitations": "AI is assistive only. It does not approve, validate finally, update records, or create audit truth.",
        "redaction_flags": flags,
    }
