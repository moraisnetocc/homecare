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
sudo chown root:root /opt/homecore/staging/compose.yaml /opt/homecore/staging/Caddyfile
sudo chmod 644 /opt/homecore/staging/compose.yaml /opt/homecore/staging/Caddyfile
sudo chown root:root /opt/homecore/staging
sudo chmod 755 /opt/homecore/staging
```

Configure `HOMECORE_DOMAIN`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`, `DJANGO_SECRET_KEY`, `POSTGRES_PASSWORD` in `.env`. Use strong random secrets (`python3 -c 'import secrets; print(secrets.token_urlsafe(48))'`). Keep `HOMECORE_IMAGE` as placeholder: deploy script overrides it with the SHA-tagged image. The `deploy` user must not have write access to the compose, Caddyfile, env or deploy script.

### Restrict sudo to one root-owned command
Create `/etc/sudoers.d/homecore-deploy` with `sudo visudo -f /etc/sudoers.d/homecore-deploy`:
```
deploy ALL=(root) NOPASSWD: /usr/local/sbin/homecore-staging-deploy *
```
The script validates its sole argument against a fixed image repository and SHA-shaped tag. Treat this delegation as privileged: GitHub Actions can deploy code, and code execution inside the container is a security-sensitive capability. Do not grant general sudo or Docker group membership.

### Private GHCR authentication
For a **private** image, create a GitHub classic PAT with only `read:packages` (and repository read permission if GitHub requires it). Store it only on the Droplet, not in the repository or chat. Authenticate Docker as root, since the restricted deploy script runs Docker as root:
```bash
sudo docker login ghcr.io -u YOUR_GITHUB_USERNAME
```
Paste the token when prompted (not your GitHub password). For better hygiene, use a dedicated machine account and credential helper, and rotate credentials. This setup is for staging only.

### Deploy
After merging the PR into `develop`, go to Actions → Staging Cloud deploy → Run workflow. Provide the full 40-character commit SHA from `develop`. The workflow builds/pushes an immutable SHA-tagged image and invokes the server deploy script over verified SSH. Ensure the `staging` environment secrets are present.

Check `https://YOUR_STAGING_DOMAIN/api/health/` and `/api/docs/` after deploy.

### Limitations / follow-up
- Database backups and restore drills are required before real customer data.
- Add automated deployment smoke tests, rollback, and secret rotation.
- The SSH deployment user must not be able to modify root-owned deploy files.
- Consider pinning third-party GitHub Actions and container images by digest for production.
- The current API media endpoint is publicly served; verify that uploaded images contain no sensitive data.
