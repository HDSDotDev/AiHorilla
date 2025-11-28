#!/bin/bash
set -e  # Exit on error (will be temporarily disabled for migration attempts)

# Force unbuffered output for Python
export PYTHONUNBUFFERED=1

echo "=== Starting Horilla Deployment ==="

# Disable schedulers during migration
export SKIP_SCHEDULERS=1

# Mark Railway environment for Django settings
export RAILWAY_ENVIRONMENT=1

# Set Railway public domain if available
if [ -n "$RAILWAY_PUBLIC_DOMAIN" ]; then
    echo "✓ Railway domain detected: $RAILWAY_PUBLIC_DOMAIN"
fi

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
    
    echo ">>> Executing railway_setup.py (direct initialization script)..."
    echo ">>> Command starting at $(date)..."
    set +e
    python3 -u railway_setup.py 2>&1
    INIT_EXIT_CODE=$?
    set -e
    
    echo ">>> Command finished at $(date) with exit code: $INIT_EXIT_CODE"
    
    echo ">>> railway_setup.py exit code: $INIT_EXIT_CODE"
    
    if [ $INIT_EXIT_CODE -ne 0 ]; then
        echo "❌ Initialization failed with exit code $INIT_EXIT_CODE"
        echo "Attempting to continue anyway..."
    else
        echo "✓ Initialization successful"
    fi
    
    # Verify all tables exist, create if missing
    echo ""
    echo ">>> Verifying database tables..."
    set +e
    python3 -u fix_database_tables.py 2>&1
    FIX_EXIT_CODE=$?
    set -e
    
    if [ $FIX_EXIT_CODE -ne 0 ]; then
        echo "❌ Table verification failed - database may be incomplete"
        echo "Demo data loading may not work"
    else
        echo "✓ All database tables verified"
    fi
    
    # Ensure Django migrations are applied (idempotent). Retry a few times
    # to allow the DB to settle in case of transient connection issues.
    echo "\n>>> Applying Django migrations (this blocks startup until complete)..."
    MAX_ATTEMPTS=5
    ATTEMPT=1
    set +e
    until [ $ATTEMPT -gt $MAX_ATTEMPTS ]
    do
        echo "> Attempt $ATTEMPT of $MAX_ATTEMPTS: running migrate..."
        python3 manage.py migrate --noinput 2>&1
        MIGRATE_EXIT=$?
        if [ $MIGRATE_EXIT -eq 0 ]; then
            echo "✓ Migrations applied successfully"
            break
        else
            echo "⚠ migrate failed (exit $MIGRATE_EXIT). Retrying after delay..."
            sleep $(( ATTEMPT * 5 ))
            ATTEMPT=$(( ATTEMPT + 1 ))
        fi
    done
    set -e

    if [ $MIGRATE_EXIT -ne 0 ]; then
        echo "❌ ERROR: Could not apply migrations after $MAX_ATTEMPTS attempts."
        echo "The application will not start to avoid serving a partially-initialized site."
        echo "Please check the container logs and run 'python manage.py migrate' in the service shell."
        exit 1
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
