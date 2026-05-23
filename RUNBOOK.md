# Runbook

## Start App

```bash
git clone <repo-url>
cd campus-erp-integration-bridge
cp -n .env.example .env
docker compose up --build -d
```

The local app listens on `http://127.0.0.1:4910` by default. To use another host port, change `APP_HOST_PORT` in `.env` before starting the stack.

## Seed Data

```bash
docker compose exec app python -m scripts.seed_demo_data
```

## Reset Database

```bash
docker compose exec app python -m scripts.reset_db
```

The HTTP reset endpoint `DELETE /api/demo/reset` is protected by `DEMO_MODE=true`. If `DEMO_MODE=false`, the endpoint returns `403` and does not reset data. The local `scripts.reset_db` command is still intentionally available for developer-controlled local demo resets.

## Submit Demo Request

UI path:

1. Open `http://127.0.0.1:4910/requests/new`.
2. Create a Worker Change or Payroll Correction.
3. Open the created request detail page and click **Submit for Validation**.

API path:

```bash
curl -s -X POST http://127.0.0.1:4910/api/intake/requests \
  -H 'Content-Type: application/json' \
  -H 'Idempotency-Key: demo-worker-1' \
  -d @sample_payloads/worker_change_valid.json
```

Then submit it:

```bash
curl -s -X POST http://127.0.0.1:4910/api/intake/requests/{request_id}/submit
```

## Approve Request

UI path:

1. Open the request detail page.
2. Use the approval form under **Workflow Actions**.
3. Confirm status and integration job state on the same page.

API path:

```bash
curl -s http://127.0.0.1:4910/api/approvals/pending
curl -s -X POST http://127.0.0.1:4910/api/approvals/{approval_id}/decision \
  -H 'Content-Type: application/json' \
  -d '{"decision":"approved","decision_by":"synthetic_reviewer","comment":"Approved for demo."}'
```

## Retry Failed Job

UI path:

1. Create a request with `simulate_failure=transient`.
2. Submit and approve it.
3. Open the request detail page and click **Retry Job**.

API path:

```bash
curl -s -X POST http://127.0.0.1:4910/api/jobs/{job_id}/retry
```

## Troubleshooting

- `port is already allocated`: change host port `4910` in `docker-compose.yml`.
- `database connection failed`: wait for Postgres healthcheck or restart with `docker compose restart db app`.
- `validation_failed`: inspect `GET /api/audit/requests/{request_id}` and request detail.
- `failed_retryable`: retry from API or support console.
- `failed_permanent`: inspect adapter error; retry is intentionally blocked.
