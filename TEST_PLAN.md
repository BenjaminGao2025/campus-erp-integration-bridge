# Test Plan

## Automated Tests

Run:

```bash
docker compose run --rm app pytest -q
```

Coverage areas:

- Worker change happy path.
- Payroll correction happy path with XML generation and XSD validation.
- JSON Schema validation failure.
- Idempotency success and conflict cases.
- Transient adapter failure and retry.
- Permanent adapter failure and blocked retry.
- Audit timeline ordering and event presence.
- AI boundary behavior.
- XML/XSD direct validation behavior.
- Web support console rendering and UI submit/approve/retry paths.

## Manual QA Checklist

- App loads at `/`.
- API docs load at `/docs`.
- `GET /health` returns `{"status":"ok"}`.
- Sample payloads return from `/api/demo/sample-payloads`.
- Worker change can be created, submitted, approved, and completed from the UI.
- Payroll correction can be created, submitted, approved, and completed from the UI or API.
- Transient payroll sample fails once and completes after retry.
- Permanent failure sample cannot be retried.
- Audit timeline shows schema, approval, adapter, retry, and completion events.
