from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_session
from app.validation.xml_validator import generate_payroll_xml, validate_payroll_xml

router = APIRouter(prefix="/api/adapters", tags=["adapters"])


@router.post("/mock-erp/worker-change")
def mock_worker_change(canonical_event: dict):
    return {"status": "accepted", "adapter": "mock_erp_rest", "canonical_event_id": canonical_event.get("canonical_event_id")}


@router.post("/mock-legacy/payroll-correction")
def mock_payroll(canonical_event: dict, db: Session = Depends(get_session)):
    xml_body = generate_payroll_xml(canonical_event)
    return {"status": "accepted", "adapter": "mock_legacy_payroll_xml", "validation": validate_payroll_xml(xml_body), "xml": xml_body}
