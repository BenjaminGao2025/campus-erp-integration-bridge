from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app.enums import REQUEST_PAYROLL_CORRECTION, REQUEST_WORKER_CHANGE
from app.models import MockWorker


def _parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def evaluate_business_rules(db: Session, request_type: str, payload: dict) -> dict:
    errors: list[str] = []
    worker = db.get(MockWorker, payload.get("worker_id"))
    if worker is None:
        errors.append("worker_id must exist in synthetic mock_workers data")

    if request_type == REQUEST_WORKER_CHANGE:
        effective_date = _parse_date(payload["effective_date"])
        if effective_date < date.today() - timedelta(days=180):
            errors.append("effective_date cannot be more than 180 days in the past")
        priority = "high" if payload["change_type"] == "employment_status_update" else "medium"
        return {
            "valid": not errors,
            "errors": errors,
            "priority": priority,
            "requires_approval": True,
            "approval_roles": ["manager"],
        }

    if request_type == REQUEST_PAYROLL_CORRECTION:
        start = _parse_date(payload["pay_period_start"])
        end = _parse_date(payload["pay_period_end"])
        if end <= start:
            errors.append("pay_period_end must be after pay_period_start")
        amount = float(payload["amount"])
        priority = "critical" if amount >= 2000 else "high" if amount >= 500 else "medium"
        return {
            "valid": not errors,
            "errors": errors,
            "priority": priority,
            "requires_approval": True,
            "approval_roles": ["payroll_reviewer"],
        }

    return {"valid": False, "errors": [f"unsupported request_type {request_type}"], "priority": "medium"}
