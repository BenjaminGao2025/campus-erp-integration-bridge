import json
from datetime import datetime

from sqlalchemy.orm import Session

from app.audit import hash_payload, write_audit_event
from app.enums import EVENT_XML_GENERATED, EVENT_XSD_VALIDATION_FAILED, EVENT_XSD_VALIDATION_PASSED
from app.models import IntegrationArtifact, IntegrationJob, MockPayrollRecord, MockWorker, Request
from app.validation.xml_validator import generate_payroll_xml, validate_payroll_xml


def _canonical(request: Request) -> dict:
    return request.payloads[0].normalized_payload or {}


def execute_job(db: Session, request: Request, job: IntegrationJob) -> dict:
    canonical = _canonical(request)
    simulate_failure = canonical.get("data", {}).get("simulate_failure", "none")
    if simulate_failure == "transient" and job.attempt_count == 1:
        return {"status": "failed_retryable", "error_code": "TRANSIENT_TIMEOUT", "error_message": "Synthetic timeout."}
    if simulate_failure == "permanent":
        return {"status": "failed_permanent", "error_code": "PERMANENT_VALIDATION", "error_message": "Synthetic permanent adapter rejection."}
    if job.adapter_type == "mock_legacy_payroll_xml":
        return _execute_payroll_adapter(db, request, job, canonical)
    return _execute_worker_adapter(db, request, job, canonical)


def _execute_worker_adapter(db: Session, request: Request, job: IntegrationJob, canonical: dict) -> dict:
    body = json.dumps(canonical, sort_keys=True, default=str)
    db.add(
        IntegrationArtifact(
            job_id=job.id,
            request_id=request.id,
            payload_format="json",
            payload_body=body,
            payload_hash=hash_payload(canonical),
            validation_result={"valid": True, "adapter": "mock_erp_rest"},
        )
    )
    worker = db.get(MockWorker, canonical["subject"]["worker_id"])
    if worker is None:
        return {"status": "failed_permanent", "error_code": "WORKER_NOT_FOUND", "error_message": "Synthetic worker not found."}
    data = canonical["data"]
    if data["change_type"] == "department_update":
        worker.department = data["proposed_value"]
    elif data["change_type"] == "manager_update":
        worker.manager_id = data["proposed_value"]
    elif data["change_type"] == "location_update":
        worker.location = data["proposed_value"]
    elif data["change_type"] == "employment_status_update":
        worker.employment_status = data["proposed_value"]
    return {"status": "completed"}


def _execute_payroll_adapter(db: Session, request: Request, job: IntegrationJob, canonical: dict) -> dict:
    xml = generate_payroll_xml(canonical)
    write_audit_event(
        db,
        request_id=request.id,
        correlation_id=request.correlation_id,
        actor_type="adapter_service",
        event_type=EVENT_XML_GENERATED,
        message="Outbound payroll XML generated from canonical event.",
        payload_hash=hash_payload(xml),
    )
    validation = validate_payroll_xml(xml)
    db.add(
        IntegrationArtifact(
            job_id=job.id,
            request_id=request.id,
            payload_format="xml",
            payload_body=xml,
            payload_hash=hash_payload(xml),
            validation_result=validation,
        )
    )
    write_audit_event(
        db,
        request_id=request.id,
        correlation_id=request.correlation_id,
        actor_type="adapter_service",
        event_type=EVENT_XSD_VALIDATION_PASSED if validation["valid"] else EVENT_XSD_VALIDATION_FAILED,
        message="Payroll XML XSD validation passed." if validation["valid"] else "Payroll XML XSD validation failed.",
        validation_result=validation,
    )
    if not validation["valid"]:
        return {"status": "failed_permanent", "error_code": "XSD_VALIDATION_FAILED", "error_message": "; ".join(validation["errors"])}
    data = canonical["data"]
    db.add(
        MockPayrollRecord(
            worker_id=canonical["subject"]["worker_id"],
            pay_period_start=datetime.strptime(data["pay_period_start"], "%Y-%m-%d").date(),
            pay_period_end=datetime.strptime(data["pay_period_end"], "%Y-%m-%d").date(),
            issue_type=data["correction_type"],
            amount=data["amount"],
            currency=data["currency"],
            status="recorded",
        )
    )
    return {"status": "completed"}
