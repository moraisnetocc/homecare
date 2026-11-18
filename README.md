# HomeCore — Monorepo

Independent services with independent dependencies and Docker builds:

- `cloud/`: Django REST API, PostgreSQL, JWT, Swagger, tenants, homes, catalog.
- `agent/`: lightweight Python asyncio service, SQLite; ARM64/AMD64 compatible base image.
- `deploy/local/`: local agent Compose file.
- `contracts/`: future versioned cloud-agent protocol.

## Cloud (same root commands as before)

```bash
cp .env.example .env
docker compose up --build -d
docker compose exec api python manage.py migrate
docker compose exec api pytest -q
```

Swagger: http://localhost:8000/api/docs/

## Agent (standalone)

```bash
docker compose -f deploy/local/compose.yaml up --build -d
curl http://127.0.0.1:8081/health
```

Agent tests: `pip install -e './agent[test]' && pytest -q agent/tests`.

The agent does not connect to Home Assistant or the cloud yet. Its health endpoint is bound to localhost on the host; do not expose it publicly. Cloud and agent releases are independent.
