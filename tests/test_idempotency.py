from http import HTTPStatus


def _payload(reason="Department record needs to reflect a synthetic internal transfer."):
    return {
        "request_type": "worker_change",
        "submitted_by": "Demo Requester",
        "submitted_by_email": "requester@example.test",
        "payload": {
            "worker_id": "WKR-10001",
            "change_type": "department_update",
            "effective_date": "2026-07-01",
            "current_value": "Operations",
            "proposed_value": "Enterprise Systems",
            "reason": reason,
            "requested_by_role": "manager",
            "simulate_failure": "none",
        },
    }


def test_same_idempotency_key_and_same_payload_returns_existing_request(client):
    first = client.post("/api/intake/requests", headers={"Idempotency-Key": "same-key"}, json=_payload())
    second = client.post("/api/intake/requests", headers={"Idempotency-Key": "same-key"}, json=_payload())

    assert first.status_code == HTTPStatus.CREATED
    assert second.status_code == HTTPStatus.OK
    assert first.json()["id"] == second.json()["id"]


def test_same_idempotency_key_and_different_payload_returns_conflict(client):
    first = client.post("/api/intake/requests", headers={"Idempotency-Key": "conflict-key"}, json=_payload())
    second = client.post(
        "/api/intake/requests",
        headers={"Idempotency-Key": "conflict-key"},
        json=_payload(reason="Different synthetic reason that changes payload hash."),
    )

    assert first.status_code == HTTPStatus.CREATED
    assert second.status_code == HTTPStatus.CONFLICT
