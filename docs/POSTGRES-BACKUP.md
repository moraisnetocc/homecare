# PostgreSQL backup and recovery

Initial scope: local logical backups, monthly on day 1 at 03:00 America/Sao_Paulo, retention of the six latest successful archives. PostgreSQL custom-format archives are compressed by default. Archives are sensitive; directory 0700, files 0600, root only. No application credentials need to be copied out of the database container. This does not cover media volumes, database global roles or external secrets. A local backup is not disaster recovery if the droplet is lost. Offsite encrypted storage and alerting are follow-up requirements before production.

## Installation (staging)

From a reviewed checkout, upload the four files in deploy/backup to a private directory in the homecore user's home (do not upload directly to root-owned paths). On the VPS, from that directory:

```bash
sudo bash -n backup.sh
sudo bash -n restore-test.sh
sudo install -o root -g root -m 755 backup.sh /usr/local/sbin/homecore-postgres-backup
sudo install -o root -g root -m 755 restore-test.sh /usr/local/sbin/homecore-postgres-restore-test
sudo install -o root -g root -m 644 homecore-postgres-backup@.{service,timer} /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl start homecore-postgres-backup@staging.service
sudo journalctl -u homecore-postgres-backup@staging.service -n 30 --no-pager
sudo ls -lh /var/backups/homecore/staging/
```

Run a restore test with an exact archive path from the listing:

```bash
sudo /usr/local/sbin/homecore-postgres-restore-test staging /var/backups/homecore/staging/postgres-YYYYMMDDTHHMMSSZ.dump
```

The test uses a temporary database in the same PostgreSQL instance, not the active application database, and drops it afterward. It restores schema/data and checks django_migrations. Run during low traffic with sufficient disk space; it consumes resources and is not a fully isolated server or a complete business-data validation. If interrupted abruptly, inspect leftover homecore_restore_test_* databases before manual cleanup. Do not drop the live database.

After success:

```bash
sudo systemctl enable --now homecore-postgres-backup@staging.timer
systemctl list-timers homecore-postgres-backup@staging.timer
```

Check disk utilization and journal periodically. Retention keeps the six newest matching archives (including manual backups), deleting older ones only after a new archive passes structural validation. Failed backups do not prune existing archives. This is count-based retention, not a fixed six-month TTL. Monthly backups can lose a month of changes or more if a run fails; revisit frequency before production. The timer catches missed scheduled runs after downtime. Test restoration regularly. Run an additional backup on demand using sudo systemctl start homecore-postgres-backup@staging.service. Production usage requires a separate compose installation at /opt/homecore/production and explicit activation; do not activate it yet. For real recovery, restore to a fresh database/instance, validate data and application compatibility before switching traffic. Never overwrite the live database as a routine test.
