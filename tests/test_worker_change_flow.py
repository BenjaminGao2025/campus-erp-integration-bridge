from http import HTTPStatus


def test_valid_worker_change_flow_completes_after_manager_approval(client):
    create_response = client.post(
        "/api/intake/requests",
        headers={"X-Correlation-Id": "corr-worker-1", "Idempotency-Key": "worker-key-1"},
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
                "simulate_failure": "none",
            },
            "free_text": "Please update this synthetic worker's department after manager approval.",
        },
    )
    assert create_response.status_code == HTTPStatus.CREATED
    request_id = create_response.json()["id"]

    submit_response = client.post(f"/api/intake/requests/{request_id}/submit")
    assert submit_response.status_code == HTTPStatus.OK
    assert submit_response.json()["status"] == "pending_approval"

    pending = client.get("/api/approvals/pending").json()
    approval = next(item for item in pending if item["request_id"] == request_id)

    decision_response = client.post(
        f"/api/approvals/{approval['id']}/decision",
        json={"decision": "approved", "decision_by": "synthetic_manager", "comment": "Approved for demo."},
    )
    assert decision_response.status_code == HTTPStatus.OK
    assert decision_response.json()["request_status"] == "completed"

    detail = client.get(f"/api/intake/requests/{request_id}").json()
    assert detail["status"] == "completed"
    assert detail["normalized_payload"]["domain"] == "hcm"
    assert detail["integration_jobs"][0]["status"] == "completed"

    timeline = client.get(f"/api/audit/requests/{request_id}").json()
    event_types = [event["event_type"] for event in timeline]
    assert "schema_validation_passed" in event_types
    assert "approval_approved" in event_types
    assert "adapter_execution_completed" in event_types
    assert "request_completed" in event_types
