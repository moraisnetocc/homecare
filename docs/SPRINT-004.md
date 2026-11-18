# Sprint 004 — monorepo and agent foundation

- Django files moved to `cloud/` without changing Python import paths or Django app labels; existing database migrations remain valid.
- Root Compose now builds `./cloud` and mounts `./cloud:/app`, retaining the original PostgreSQL and media named volumes.
- Agent has independent Python packaging, SQLite persistence, asyncio health service, Dockerfile and Compose.
- Cloud and agent CI use path filters and independent dependency installs.
- No HA integration, device control, pairing or cloud communication in this sprint.
- ARM64 and AMD64 are supported by the official multi-platform Python base image; publishing multi-platform images requires a subsequent buildx release workflow.
- Local agent HTTP endpoint must remain private. No public API auth is implemented for it.

## Validation

```bash
cp .env.example .env
docker compose up --build -d
docker compose exec api python manage.py migrate
docker compose exec api python manage.py makemigrations --check --dry-run
docker compose exec api pytest -q
docker compose -f deploy/local/compose.yaml up --build -d
curl http://127.0.0.1:8081/health
pip install -e './agent[test]'
pytest -q agent/tests
```
