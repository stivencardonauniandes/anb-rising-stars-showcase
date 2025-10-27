# Use the official Nextcloud image
FROM nextcloud:latest

# Set environment variables
ENV NEXTCLOUD_ADMIN_USER=worker \
    NEXTCLOUD_ADMIN_PASSWORD=super-secret \
    NEXTCLOUD_TRUSTED_DOMAINS=

# Expose the HTTP port
EXPOSE 80

# Create directories and copy custom entrypoint or configuration
# (Your ./next_cloud folder from the host is copied here)
COPY ./next_cloud /next_cloud

# Ensure entrypoint is executable
RUN chmod +x /next_cloud/entrypoint.sh

# Define volumes (data persistence)
VOLUME ["/var/www/html"]

# Healthcheck to ensure Nextcloud is up
HEALTHCHECK --interval=30s --timeout=10s --retries=5 --start-period=60s \
  CMD curl -f http://localhost/status.php || exit 1

# Set custom entrypoint
ENTRYPOINT ["/next_cloud/entrypoint.sh"]

# Default command to run Apache in foreground
CMD ["apache2-foreground"]
