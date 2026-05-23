from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit import write_audit_event
from app.enums import EVENT_APPROVAL_APPROVED, EVENT_APPROVAL_REJECTED
from app.models import ApprovalTask, Request
from app.services.orchestration_service import create_and_run_job


def decide_approval(db: Session, approval_id: str, decision: str, decision_by: str, comment: str | None = None) -> Request:
    approval = db.get(ApprovalTask, approval_id)
    if approval is None:
        raise HTTPException(status_code=404, detail="approval not found")
    request = db.get(Request, approval.request_id)
    assert request is not None
    if approval.status != "pending":
        raise HTTPException(status_code=409, detail="approval already decided")

    before = {"status": request.status, "approval_status": approval.status}
    approval.status = decision
    approval.decision = decision
    approval.decision_by = decision_by
    approval.decision_at = datetime.now(timezone.utc)
    approval.comment = comment
    if decision == "rejected":
        request.status = "rejected"
        write_audit_event(
            db,
            request_id=request.id,
            correlation_id=request.correlation_id,
            actor_type="approver",
            actor_id=decision_by,
            event_type=EVENT_APPROVAL_REJECTED,
            message="Approval rejected by synthetic approver.",
            before_state=before,
            after_state={"status": request.status, "approval_status": approval.status},
        )
        db.commit()
        db.refresh(request)
        return request

    request.status = "approved"
    write_audit_event(
        db,
        request_id=request.id,
        correlation_id=request.correlation_id,
        actor_type="approver",
        actor_id=decision_by,
        event_type=EVENT_APPROVAL_APPROVED,
        message="Approval completed by synthetic approver.",
        before_state=before,
        after_state={"status": request.status, "approval_status": approval.status},
    )
    db.flush()
    return create_and_run_job(db, request)


def pending_approvals(db: Session) -> list[ApprovalTask]:
    return list(db.execute(select(ApprovalTask).where(ApprovalTask.status == "pending")).scalars())
