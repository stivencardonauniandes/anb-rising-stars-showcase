#!/bin/bash

# Wait for the database to be ready
echo "⏳ Waiting for database to be ready..."
while ! python -c "
import psycopg2
import os
try:
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    conn.close()
    print('✅ Database is ready!')
except:
    print('❌ Database not ready yet...')
    exit(1)
"; do
    sleep 2
done

# Run database migrations
echo "🔄 Running database migrations..."
alembic upgrade head

# Check if migrations were successful
if [[ $? -eq 0 ]]; then
    echo "✅ Migrations completed successfully!"
else
    echo "❌ Migration failed!"
    exit 1
fi

# Start the application with workers for better concurrency
echo "🚀 Starting API server with workers..."
# Use 4 workers for better concurrency (adjust based on CPU cores)
exec uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
