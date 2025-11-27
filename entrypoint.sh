#!/bin/bash
set -e  # Exit on error (will be temporarily disabled for migration attempts)

echo "=== Starting Horilla Deployment ==="

# Disable schedulers during migration
export SKIP_SCHEDULERS=1

# Railway PostgreSQL is ready immediately, skip wait if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "⚠ DATABASE_URL not set, using SQLite or custom database config"
else
    echo "✓ Using Railway PostgreSQL (DATABASE_URL detected)"
fi

echo "Step 1: Initializing database..."
# Run migrations with fallback strategies
echo "Running migrations..."

# Try standard migration first - show output
set +e  # Don't exit on error
python3 manage.py migrate --noinput
MIGRATE_EXIT_CODE=$?
set -e

if [ $MIGRATE_EXIT_CODE -eq 0 ]; then
    echo "✓ Migrations completed successfully"
else
    echo "⚠ Standard migration failed with exit code $MIGRATE_EXIT_CODE"
    echo "Trying --run-syncdb..."
    
    set +e
    python3 manage.py migrate --run-syncdb --noinput
    SYNCDB_EXIT_CODE=$?
    set -e
    
    if [ $SYNCDB_EXIT_CODE -eq 0 ]; then
        echo "✓ Migrations completed with --run-syncdb"
    else
        echo "⚠ Syncdb also failed. Trying --fake-initial..."
        python3 manage.py migrate --fake-initial --noinput || echo "⚠ Migration failed - database may be in inconsistent state"
    fi
fi

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
