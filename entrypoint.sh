#!/bin/bash

echo "=== Starting Horilla Deployment ==="

# Disable schedulers during migration
export SKIP_SCHEDULERS=1

# Wait for database to be ready (important for Railway)
echo "Waiting for database to be ready..."
max_retries=30
retry_count=0

while [ $retry_count -lt $max_retries ]; do
    if python3 -c "import django; django.setup(); from django.db import connection; connection.ensure_connection()" 2>/dev/null; then
        echo "✓ Database is ready!"
        break
    fi
    retry_count=$((retry_count + 1))
    echo "Waiting for database... ($retry_count/$max_retries)"
    sleep 2
done

if [ $retry_count -eq $max_retries ]; then
    echo "✗ Database connection timeout. Exiting..."
    exit 1
fi

echo "Step 1: Initializing database..."
# Use custom command for safe migration
python3 manage.py init_railway_db || {
    echo "⚠ Custom migration failed, trying standard approach..."
    
    # Fallback to standard migrations
    python3 manage.py migrate contenttypes --noinput
    python3 manage.py migrate auth --noinput
    python3 manage.py migrate --noinput || {
        echo "⚠ Standard migration failed, trying with --run-syncdb..."
        python3 manage.py migrate --run-syncdb --noinput || {
            echo "⚠ Syncdb failed, using --fake-initial as last resort..."
            python3 manage.py migrate --fake-initial --noinput
        }
    }
}

echo "Step 2: Collecting static files..."
python3 manage.py collectstatic --noinput --clear || {
    echo "⚠ Static files collection failed, continuing..."
}

echo "Step 3: Creating admin user (if not exists)..."
python3 manage.py createhorillauser \
    --first_name admin \
    --last_name admin \
    --username admin \
    --password admin \
    --email admin@example.com \
    --phone 1234567890 2>/dev/null || echo "ℹ Admin user already exists or creation skipped"

# Re-enable schedulers for server
unset SKIP_SCHEDULERS

echo "Step 4: Starting Gunicorn server on port ${PORT:-8000}..."
echo "✓ Deployment complete! Application starting..."

exec gunicorn \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers ${GUNICORN_WORKERS:-2} \
    --threads ${GUNICORN_THREADS:-4} \
    --timeout 120 \
    --log-level info \
    --access-logfile - \
    --error-logfile - \
    --worker-class sync \
    horilla.wsgi:application
