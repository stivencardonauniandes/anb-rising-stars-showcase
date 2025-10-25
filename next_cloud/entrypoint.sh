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

echo "Nextcloud is ready. Configuring trusted domains..."

# Configure trusted domains via occ command
su -s /bin/bash www-data -c "php /var/www/html/occ config:system:set trusted_domains 0 --value=localhost"
su -s /bin/bash www-data -c "php /var/www/html/occ config:system:set trusted_domains 1 --value=10.0.5.46"
su -s /bin/bash www-data -c "php /var/www/html/occ config:system:set trusted_domains 2 --value=3.90.52.76"
su -s /bin/bash www-data -c "php /var/www/html/occ config:system:set trusted_domains 3 --value=98.98.186.148"
su -s /bin/bash www-data -c "php /var/www/html/occ config:system:set trusted_domains 4 --value=54.237.229.253"
su -s /bin/bash www-data -c "php /var/www/html/occ config:system:set trusted_domains 5 --value=10.0.7.94"

echo "Trusted domains configured. Creating folders..."

# Run the folder creation script
/next_cloud/setup_nextcloud_folders.sh

echo "Folders created successfully."

# Bring the Nextcloud process back to foreground
wait $NEXTCLOUD_PID
