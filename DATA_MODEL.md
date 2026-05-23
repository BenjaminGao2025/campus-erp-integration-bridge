# Data Model

## Core Tables

- `requests`: primary request record with request type, source, submitter, status, priority, correlation ID, and optional idempotency key.
- `request_payloads`: raw inbound payload, normalized canonical payload, schema version, and payload hash for idempotency/audit traceability.
- `approval_tasks`: synthetic approval workflow tasks with role, decision, decision actor, timestamp, and comment.
- `integration_jobs`: adapter execution state, target system, attempt count, max attempts, next retry timestamp, and last error.
- `integration_artifacts`: JSON/XML payloads sent to mock adapters plus payload hash and validation result.
- `audit_events`: chronological event trail for request and integration state changes, including before/after state, actor, validation result, redaction flags, and error metadata.
- `mock_workers`: synthetic worker records updated by the mock ERP REST adapter.
- `mock_payroll_records`: synthetic downstream payroll correction records written by the mock legacy payroll adapter.
- `support_notes`: AI summaries, analyst notes, and system notes. AI notes are advisory only.
- `policy_docs`: synthetic policy text for future support workflows.

## Canonical Event Model

After schema and business-rule validation, requests are mapped into a normalized canonical event:

- `canonical_event_id`: generated event identifier.
- `request_id`, `request_type`: source request linkage.
- `subject.worker_id`: synthetic worker reference.
- `domain`: `hcm` or `payroll`.
- `operation`: worker change type or payroll correction type.
- `risk`: priority and required approval roles.
- `data`: validated source payload.
- `metadata`: schema version, correlation ID, and creation timestamp.

## Request Status

`draft`, `received`, `validation_failed`, `pending_approval`, `approved`, `rejected`, `ready_for_integration`, `processing`, `completed`, `failed_retryable`, `failed_permanent`, `retry_scheduled`.

## Integration Job Status

`pending`, `processing`, `completed`, `failed_retryable`, `failed_permanent`, `retry_scheduled`.

## Audit Model

Audit events include:

- `request_id` and `correlation_id`
- actor type and actor ID
- event type
- before/after state
- payload hash
- validation result
- error code/message
- redaction flags
- metadata

Normal application services only append audit events. They do not update or delete previous audit events.
