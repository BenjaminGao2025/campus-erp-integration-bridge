# Architecture

## Component Diagram

```mermaid
flowchart TD
  Portal["Mock Service Portal / Support Console"] --> Intake["FastAPI Intake Routes"]
  Intake --> AIAssist["Mock AI Assist Service"]
  Intake --> Schema["JSON Schema Validator"]
  Schema --> Rules["Business Rules Engine"]
  Rules --> Approval["Approval Service"]
  Approval --> Orchestrator["Orchestration Service"]
  Orchestrator --> Queue["Integration Job Model"]
  Queue --> Adapter["Adapter Service"]
  Adapter --> Rest["Mock ERP REST Adapter"]
  Adapter --> Payroll["Mock Legacy Payroll XML Adapter"]
  Payroll --> XSD["XSD Validator"]
  Rest --> Data[(PostgreSQL)]
  XSD --> Data
  Intake --> Audit["Audit Service"]
  Rules --> Audit
  Approval --> Audit
  Adapter --> Audit
  Data --> Metrics["Dashboard Metrics"]
```

## Worker Change Sequence

```mermaid
sequenceDiagram
  participant User
  participant API
  participant Rules
  participant Approver
  participant Adapter
  participant DB
  User->>API: POST /api/intake/requests
  API->>DB: request + payload + audit
  User->>API: POST /submit
  API->>Rules: JSON Schema + business rules
  Rules->>DB: canonical event + approval task + audit
  Approver->>API: approval decision
  API->>Adapter: mock ERP REST adapter
  Adapter->>DB: update synthetic worker + artifact + audit
  API->>DB: request completed
```

## Payroll Correction Sequence

```mermaid
sequenceDiagram
  participant User
  participant API
  participant Rules
  participant Approver
  participant XML
  participant Adapter
  participant DB
  User->>API: POST /api/intake/requests
  User->>API: POST /submit
  API->>Rules: JSON Schema + payroll rules
  Rules->>DB: canonical event + approval task
  Approver->>API: approval decision
  API->>XML: generate outbound XML
  XML->>XML: validate against XSD
  XML->>Adapter: mock legacy payroll adapter
  Adapter->>DB: payroll record + artifact + audit
```

## Deterministic Validation

Validation is layered:

- JSON Schema validates inbound payload shape.
- Business rules validate dates, worker existence, priority, and approval requirements.
- XSD validates payroll outbound XML.
- AI output is not accepted as final validation.

## Adapter Layer

The adapter layer receives canonical events and writes synthetic downstream records. It intentionally uses generic names: mock ERP REST system and mock legacy payroll system. There are no fake Workday tenants, credentials, endpoints, or official system names.

## Runtime Contract

The main workflow is deliberately service-layer driven rather than route-handler driven:

- `intake_service` creates requests, hashes payloads, applies idempotency, writes audit events, and creates canonical events.
- `approval_service` records human decisions and hands approved requests to orchestration.
- `orchestration_service` creates integration jobs, runs adapters, records retryable/permanent failures, and updates request/job status.
- `adapter_service` writes JSON/XML artifacts and mutates only synthetic downstream tables.
- `audit.write_audit_event` is the single normal path for audit event creation.

## Retry And Failure Path

`simulate_failure=transient` fails the first adapter attempt and allows `POST /api/jobs/{job_id}/retry` to complete the job. `simulate_failure=permanent` creates a permanent failure and retry returns a conflict.

## AI Boundaries

AI assist can summarize, suggest type, hint missing fields, and draft next action. It never approves, writes records, validates finally, changes permissions, or creates audit truth.
