from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.audit import hash_payload, write_audit_event
from app.enums import (
    EVENT_ADAPTER_EXECUTION_COMPLETED,
    EVENT_ADAPTER_EXECUTION_FAILED,
    EVENT_ADAPTER_EXECUTION_STARTED,
    EVENT_INTEGRATION_JOB_CREATED,
    EVENT_REQUEST_COMPLETED,
    EVENT_REQUEST_FAILED,
    EVENT_RETRY_SCHEDULED,
    REQUEST_PAYROLL_CORRECTION,
)
from app.models import IntegrationJob, Request
from app.services.adapter_service import execute_job


def create_job_for_request(db: Session, request: Request) -> IntegrationJob:
    adapter_type = "mock_legacy_payroll_xml" if request.request_type == REQUEST_PAYROLL_CORRECTION else "mock_erp_rest"
    target = "mock legacy payroll system" if adapter_type == "mock_legacy_payroll_xml" else "mock ERP REST system"
    job = IntegrationJob(request_id=request.id, adapter_type=adapter_type, target_system=target)
    db.add(job)
    db.flush()
    write_audit_event(
        db,
        request_id=request.id,
        correlation_id=request.correlation_id,
        actor_type="system",
        event_type=EVENT_INTEGRATION_JOB_CREATED,
        message=f"Integration job created for {target}.",
        metadata={"job_id": job.id, "adapter_type": adapter_type},
    )
    return job


def run_job(db: Session, job: IntegrationJob) -> Request:
    request = db.get(Request, job.request_id)
    assert request is not None
    before = {"status": request.status, "job_status": job.status}
    request.status = "processing"
    job.status = "processing"
    job.attempt_count += 1
    write_audit_event(
        db,
        request_id=request.id,
        correlation_id=request.correlation_id,
        actor_type="adapter_service",
        event_type=EVENT_ADAPTER_EXECUTION_STARTED,
        message="Adapter execution started.",
        before_state=before,
        after_state={"status": request.status, "job_status": job.status, "attempt_count": job.attempt_count},
    )
    result = execute_job(db, request, job)
    if result["status"] == "completed":
        job.status = "completed"
        request.status = "completed"
        write_audit_event(
            db,
            request_id=request.id,
            correlation_id=request.correlation_id,
            actor_type="adapter_service",
            event_type=EVENT_ADAPTER_EXECUTION_COMPLETED,
            message="Adapter execution completed.",
            after_state={"status": request.status, "job_status": job.status},
        )
        write_audit_event(
            db,
            request_id=request.id,
            correlation_id=request.correlation_id,
            actor_type="system",
            event_type=EVENT_REQUEST_COMPLETED,
            message="Request completed after adapter execution.",
        )
    elif result["status"] == "failed_retryable":
        failure_before = {"status": request.status, "job_status": job.status, "attempt_count": job.attempt_count}
        job.status = "failed_retryable"
        request.status = "failed_retryable"
        job.last_error_code = result["error_code"]
        job.last_error_message = result["error_message"]
        job.next_retry_at = datetime.now(timezone.utc) + timedelta(seconds=1)
        write_audit_event(
            db,
            request_id=request.id,
            correlation_id=request.correlation_id,
            actor_type="adapter_service",
            event_type=EVENT_ADAPTER_EXECUTION_FAILED,
            message="Adapter execution failed with retryable error.",
            error_code=result["error_code"],
            error_message=result["error_message"],
            before_state=failure_before,
            after_state={"status": request.status, "job_status": job.status, "attempt_count": job.attempt_count},
        )
        write_audit_event(
            db,
            request_id=request.id,
            correlation_id=request.correlation_id,
            actor_type="system",
            event_type=EVENT_RETRY_SCHEDULED,
            message="Retry scheduled for transient adapter failure.",
            metadata={"next_retry_at": job.next_retry_at.isoformat()},
        )
    else:
        failure_before = {"status": request.status, "job_status": job.status, "attempt_count": job.attempt_count}
        job.status = "failed_permanent"
        request.status = "failed_permanent"
        job.last_error_code = result["error_code"]
        job.last_error_message = result["error_message"]
        write_audit_event(
            db,
            request_id=request.id,
            correlation_id=request.correlation_id,
            actor_type="adapter_service",
            event_type=EVENT_ADAPTER_EXECUTION_FAILED,
            message="Adapter execution failed permanently.",
            error_code=result["error_code"],
            error_message=result["error_message"],
            before_state=failure_before,
            after_state={"status": request.status, "job_status": job.status, "attempt_count": job.attempt_count},
        )
        write_audit_event(
            db,
            request_id=request.id,
            correlation_id=request.correlation_id,
            actor_type="system",
            event_type=EVENT_REQUEST_FAILED,
            message="Request failed permanently.",
        )
    db.commit()
    db.refresh(request)
    return request


def create_and_run_job(db: Session, request: Request) -> Request:
    job = create_job_for_request(db, request)
    return run_job(db, job)
