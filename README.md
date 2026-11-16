# HomeCore — Sprint 001

Cloud Django multi-tenant foundation. Requires Docker with Compose.

```bash
cp .env.example .env
docker compose up --build -d
docker compose exec api python manage.py migrate
docker compose exec api python manage.py createsuperuser
docker compose exec api pytest
curl http://localhost:8000/api/health/
```

Admin: http://localhost:8000/admin/ . Health: `/api/health/`.

**Security:** This is a development-only scaffold. No tenant-scoped public API is exposed yet. Do not deploy publicly. Before exposing business data, implement tenant authorization, membership checks and tests for every endpoint. Local licenses, billing, HA integration and relay are later sprints.
