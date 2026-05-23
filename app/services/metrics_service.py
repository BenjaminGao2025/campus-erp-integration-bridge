from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import IntegrationJob, Request


def dashboard_metrics(db: Session) -> dict:
    total = db.scalar(select(func.count()).select_from(Request)) or 0
    pending_approvals = db.scalar(select(func.count()).select_from(Request).where(Request.status == "pending_approval")) or 0
    completed = db.scalar(select(func.count()).select_from(Request).where(Request.status == "completed")) or 0
    failed_retryable = db.scalar(select(func.count()).select_from(IntegrationJob).where(IntegrationJob.status == "failed_retryable")) or 0
    failed_permanent = db.scalar(select(func.count()).select_from(IntegrationJob).where(IntegrationJob.status == "failed_permanent")) or 0
    avg_attempts = db.scalar(select(func.avg(IntegrationJob.attempt_count))) or 0
    by_type = {row[0]: row[1] for row in db.execute(select(Request.request_type, func.count()).group_by(Request.request_type))}
    by_status = {row[0]: row[1] for row in db.execute(select(Request.status, func.count()).group_by(Request.status))}
    return {
        "total_requests": total,
        "pending_approvals": pending_approvals,
        "completed_requests": completed,
        "failed_retryable_jobs": failed_retryable,
        "failed_permanent_jobs": failed_permanent,
        "average_attempts": float(avg_attempts),
        "requests_by_type": by_type,
        "requests_by_status": by_status,
    }
