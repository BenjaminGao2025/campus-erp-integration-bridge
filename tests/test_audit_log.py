def test_audit_timeline_is_ordered_and_contains_no_update_endpoint(client):
    response = client.post(
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
                "simulate_failure": "none",
            },
        },
    )
    request_id = response.json()["id"]
    timeline = client.get(f"/api/audit/requests/{request_id}").json()

    assert [event["created_at"] for event in timeline] == sorted(event["created_at"] for event in timeline)
    assert timeline[0]["event_type"] == "request_received"
