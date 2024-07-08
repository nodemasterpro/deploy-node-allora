#!/bin/bash
set -eu

YELLOW='\033[1;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

APP_HOME="/root/.allorad"
RESTORED_FLAG="${APP_HOME}/snapshot-restored.txt"
S3_BUCKET="allora-edgenet-backups"
LATEST_BACKUP_FILE_NAME="latest_backup.txt"
RCLONE_S3_NAME="allora_s3"

if [ ! -f "$RESTORED_FLAG" ]; then
  echo "Restoring the node from backup..."

  LATEST_BACKUP_FILE=$(rclone cat "$RCLONE_S3_NAME:$S3_BUCKET/$LATEST_BACKUP_FILE_NAME")
  LOGFILE="${APP_HOME}/restore.log"

  mkdir -p "${APP_HOME}/data"
  touch "$LOGFILE"
  rm -rf "${APP_HOME}/data/*"
  rclone -v cat "$RCLONE_S3_NAME:$S3_BUCKET/$LATEST_BACKUP_FILE" | tar --zstd -xvf - -C "${APP_HOME}/data" > "$LOGFILE" 2>&1
  tail -n 50 "$LOGFILE"

  echo "$LATEST_BACKUP_FILE" > "$RESTORED_FLAG"

  USER_ID=$(id -u)
  GROUP_ID=$(id -g)

  chown -R "$USER_ID:$GROUP_ID" "${APP_HOME}/data"
else
  RESTORED_SNAPSHOT=$(basename "$(cat "$RESTORED_FLAG")" .tar.zst)
  echo -e "Node already restored with snapshot ${GREEN}$RESTORED_SNAPSHOT${NC}"
  echo -e "${RED}To restore from the latest snapshot, remove the file: $RESTORED_FLAG${NC}"
fi
