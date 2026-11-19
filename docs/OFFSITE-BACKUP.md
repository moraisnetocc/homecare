# Encrypted offsite PostgreSQL backups (R2)

Separate service triggered by OnSuccess of the local backup. It can be retried independently. Six latest timestamped encrypted objects per environment; no remote pruning until all missing local archives have been uploaded and byte-compared against the remote. Existing remote names are trusted and skipped; periodically perform an actual recovery drill. If remote upload succeeds but verification fails, inspect/delete that specific object before retrying. Remote credentials allow deletion, so this is not immutable ransomware protection. Media and secrets are not included.

## Setup

On the Mac, install age (brew install age), then generate a dedicated recovery key in a private directory with umask 077 using age-keygen -o homecore-staging.agekey. Save the private key in two secure offline locations, never upload it to the VPS or GitHub. Export the public recipient using age-keygen -y homecore-staging.agekey > recipient.txt. Production must use separate keys and credentials.

On the VPS install age and rclone with apt. Create /etc/homecore/backup/staging with root ownership and mode 0700. Install recipient.txt there as root mode 0600. Create rclone.conf there as root mode 0600 (sudoedit after creating with install -m 600 /dev/null). Contents:

```ini
[r2]
type = s3
provider = Cloudflare
access_key_id = REPLACE
secret_access_key = REPLACE
endpoint = https://ACCOUNT_ID.r2.cloudflarestorage.com
region = auto
no_check_bucket = true
```

Use the actual S3 endpoint from the dashboard. Bucket homecore-backups-staging must already exist and be private. Token scoped to this bucket, object read/write. No secrets in shell history or source control.

Upload reviewed files to a private directory in the homecore user's home. Install:

```bash
bash -n offsite.sh
sudo install -o root -g root -m 755 offsite.sh /usr/local/sbin/homecore-postgres-offsite
sudo install -o root -g root -m 644 homecore-postgres-offsite@.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl start homecore-postgres-offsite@staging.service
sudo journalctl -u homecore-postgres-offsite@staging.service -n 30 --no-pager
```

Verify the object in the private bucket. Download it using the Cloudflare dashboard to the trusted Mac (or use separately authorized credentials), decrypt with age -d -i homecore-staging.agekey -o recovered.dump downloaded.dump.age; compare SHA-256 with original and perform isolated restore using existing restore-test.sh. Protect and delete plaintext recovery copies when finished. Never transfer the private key to the server.

Only after a successful recovery test install the updated homecore-postgres-backup@.service (adds OnSuccess trigger), daemon-reload, and verify the existing monthly timer remains enabled. Retry offsite manually via systemctl start homecore-postgres-offsite@staging.service. A failed remote service does not mark local backup failed. Monitor journal for failures; automatic retry/alerting not yet implemented. Never use rclone sync on the bucket. Do not configure remote TTL. 
