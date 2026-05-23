from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_session
from app.routes.serializers import approval_to_dict, request_to_dict
from app.schemas import ApprovalDecision
from app.services.approval_service import decide_approval, pending_approvals

router = APIRouter(prefix="/api/approvals", tags=["approvals"])


@router.get("/pending")
def pending(db: Session = Depends(get_session)):
    return [approval_to_dict(item) for item in pending_approvals(db)]


@router.post("/{approval_id}/decision")
def decision(approval_id: str, body: ApprovalDecision, db: Session = Depends(get_session)):
    request = decide_approval(db, approval_id, body.decision, body.decision_by, body.comment)
    return {"request_status": request.status, "request": request_to_dict(request, detail=True)}
