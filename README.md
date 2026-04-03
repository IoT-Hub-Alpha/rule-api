# Rule API

Dedicated service for managing rule configuration.

## Quick Start

```bash
cp .env.example .env
uvicorn app.core.main:app --host 0.0.0.0 --port 8011 --reload
```

## Docker

```bash
docker build -t rule-api .
docker run --env-file .env -p 8011:8011 rule-api
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
