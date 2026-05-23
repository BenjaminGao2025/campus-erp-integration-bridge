from fastapi import APIRouter, Depends, Header, Response
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import Request
from app.routes.serializers import request_to_dict
from app.schemas import IntakeRequest
from app.services.intake_service import create_request, submit_request

router = APIRouter(prefix="/api/intake", tags=["intake"])


@router.post("/requests")
def create_intake_request(
    body: IntakeRequest,
    response: Response,
    db: Session = Depends(get_session),
    x_correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    request, created = create_request(
        db,
        request_type=body.request_type,
        submitted_by=body.submitted_by,
        submitted_by_email=body.submitted_by_email,
        payload=body.payload,
        free_text=body.free_text,
        correlation_id=x_correlation_id,
        idempotency_key=idempotency_key,
    )
    response.status_code = 201 if created else 200
    return request_to_dict(request)


@router.get("/requests")
def list_requests(db: Session = Depends(get_session)):
    return [request_to_dict(item) for item in db.execute(select(Request).order_by(Request.created_at.desc())).scalars()]


@router.get("/requests/{request_id}")
def get_request(request_id: str, db: Session = Depends(get_session)):
    request = db.get(Request, request_id)
    if request is None:
        return JSONResponse(status_code=404, content={"detail": "request not found"})
    return request_to_dict(request, detail=True)


@router.post("/requests/{request_id}/submit")
def submit(request_id: str, db: Session = Depends(get_session)):
    request, ok, validation = submit_request(db, request_id)
    body = request_to_dict(request, detail=True)
    if validation is not None:
        body["validation_result"] = validation
    if not ok:
        return JSONResponse(status_code=422, content=body)
    return body
