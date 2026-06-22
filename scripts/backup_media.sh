#!/usr/bin/env bash
set -euo pipefail

# Example wrapper script for production (Ubuntu)
# Place in /usr/local/bin/backup_media.sh and run from cron or systemd timer

# Load environment (adapt path to your secret store)
ENV_FILE=/etc/bolayetu/.env
if [[ -f "$ENV_FILE" ]]; then
  set -o allexport
  source "$ENV_FILE"
  set +o allexport
fi

# Defaults
PROJECT_DIR="/srv/bolayetu/backend"
PYTHON_BIN="/usr/bin/python3"
SCRIPT="$PROJECT_DIR/scripts/backup_and_upload_media.py"
BACKUP_DIR="/var/backups/bolayetu"

# Execute
cd "$PROJECT_DIR"
$PYTHON_BIN "$SCRIPT" --backup-dir "$BACKUP_DIR" --media-root "$PROJECT_DIR/media" --upload --remove-local-zip

# Example crontab (run daily at 02:00):
# 0 2 * * * /usr/local/bin/backup_media.sh >> /var/log/bolayetu/backup.log 2>&1
