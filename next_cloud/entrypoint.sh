#!/bin/bash

# Custom entrypoint for Nextcloud that creates folders after startup

# Run the original Nextcloud entrypoint in the background
/entrypoint.sh "$@" &

NEXTCLOUD_PID=$!

# Wait for Nextcloud to be ready
echo "Waiting for Nextcloud to be ready..."
while ! curl -f http://localhost/status.php > /dev/null 2>&1; do
  sleep 10
done

echo "Nextcloud is ready. Creating folders..."

# Run the folder creation script
/next_cloud/setup_nextcloud_folders.sh

echo "Folders created successfully."

# Bring the Nextcloud process back to foreground
wait $NEXTCLOUD_PID