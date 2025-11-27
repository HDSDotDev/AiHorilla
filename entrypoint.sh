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

echo "=== RAILWAY DATABASE INITIALIZATION ==="
echo "DATABASE_URL: ${DATABASE_URL:+SET (PostgreSQL)} ${DATABASE_URL:-NOT SET (will use SQLite)}"

# Check if DATABASE_URL is set (PostgreSQL on Railway)
if [ -n "$DATABASE_URL" ]; then
    echo "✓ PostgreSQL detected - running full initialization"
    python3 manage.py railway_init_db
else
    echo "⚠️  WARNING: No DATABASE_URL - using SQLite (data will NOT persist on Railway!)"
    echo "⚠️  Please add a PostgreSQL database in Railway dashboard"
    echo "⚠️  Attempting initialization anyway..."
    python3 manage.py railway_init_db || {
        echo "❌ Initialization failed"
        exit 1
    }
fi

echo "=== INITIALIZATION COMPLETE ==="

# Re-enable schedulers for server
unset SKIP_SCHEDULERS

echo "=== STARTING APPLICATION SERVER ==="
echo "Port: ${PORT:-8000}"
echo "Workers: ${GUNICORN_WORKERS:-2}"
echo "Threads: ${GUNICORN_THREADS:-4}"
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
