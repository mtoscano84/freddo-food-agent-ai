#!/bin/bash

# Get current date and minutes in DDMMYYYYHHMM format
DATE=$(date +%d%m%Y%H%M)

# Set source and destination paths
SOURCE_DIR="/Users/mtoscano/Sandbox/freddo-food-agent-ai"
BACKUP_DIR="/Users/mtoscano/Sandbox/backups"
BACKUP_FILE="$DATE-freddo-project.bck"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Create tar archive
echo "Creating backup of freddo-project..."
tar -czf "$BACKUP_DIR/$BACKUP_FILE" -C "$(dirname "$SOURCE_DIR")" "$(basename "$SOURCE_DIR")"

# Check if backup was successful
if [ $? -eq 0 ]; then
    echo "Backup completed successfully: $BACKUP_DIR/$BACKUP_FILE"
else
    echo "Backup failed!"
    exit 1
fi
