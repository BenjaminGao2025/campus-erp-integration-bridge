from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.audit import write_audit_event
from app.enums import EVENT_RETRY_STARTED
from app.models import IntegrationJob, Request
from app.services.orchestration_service import run_job


def retry_job(db: Session, job_id: str) -> Request:
    job = db.get(IntegrationJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    if job.status not in {"failed_retryable", "retry_scheduled"}:
        raise HTTPException(status_code=409, detail="only retryable failed jobs can be retried")
    if job.attempt_count >= job.max_attempts:
        raise HTTPException(status_code=409, detail="max attempts reached")
    request = db.get(Request, job.request_id)
    assert request is not None
    write_audit_event(
        db,
        request_id=request.id,
        correlation_id=request.correlation_id,
        actor_type="system",
        event_type=EVENT_RETRY_STARTED,
        message="Manual retry started from support console.",
        metadata={"job_id": job.id, "attempt_count_before": job.attempt_count},
    )
    return run_job(db, job)
