# Sprint 002 — APIs multi-tenant

## Endpoints (v1)

All endpoints require authenticated users. The initial authentication mechanism is Django session authentication; production mobile/OIDC authentication is not implemented yet.

- GET/POST /api/v1/tenants/ — list memberships / create tenant and owner
- GET /api/v1/tenants/{id}/ — retrieve accessible tenant
- GET/POST /api/v1/tenants/{id}/members/ — owner/admin management
- GET/POST /api/v1/homes/ — list visible homes / owner/admin create
- GET /api/v1/homes/{id}/ — retrieve visible home
- GET/POST /api/v1/homes/{id}/members/ — tenant owner/admin or home owner management

## Security boundaries

- No anonymous access to v1 endpoints.
- No global superuser bypass in the API.
- Tenant memberships gate tenant reads.
- Home reads require direct home membership or tenant owner/admin role.
- Home creation requires tenant owner/admin role.
- Membership management checks permissions server-side.
- New home members must already belong to the home tenant.
- Owner transfers, member removal, and tenant updates are intentionally deferred.
- Tenant creation is currently open to any authenticated user; product provisioning and quotas are future work.
- Session-authenticated unsafe requests require CSRF protection.

## Validation

Run:

```bash
docker compose exec api python manage.py check
docker compose exec api python manage.py makemigrations --check --dry-run
docker compose exec api pytest -q
```

No model changes or migrations are required in this sprint.
