Backup scripts for production

Files:
- backup_and_upload_media.py : Python script that zips MEDIA_ROOT and uploads to Cloudflare R2.
- backup_media.sh : Bash wrapper for Ubuntu (loads /etc/bolayetu/.env and runs the python script).
- backup_media.ps1 : PowerShell wrapper for local/dev usage.

Usage (production):
1. Place your secrets in /etc/bolayetu/.env (CLOUDFLARE_R2_* vars and CLOUDFLARE_CDN_DOMAIN).
2. Ensure script is executable: sudo chmod +x /usr/local/bin/backup_media.sh
3. Add to cron or systemd timer to run regularly.

Example env variables (in /etc/bolayetu/.env):
CLOUDFLARE_R2_ACCESS_KEY=...
CLOUDFLARE_R2_SECRET_KEY=...
CLOUDFLARE_R2_BUCKET=bolayetu-media
CLOUDFLARE_R2_ENDPOINT=https://<account-id>.r2.cloudflarestorage.com
CLOUDFLARE_CDN_DOMAIN=cdn.bolayetu.com

Safety:
- The script will refuse to purge media unless upload completed successfully.
- Keep backups in an external archive for disaster recovery.
