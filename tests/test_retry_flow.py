from http import HTTPStatus


def test_transient_payroll_adapter_failure_can_be_retried_to_completion(client):
    create = client.post(
        "/api/intake/requests",
        json={
            "request_type": "payroll_correction",
            "submitted_by": "Demo Payroll Analyst",
            "submitted_by_email": "payroll@example.test",
            "payload": {
                "worker_id": "WKR-10002",
                "pay_period_start": "2026-06-01",
                "pay_period_end": "2026-06-15",
                "correction_type": "underpayment",
                "amount": 650.00,
                "currency": "CAD",
                "reason": "Synthetic payroll correction for missed earning code in the demo period.",
                "requested_by_role": "payroll_analyst",
                "simulate_failure": "transient",
            },
        },
    )
    request_id = create.json()["id"]
    client.post(f"/api/intake/requests/{request_id}/submit")
    approval = client.get("/api/approvals/pending").json()[0]

    approved = client.post(
        f"/api/approvals/{approval['id']}/decision",
        json={"decision": "approved", "decision_by": "synthetic_payroll_reviewer"},
    )
    assert approved.status_code == HTTPStatus.OK
    assert approved.json()["request_status"] == "failed_retryable"

    detail = client.get(f"/api/intake/requests/{request_id}").json()
    job_id = detail["integration_jobs"][0]["id"]
    assert detail["integration_jobs"][0]["attempt_count"] == 1

    retry = client.post(f"/api/jobs/{job_id}/retry")
    assert retry.status_code == HTTPStatus.OK
    assert retry.json()["request_status"] == "completed"

    retried_detail = client.get(f"/api/intake/requests/{request_id}").json()
    assert retried_detail["integration_jobs"][0]["attempt_count"] == 2
    assert retried_detail["integration_jobs"][0]["status"] == "completed"


def test_permanent_adapter_failure_cannot_be_retried(client):
    create = client.post(
        "/api/intake/requests",
        json={
            "request_type": "worker_change",
            "submitted_by": "Demo Requester",
            "submitted_by_email": "requester@example.test",
            "payload": {
                "worker_id": "WKR-10001",
                "change_type": "department_update",
                "effective_date": "2026-07-01",
                "current_value": "Operations",
                "proposed_value": "Enterprise Systems",
                "reason": "Department record needs to reflect a synthetic internal transfer.",
                "requested_by_role": "manager",
                "simulate_failure": "permanent",
            },
        },
    )
    request_id = create.json()["id"]
    client.post(f"/api/intake/requests/{request_id}/submit")
    approval = client.get("/api/approvals/pending").json()[0]
    client.post(f"/api/approvals/{approval['id']}/decision", json={"decision": "approved", "decision_by": "manager"})
    job_id = client.get(f"/api/intake/requests/{request_id}").json()["integration_jobs"][0]["id"]

    retry = client.post(f"/api/jobs/{job_id}/retry")
    assert retry.status_code == HTTPStatus.CONFLICT
