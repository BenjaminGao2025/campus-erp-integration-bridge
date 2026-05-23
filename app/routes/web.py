from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import IntegrationJob, Request as RequestModel
from app.routes.serializers import request_to_dict
from app.services.approval_service import decide_approval
from app.services.intake_service import create_request, submit_request
from app.services.metrics_service import dashboard_metrics
from app.services.retry_service import retry_job

router = APIRouter(tags=["web"])
templates = Jinja2Templates(directory="app/templates")


def _dashboard_context(metrics: dict) -> dict:
    return {
        "metric_cards": [
            {"label": "Total requests", "value": metrics["total_requests"]},
            {"label": "Pending approvals", "value": metrics["pending_approvals"]},
            {"label": "Completed requests", "value": metrics["completed_requests"]},
            {"label": "Retryable failures", "value": metrics["failed_retryable_jobs"]},
            {"label": "Permanent failures", "value": metrics["failed_permanent_jobs"]},
            {"label": "Average attempts", "value": metrics["average_attempts"]},
        ],
        "requests_by_type": metrics["requests_by_type"],
        "requests_by_status": metrics["requests_by_status"],
    }


def _request_or_404(db: Session, request_id: str) -> RequestModel:
    item = db.get(RequestModel, request_id)
    if item is None:
        raise HTTPException(status_code=404, detail="request not found")
    return item


@router.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_session)):
    requests = db.execute(select(RequestModel).order_by(RequestModel.created_at.desc()).limit(10)).scalars()
    failed_jobs = db.execute(select(IntegrationJob).where(IntegrationJob.status.in_(["failed_retryable", "failed_permanent"]))).scalars()
    metrics = dashboard_metrics(db)
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "request": request,
            "metrics": metrics,
            "requests": list(requests),
            "failed_jobs": list(failed_jobs),
        },
    )


@router.get("/requests/new", response_class=HTMLResponse)
def new_request(request: Request):
    return templates.TemplateResponse(request, "request_form.html", {"request": request})


@router.post("/requests/new", response_class=HTMLResponse)
def create_request_from_form(
    db: Session = Depends(get_session),
    request_type: str = Form(...),
    submitted_by: str = Form(...),
    submitted_by_email: str = Form(...),
    free_text: str | None = Form(default=None),
    worker_id: str = Form(...),
    simulate_failure: str = Form("none"),
    change_type: str | None = Form(default=None),
    effective_date: str | None = Form(default=None),
    current_value: str | None = Form(default=None),
    proposed_value: str | None = Form(default=None),
    reason: str | None = Form(default=None),
    requested_by_role: str | None = Form(default=None),
    pay_period_start: str | None = Form(default=None),
    pay_period_end: str | None = Form(default=None),
    correction_type: str | None = Form(default=None),
    amount: float | None = Form(default=None),
    currency: str = Form("CAD"),
):
    if request_type == "worker_change":
        payload = {
            "worker_id": worker_id,
            "change_type": change_type,
            "effective_date": effective_date,
            "current_value": current_value,
            "proposed_value": proposed_value,
            "reason": reason,
            "requested_by_role": requested_by_role,
            "simulate_failure": simulate_failure,
        }
    else:
        payload = {
            "worker_id": worker_id,
            "pay_period_start": pay_period_start,
            "pay_period_end": pay_period_end,
            "correction_type": correction_type,
            "amount": amount,
            "currency": currency,
            "reason": reason,
            "requested_by_role": requested_by_role,
            "simulate_failure": simulate_failure,
        }

    created, _ = create_request(
        db,
        request_type=request_type,
        submitted_by=submitted_by,
        submitted_by_email=submitted_by_email,
        payload=payload,
        free_text=free_text,
        correlation_id=None,
        idempotency_key=None,
    )
    return RedirectResponse(url=f"/requests/{created.id}", status_code=303)


@router.get("/requests/{request_id}", response_class=HTMLResponse)
def request_detail(request_id: str, request: Request, db: Session = Depends(get_session)):
    item = _request_or_404(db, request_id)
    return templates.TemplateResponse(request, "request_detail.html", {"request": request, "item": item, "detail": request_to_dict(item, True)})


@router.post("/requests/{request_id}/submit", response_class=HTMLResponse)
def submit_request_from_web(request_id: str, db: Session = Depends(get_session)):
    submit_request(db, request_id)
    return RedirectResponse(url=f"/requests/{request_id}", status_code=303)


@router.post("/requests/{request_id}/approvals/{approval_id}/decision", response_class=HTMLResponse)
def decide_approval_from_web(
    request_id: str,
    approval_id: str,
    db: Session = Depends(get_session),
    decision: str = Form(...),
    decision_by: str = Form("synthetic_reviewer"),
    comment: str | None = Form(default=None),
):
    decided = decide_approval(db, approval_id, decision, decision_by, comment)
    return RedirectResponse(url=f"/requests/{decided.id}", status_code=303)


@router.post("/requests/{request_id}/jobs/{job_id}/retry", response_class=HTMLResponse)
def retry_job_from_web(request_id: str, job_id: str, db: Session = Depends(get_session)):
    retried = retry_job(db, job_id)
    return RedirectResponse(url=f"/requests/{retried.id}", status_code=303)


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request, db: Session = Depends(get_session)):
    metrics = dashboard_metrics(db)
    return templates.TemplateResponse(request, "dashboard.html", {"request": request, "metrics": metrics, **_dashboard_context(metrics)})


@router.get("/requests/{request_id}/audit", response_class=HTMLResponse)
def audit_page(request_id: str, request: Request, db: Session = Depends(get_session)):
    item = _request_or_404(db, request_id)
    return templates.TemplateResponse(request, "audit_timeline.html", {"request": request, "item": item, "events": item.audit_events})
