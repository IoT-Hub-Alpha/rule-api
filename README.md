# Rule API

Dedicated service for managing rule configuration.

## Quick Start

```bash
cp .env.example .env
uvicorn app.core.main:app --host 0.0.0.0 --port 8013 --reload
```

## Local Development With jwt-auth-lib

If `jwt-auth-lib` is checked out next to `rule-api` (sibling folders), install the
local editable package so the FastAPI integration is available while you work:

```bash
pip install -r requirements-local.txt
```

For Docker/CI builds or when you want the remote package, keep using
`requirements.txt` (it installs from the GitHub repo).

## Docker

```bash
docker build -t rule-api .
docker run --env-file .env -p 8013:8013 rule-api
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `RULE_API_DATABASE_URL` | SQLAlchemy Postgres URL (psycopg2) overrides all DB_* vars | Yes |
| `DATABASE_URL` | Generic SQLAlchemy Postgres URL fallback | No |
| `DB_HOST` | Postgres host (umbrella repo) | Yes (if RULE_API_DATABASE_URL not set) |
| `DB_PORT` | Postgres port (umbrella repo) | Yes (if RULE_API_DATABASE_URL not set) |
| `DB_NAME` | Postgres database name (umbrella repo) | Yes (if RULE_API_DATABASE_URL not set) |
| `DB_USER` | Postgres username (umbrella repo) | Yes (if RULE_API_DATABASE_URL not set) |
| `DB_PASSWORD` | Postgres password (umbrella repo) | Yes (if RULE_API_DATABASE_URL not set) |
| `RULE_API_CREATE_TABLES` | Auto-create tables on startup | No |
| `RULE_API_SQL_ECHO` | Enable SQL query logging | No |
| `JWT_SECRET_KEY` | JWT secret key used by jwt-auth-lib | Yes |
| `JWT_ALGORITHM` | JWT signing algorithm | No (default: HS256) |
| `INTERNAL_SERVICE_HEADER` | Header name for internal service bypass | No (default: X-Internal-Service) |

## JWT Authentication

All Rule API endpoints require a valid JWT and permissions. Permission checks are enforced using `jwt-auth-lib`.

Permissions used:
- `rules.view` for GET list and detail
- `rules.add` for POST create
- `rules.change` for PATCH update and enable/disable
- `rules.delete` for DELETE

Internal service requests can bypass JWT auth by sending the `X-Internal-Service` header (or the value of `INTERNAL_SERVICE_HEADER`).

## Endpoints

- `GET /v1/rules/`
- `GET /v1/rules/all`
- `POST /v1/rules/`
- `GET /v1/rules/{rule_id}/`
- `PATCH /v1/rules/{rule_id}/`
- `DELETE /v1/rules/{rule_id}/`
- `POST /v1/rules/{rule_id}/enable`
- `POST /v1/rules/{rule_id}/disable`
- `GET /health`
