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
echo "=== STARTING MIGRATIONS ==="
echo "DATABASE_URL status: ${DATABASE_URL:+SET}"
echo "Current directory: $(pwd)"
echo "Python version: $(python3 --version)"

# Try standard migration first - show output
set +e  # Don't exit on error
echo ">>> Executing: python3 manage.py migrate --noinput"
python3 manage.py migrate --noinput 2>&1
MIGRATE_EXIT_CODE=$?
echo ">>> Migration exit code: $MIGRATE_EXIT_CODE"
set -e

if [ $MIGRATE_EXIT_CODE -eq 0 ]; then
    echo "✓✓✓ MIGRATIONS COMPLETED SUCCESSFULLY ✓✓✓"
else
    echo "⚠⚠⚠ STANDARD MIGRATION FAILED (exit code: $MIGRATE_EXIT_CODE) ⚠⚠⚠"
    echo ">>> Trying --run-syncdb..."
    
    set +e
    echo ">>> Executing: python3 manage.py migrate --run-syncdb --noinput"
    python3 manage.py migrate --run-syncdb --noinput 2>&1
    SYNCDB_EXIT_CODE=$?
    echo ">>> Syncdb exit code: $SYNCDB_EXIT_CODE"
    set -e
    
    if [ $SYNCDB_EXIT_CODE -eq 0 ]; then
        echo "✓✓✓ MIGRATIONS COMPLETED WITH --run-syncdb ✓✓✓"
    else
        echo "⚠⚠⚠ SYNCDB ALSO FAILED (exit code: $SYNCDB_EXIT_CODE) ⚠⚠⚠"
        echo ">>> Trying --fake-initial as last resort..."
        set +e
        python3 manage.py migrate --fake-initial --noinput 2>&1
        FAKE_EXIT_CODE=$?
        echo ">>> Fake-initial exit code: $FAKE_EXIT_CODE"
        set -e
        
        if [ $FAKE_EXIT_CODE -ne 0 ]; then
            echo "❌❌❌ ALL MIGRATION ATTEMPTS FAILED ❌❌❌"
        fi
    fi
fi
echo "=== MIGRATIONS PHASE COMPLETE ==="

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
