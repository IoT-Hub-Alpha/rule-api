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
| `RULE_API_DATABASE_URL` | SQLAlchemy database URL | Yes |
| `RULE_API_CREATE_TABLES` | Auto-create tables on startup | No |
| `RULE_API_SQL_ECHO` | Enable SQL query logging | No |

## Endpoints

- `GET /api/v1/rules/`
- `POST /api/v1/rules/`
- `GET /api/v1/rules/{rule_id}/`
- `PATCH /api/v1/rules/{rule_id}/`
- `DELETE /api/v1/rules/{rule_id}/`
- `POST /api/v1/rules/{rule_id}/enable`
- `POST /api/v1/rules/{rule_id}/disable`
- `GET /health`
