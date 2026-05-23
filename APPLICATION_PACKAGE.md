# Application Package

## Live Links

- Live demo: https://demo.gaoyuze.com/
- API docs: https://demo.gaoyuze.com/docs
- Health check: https://demo.gaoyuze.com/health

## What To Click First

1. Open the live demo.
2. Click **New Request**.
3. Create a **Worker Change** request.
4. On the request detail page, click **Submit for Validation**.
5. Approve the request and open the audit timeline.

## 2-Minute Demo Path

Open the dashboard and explain that the project models enterprise integration behavior rather than generic CRUD. Create a Worker Change, submit it, approve it, and show the completed integration job. Open the audit timeline and point out deterministic validation, approval, adapter execution, and completion events. Mention that the Payroll Correction flow adds XML generation, XSD validation, transient failure, and retry.

## 6-Minute Technical Demo Path

1. Show the architecture in `ARCHITECTURE.md`.
2. Run the Worker Change happy path from the UI.
3. Show the canonical payload, approval task, integration job, and audit timeline.
4. Run or inspect the Payroll Correction path and its XML artifact.
5. Demonstrate transient adapter failure and retry.
6. Open `/docs` and show the API contracts.
7. Point to the pytest suite and run `docker compose run --rm app pytest -q`.

## What This Proves

- API intake with idempotency and correlation IDs.
- JSON Schema, business-rule, and XSD validation.
- Human approval routing before downstream writes.
- Canonical event mapping before adapter execution.
- Mock REST and XML adapter boundaries.
- Retry/error handling and support-console visibility.
- Append-only audit logging through normal service flows.
- AI boundaries: summaries and suggestions only.

## What This Does Not Claim

This is a synthetic, Workday-adjacent ERP-style integration prototype. It is not an official UBC project, does not use UBC branding or data, and does not connect to Workday.

It also does not claim real Workday Extend, Workday Orchestrate, ServiceNow, Jira, production ERP access, real credentials, real tenants, or real institutional data.
