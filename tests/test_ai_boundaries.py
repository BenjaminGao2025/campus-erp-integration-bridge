def test_ai_summary_endpoint_does_not_change_operational_state(client):
    before_metrics = client.get("/api/dashboard/metrics").json()

    response = client.post(
        "/api/ai/request-summary",
        json={
            "free_text": "A synthetic payroll request says a worker was underpaid.",
            "payload": {"worker_id": "WKR-10002"},
        },
    )

    assert response.status_code == 200
    assert response.json()["suggested_request_type"] == "payroll_correction"
    assert "AI is assistive only" in response.json()["limitations"]
    assert client.get("/api/dashboard/metrics").json() == before_metrics
