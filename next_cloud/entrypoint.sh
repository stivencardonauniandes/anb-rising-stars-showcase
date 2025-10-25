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
su -s /bin/bash www-data -c "php /var/www/html/occ config:system:set trusted_domains 1 --value=nextcloud"
su -s /bin/bash www-data -c "php /var/www/html/occ config:system:set trusted_domains 2 --value=127.0.0.1"
su -s /bin/bash www-data -c "php /var/www/html/occ config:system:set trusted_domains 2 --value=98.84.32.245"
su -s /bin/bash www-data -c "php /var/www/html/occ config:system:set trusted_domains 2 --value=190.145.240.152"
su -s /bin/bash www-data -c "php /var/www/html/occ config:system:set trusted_domains 2 --value=api"
su -s /bin/bash www-data -c "php /var/www/html/occ config:system:set trusted_domains 2 --value=worker"

echo "Trusted domains configured. Creating folders..."

# Run the folder creation script
/setup_nextcloud_folders.sh

echo "Folders created successfully."

# Bring the Nextcloud process back to foreground
wait $NEXTCLOUD_PID