#!/bin/bash

# Script to create 'raw' and 'processed' folders in Nextcloud
# Assumes Nextcloud is running on localhost:8080 with admin user 'worker' and password 'super-secret'

NEXTCLOUD_URL="http://localhost"
USERNAME="worker"
PASSWORD="super-secret"
USER_DIR="remote.php/dav/files/$USERNAME"

# Function to create folder
create_folder() {
    local folder=$1
    echo "Creating folder: $folder"
    curl -X MKCOL -u "$USERNAME:$PASSWORD" "$NEXTCLOUD_URL/$USER_DIR/$folder"
    if [ $? -eq 0 ]; then
        echo "Successfully created folder: $folder"
    else
        echo "Failed to create folder: $folder"
    fi
}

# Create raw folder
create_folder "raw"

# Create processed folder
create_folder "processed"

echo "Folder creation script completed."