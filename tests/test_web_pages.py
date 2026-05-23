def test_dashboard_renders_breakdowns_without_python_dict_repr(client):
    client.post(
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
            "free_text": "Synthetic worker change demo.",
        },
    )

    response = client.get("/dashboard")

    assert response.status_code == 200
    assert "{'worker_change': 1}" not in response.text
    assert "{'received': 1}" not in response.text
    assert "Requests by Type" in response.text
    assert "Worker Change" in response.text


def test_new_request_page_uses_public_safe_demo_forms(client):
    response = client.get("/requests/new")

    assert response.status_code == 200
    assert "http://127.0.0.1:4910" not in response.text
    assert "[worker_change_valid.json]" not in response.text
    assert "Create Worker Change" in response.text
    assert "Create Payroll Correction" in response.text


def test_new_request_form_creates_synthetic_request(client):
    response = client.post(
        "/requests/new",
        data={
            "request_type": "worker_change",
            "submitted_by": "Demo Requester",
            "submitted_by_email": "requester@example.test",
            "worker_id": "WKR-10001",
            "change_type": "department_update",
            "effective_date": "2026-07-01",
            "current_value": "Operations",
            "proposed_value": "Enterprise Systems",
            "requested_by_role": "manager",
            "simulate_failure": "none",
            "reason": "Department record needs to reflect a synthetic internal transfer.",
            "free_text": "Please update this synthetic worker's department after manager approval.",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"].startswith("/requests/")


def test_request_detail_supports_worker_change_ui_flow(client):
    create = client.post(
        "/requests/new",
        data={
            "request_type": "worker_change",
            "submitted_by": "Demo Requester",
            "submitted_by_email": "requester@example.test",
            "worker_id": "WKR-10001",
            "change_type": "department_update",
            "effective_date": "2026-07-01",
            "current_value": "Operations",
            "proposed_value": "Enterprise Systems",
            "requested_by_role": "manager",
            "simulate_failure": "none",
            "reason": "Department record needs to reflect a synthetic internal transfer.",
            "free_text": "Please update this synthetic worker's department after manager approval.",
        },
        follow_redirects=False,
    )
    request_url = create.headers["location"]

    detail = client.get(request_url)
    assert "Submit for Validation" in detail.text
    assert "{'approval_tasks'" not in detail.text

    submit = client.post(f"{request_url}/submit", follow_redirects=False)
    assert submit.status_code == 303

    pending_detail = client.get(request_url)
    assert "Approval Required: Manager" in pending_detail.text
    request_id = request_url.rsplit("/", 1)[-1]
    approval_id = client.get("/api/approvals/pending").json()[0]["id"]

    approve = client.post(
        f"{request_url}/approvals/{approval_id}/decision",
        data={"decision": "approved", "decision_by": "manager_demo_user", "comment": "Approved for UI demo."},
        follow_redirects=False,
    )

    assert approve.status_code == 303
    complete = client.get(f"/api/intake/requests/{request_id}").json()
    assert complete["status"] == "completed"
    assert client.get(request_url).text.count("Integration Artifacts") == 1


def test_request_detail_supports_retry_action_for_transient_failure(client):
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
            "free_text": "Please review this synthetic payroll correction.",
        },
    )
    request_id = create.json()["id"]
    client.post(f"/api/intake/requests/{request_id}/submit")
    approval_id = client.get("/api/approvals/pending").json()[0]["id"]
    client.post(f"/api/approvals/{approval_id}/decision", json={"decision": "approved", "decision_by": "payroll_reviewer"})
    job_id = client.get(f"/api/intake/requests/{request_id}").json()["integration_jobs"][0]["id"]

    failed_detail = client.get(f"/requests/{request_id}")
    assert "Retry Job" in failed_detail.text

    retry = client.post(f"/requests/{request_id}/jobs/{job_id}/retry", follow_redirects=False)

    assert retry.status_code == 303
    assert client.get(f"/api/intake/requests/{request_id}").json()["status"] == "completed"
