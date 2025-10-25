# Use the official PostgreSQL 15 Alpine image
FROM postgres:15-alpine

# Set environment variables
ENV POSTGRES_USER=postgres \
    POSTGRES_PASSWORD=postgres

# Expose PostgreSQL default port
EXPOSE 5432

# Copy your initialization script into the container
# (this runs automatically the first time the DB starts)
COPY ./db/init.sql /docker-entrypoint-initdb.d/init.sql

# Define a volume for PostgreSQL data persistence
VOLUME ["/var/lib/postgresql/data"]

# Healthcheck to verify PostgreSQL is ready
HEALTHCHECK --interval=10s --timeout=5s --retries=5 \
  CMD pg_isready -U postgres || exit 1
