#!/bin/bash
set -e  # Exit on error (will be temporarily disabled for migration attempts)

# Force unbuffered output for Python
export PYTHONUNBUFFERED=1

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
    
    # Test Python is working
    echo ">>> Testing Python..."
    python3 --version 2>&1 || echo "ERROR: Python not found"
    
    # Test manage.py exists
    echo ">>> Checking manage.py..."
    ls -la manage.py 2>&1 || echo "ERROR: manage.py not found"
    
    # Try to import Django
    echo ">>> Testing Django import..."
    python3 -c "import django; print(f'Django version: {django.get_version()}')" 2>&1 || echo "ERROR: Django import failed"
    
    # Show what railway_init_db command exists
    echo ">>> Checking railway_init_db command..."
    python3 manage.py help railway_init_db 2>&1 || echo "ERROR: railway_init_db command not found"
    
    echo ">>> Executing railway_init_db command..."
    set +e
    python3 -u manage.py railway_init_db 2>&1
    INIT_EXIT_CODE=$?
    set -e
    
    echo ">>> railway_init_db exit code: $INIT_EXIT_CODE"
    
    if [ $INIT_EXIT_CODE -ne 0 ]; then
        echo "❌ Initialization failed with exit code $INIT_EXIT_CODE"
        echo "Attempting to continue anyway..."
    else
        echo "✓ Initialization successful"
    fi
else
    echo "⚠️  WARNING: No DATABASE_URL - using SQLite (data will NOT persist on Railway!)"
    echo "⚠️  Please add a PostgreSQL database in Railway dashboard"
    echo "⚠️  Attempting initialization anyway..."
    
    set +e
    python3 manage.py railway_init_db 2>&1
    INIT_EXIT_CODE=$?
    set -e
    
    if [ $INIT_EXIT_CODE -ne 0 ]; then
        echo "❌ Initialization failed with exit code $INIT_EXIT_CODE"
        exit 1
    fi
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
