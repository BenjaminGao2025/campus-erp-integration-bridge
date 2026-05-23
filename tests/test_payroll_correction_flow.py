from http import HTTPStatus


def test_valid_payroll_correction_flow_generates_valid_xml_and_completes(client):
    response = client.post(
        "/api/intake/requests",
        headers={"X-Correlation-Id": "corr-payroll-1", "Idempotency-Key": "payroll-key-1"},
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
                "simulate_failure": "none",
            },
            "free_text": "Please review this synthetic payroll correction.",
        },
    )
    assert response.status_code == HTTPStatus.CREATED
    request_id = response.json()["id"]

    submit = client.post(f"/api/intake/requests/{request_id}/submit")
    assert submit.status_code == HTTPStatus.OK

    approval = client.get("/api/approvals/pending").json()[0]
    decision = client.post(
        f"/api/approvals/{approval['id']}/decision",
        json={"decision": "approved", "decision_by": "synthetic_payroll_reviewer", "comment": "Approved."},
    )
    assert decision.status_code == HTTPStatus.OK
    assert decision.json()["request_status"] == "completed"

    detail = client.get(f"/api/intake/requests/{request_id}").json()
    assert detail["normalized_payload"]["domain"] == "payroll"
    assert detail["integration_jobs"][0]["adapter_type"] == "mock_legacy_payroll_xml"
    assert detail["integration_artifacts"][0]["payload_format"] == "xml"
    assert detail["integration_artifacts"][0]["validation_result"]["valid"] is True

    event_types = [event["event_type"] for event in client.get(f"/api/audit/requests/{request_id}").json()]
    assert "xml_generated" in event_types
    assert "xsd_validation_passed" in event_types
    assert "adapter_execution_completed" in event_types
