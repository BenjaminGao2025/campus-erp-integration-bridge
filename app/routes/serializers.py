from app.models import ApprovalTask, AuditEvent, IntegrationArtifact, IntegrationJob, Request, SupportNote


def approval_to_dict(item: ApprovalTask) -> dict:
    return {
        "id": item.id,
        "request_id": item.request_id,
        "approver_role": item.approver_role,
        "status": item.status,
        "decision": item.decision,
        "decision_by": item.decision_by,
        "decision_at": item.decision_at.isoformat() if item.decision_at else None,
        "comment": item.comment,
    }


def job_to_dict(item: IntegrationJob) -> dict:
    return {
        "id": item.id,
        "request_id": item.request_id,
        "adapter_type": item.adapter_type,
        "target_system": item.target_system,
        "status": item.status,
        "attempt_count": item.attempt_count,
        "max_attempts": item.max_attempts,
        "next_retry_at": item.next_retry_at.isoformat() if item.next_retry_at else None,
        "last_error_code": item.last_error_code,
        "last_error_message": item.last_error_message,
    }


def artifact_to_dict(item: IntegrationArtifact) -> dict:
    return {
        "id": item.id,
        "job_id": item.job_id,
        "request_id": item.request_id,
        "payload_format": item.payload_format,
        "payload_body": item.payload_body,
        "payload_hash": item.payload_hash,
        "validation_result": item.validation_result,
        "created_at": item.created_at.isoformat(),
    }


def support_note_to_dict(item: SupportNote) -> dict:
    return {
        "id": item.id,
        "note_type": item.note_type,
        "content": item.content,
        "created_by": item.created_by,
        "is_ai_generated": item.is_ai_generated,
        "created_at": item.created_at.isoformat(),
    }


def request_to_dict(item: Request, detail: bool = False) -> dict:
    payload = item.payloads[0] if item.payloads else None
    data = {
        "id": item.id,
        "request_type": item.request_type,
        "source": item.source,
        "submitted_by": item.submitted_by,
        "submitted_by_email": item.submitted_by_email,
        "status": item.status,
        "priority": item.priority,
        "correlation_id": item.correlation_id,
        "idempotency_key": item.idempotency_key,
        "created_at": item.created_at.isoformat(),
        "updated_at": item.updated_at.isoformat(),
        "normalized_payload": payload.normalized_payload if payload else None,
    }
    if detail:
        data.update(
            {
                "raw_payload": payload.raw_payload if payload else None,
                "approval_tasks": [approval_to_dict(item) for item in item.approvals],
                "integration_jobs": [job_to_dict(item) for item in item.jobs],
                "integration_artifacts": [artifact_to_dict(item) for item in item.artifacts],
                "support_notes": [support_note_to_dict(item) for item in item.support_notes],
            }
        )
    return data


def audit_to_dict(item: AuditEvent) -> dict:
    return {
        "id": item.id,
        "request_id": item.request_id,
        "correlation_id": item.correlation_id,
        "actor_type": item.actor_type,
        "actor_id": item.actor_id,
        "event_type": item.event_type,
        "before_state": item.before_state,
        "after_state": item.after_state,
        "message": item.message,
        "payload_hash": item.payload_hash,
        "validation_result": item.validation_result,
        "error_code": item.error_code,
        "error_message": item.error_message,
        "redaction_flags": item.redaction_flags,
        "metadata": item.meta,
        "created_at": item.created_at.isoformat(),
    }
