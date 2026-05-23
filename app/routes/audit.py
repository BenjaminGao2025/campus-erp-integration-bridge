from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import AuditEvent
from app.routes.serializers import audit_to_dict

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("/requests/{request_id}")
def audit_timeline(request_id: str, db: Session = Depends(get_session)):
    events = db.execute(
        select(AuditEvent).where(AuditEvent.request_id == request_id).order_by(AuditEvent.created_at.asc())
    ).scalars()
    return [audit_to_dict(event) for event in events]
