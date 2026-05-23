# Demo Script

## 2-Minute Recruiter Version

This is Campus ERP Integration Bridge, a synthetic, Workday-adjacent ERP-style integration prototype. It is not an official UBC project, does not use UBC branding or data, and does not connect to Workday.

In two minutes, I want to show that this is more than a CRUD app. It models how a campus-style operational request moves through intake, deterministic validation, approval routing, canonical mapping, adapter execution, retry handling, and audit logging.

The first flow is a worker change request. I create the request, submit it for validation, approve it, and then show the completed mock ERP adapter job. The request detail page shows the raw payload, the canonical payload, approval state, integration job, support notes, and adapter artifacts.

The second flow is a payroll correction request. It follows the same intake and approval pattern, but also generates outbound XML and validates it against XSD before a mock legacy payroll adapter records the result.

AI is assistive only. It can summarize and suggest classification, but validation, approval, audit, and record updates are deterministic and rule-based.

Suggested click path:

1. Open `/dashboard`.
2. Open `/requests/new` and create a Worker Change.
3. On the request detail page, submit it for validation, approve it, and show the completed job.
4. Open the audit timeline and point out deterministic events.

## 6-Minute Technical Version

This is a synthetic ERP-style integration bridge. The architecture is intentionally small, but the core surfaces are enterprise integration surfaces: an intake API, deterministic validation, approval routing, a canonical event model, integration jobs, mock adapters, PostgreSQL persistence, a support dashboard, and append-only audit events.

First, I open the architecture diagram and explain the two flows. Worker Change is the REST-style HCM flow. Payroll Correction is the legacy payroll-style flow with outbound XML and XSD validation.

Next, I run the Worker Change happy path. I create a request from the support console, submit it for JSON Schema and business-rule validation, approve it as a synthetic manager, and show the completed mock ERP REST adapter job. On the detail page, I point out the canonical payload, the approval task, the integration job, and the audit link.

Then I run the Payroll Correction flow. The important difference is that the outbound artifact is XML. I show the XML artifact and the XSD validation result, which demonstrates adapter contract validation at the integration boundary.

After that, I show the failure path. A transient payroll request fails on the first adapter attempt, becomes retryable, and then succeeds after retry. A permanent adapter failure is blocked from retry and returns a clear error. This is where the support console and audit timeline matter.

Finally, I open the audit timeline. I show correlation ID, event types, before and after state, validation results, payload hashes, and adapter error metadata. I finish by showing the test suite with `docker compose run --rm app pytest -q`.

The limitations are intentional: this is synthetic data only, no real Workday integration, no UBC branding or data, and AI is assistive only.
