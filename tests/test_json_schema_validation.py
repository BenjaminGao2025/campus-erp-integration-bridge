from http import HTTPStatus


def test_missing_required_field_fails_schema_validation(client):
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
                "requested_by_role": "manager",
            },
        },
    )
    assert response.status_code == HTTPStatus.CREATED
    request_id = response.json()["id"]

    submit = client.post(f"/api/intake/requests/{request_id}/submit")
    assert submit.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert submit.json()["status"] == "validation_failed"

    event_types = [event["event_type"] for event in client.get(f"/api/audit/requests/{request_id}").json()]
    assert "schema_validation_failed" in event_types
