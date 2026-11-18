# HomeCore Cloud staging — DigitalOcean

This is an initial staging workflow, **not a production-ready deployment**. The existing root `compose.yaml` remains development-only.

## Prerequisites
- Ubuntu Droplet with Docker Engine + Compose plugin.
- DNS A record for a staging hostname pointing to the Droplet. Do not run Caddy before DNS is ready.
- Inbound ports 80/443 allowed, PostgreSQL 5432 and Django 8000 not exposed.
- Dedicated `deploy` SSH user and GitHub environment `staging` with secrets `SSH_HOST`, `SSH_USER`, `SSH_PRIVATE_KEY`, `SSH_KNOWN_HOSTS`.
- Restrict staging environment deployments to trusted branches and require approval where available.

## One-time server preparation (as homecore sudo user)
The repo's `deploy/staging/` files must be transferred to the server using scp or an authenticated Git checkout. Example from Mac, with branch checked out:

```bash
scp deploy/staging/compose.yaml deploy/staging/Caddyfile deploy/staging/.env.example homecore@104.248.177.222:/opt/homecore/staging/
scp deploy/staging/deploy.sh homecore@104.248.177.222:/tmp/homecore-staging-deploy
```

On server:
```bash
cd /opt/homecore/staging
cp .env.example .env
nano .env
chmod 600 .env
sudo install -o root -g root -m 0755 /tmp/homecore-staging-deploy /usr/local/sbin/homecore-staging-deploy
sudo chown root:root /opt/homecore/staging/{compose.yaml,Caddyfile,.env}
sudo chmod 600 /opt/homecore/staging/.env
sudo chown root:root /opt/homecore
sudo chmod 755 /opt/homecore
sudo chmod 644 /opt/homecore/staging/compose.yaml /opt/homecore/staging/Caddyfile
sudo chown root:root /opt/homecore/staging
sudo chmod 755 /opt/homecore/staging
```

Configure `HOMECORE_DOMAIN`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`, `DJANGO_SECRET_KEY`, `POSTGRES_PASSWORD` in `.env`. Use strong random secrets (`python3 -c 'import secrets; print(secrets.token_urlsafe(48))'`). Keep `HOMECORE_IMAGE` as placeholder: deploy script overrides it with the digest-pinned image. The `deploy` user must not have write access to the compose, Caddyfile, env or deploy script.

### Restrict sudo to one root-owned command
Create `/etc/sudoers.d/homecore-deploy` with `sudo visudo -f /etc/sudoers.d/homecore-deploy`:
```
deploy ALL=(root) NOPASSWD: /usr/local/sbin/homecore-staging-deploy *
```
The script validates its sole argument against a fixed image repository and SHA-256 digest. Treat this delegation as privileged: GitHub Actions can deploy code, and code execution inside the container is a security-sensitive capability. Do not grant general sudo or Docker group membership.

### Private GHCR authentication
For a **private** image, create a GitHub classic PAT with only `read:packages` (and repository read permission if GitHub requires it). Store it only on the Droplet, not in the repository or chat. Authenticate Docker as root, since the restricted deploy script runs Docker as root:
```bash
sudo docker login ghcr.io -u YOUR_GITHUB_USERNAME
```
Paste the token when prompted (not your GitHub password). For better hygiene, use a dedicated machine account and credential helper, and rotate credentials. This setup is for staging only.

### Deploy
After merging into `develop`, wait for Actions → Staging Cloud image to succeed. Copy the complete digest-pinned image reference from the job summary. No SSH deployment is triggered by the merge. From your Mac, run (replace the digest):

```bash
ssh -i ~/.ssh/homecore_staging_deploy -o IdentitiesOnly=yes deploy@104.248.177.222 'sudo -n /usr/local/sbin/homecore-staging-deploy ghcr.io/moraisnetocc/homecare-cloud@sha256:REPLACE_WITH_DIGEST'
```

The script waits for PostgreSQL, runs migrations and collectstatic, starts services and checks public HTTPS health before persisting the image reference in .env. A failed check does not roll back containers or migrations. GitHub-hosted runners do not need inbound SSH access for this approach; keep SSH restricted to trusted client IPs. Existing staging secrets are reserved for a future approval-gated workflow.

Check `https://YOUR_STAGING_DOMAIN/api/health/` and `/api/docs/` after deploy.

### Limitations / follow-up
- Database backups and restore drills are required before real customer data.
- Add transactional rollback, deeper smoke tests, and secret rotation.
- The SSH deployment user must not be able to modify root-owned deploy files.
- Consider pinning third-party GitHub Actions and container images by digest for production.
- The current API media endpoint is publicly served; verify that uploaded images contain no sensitive data.
