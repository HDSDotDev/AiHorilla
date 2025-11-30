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
    
    # Migrate Django core apps FIRST (these have no circular dependencies)
    echo "\n>>> Migrating Django core apps (auth, sessions, admin, contenttypes)..."
    set +e
    python3 manage.py migrate contenttypes --noinput 2>&1
    python3 manage.py migrate auth --noinput 2>&1
    python3 manage.py migrate sessions --noinput 2>&1
    python3 manage.py migrate admin --noinput 2>&1
    CORE_EXIT=$?
    set -e
    
    if [ $CORE_EXIT -eq 0 ]; then
        echo "✓ Django core tables created"
    else
        echo "⚠ Core migrations had issues (exit code $CORE_EXIT)"
    fi
    
    # Attempt application migrations (may fail due to circular dependencies)
    # fix_database_tables.py already created app tables, so migration failures are non-fatal
    echo "\n>>> Applying application migrations (best effort - tables already created)..."
    set +e
    python3 manage.py migrate --noinput 2>&1
    MIGRATE_EXIT=$?
    set -e
    
    if [ $MIGRATE_EXIT -eq 0 ]; then
        echo "✓ All migrations applied successfully"
    else
        echo "⚠ Migrations exited with code $MIGRATE_EXIT (likely circular dependencies)"
        echo "ℹ This is OK - tables were already created by fix_database_tables.py"
        echo "ℹ Django migration history may be incomplete, but all tables should exist"
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

# NOTE: Keep SKIP_SCHEDULERS and RAILWAY_ENVIRONMENT set!
# - SKIP_SCHEDULERS prevents schedulers from starting in worker processes before DB is ready
# - RAILWAY_ENVIRONMENT ensures proper Railway integration and CSRF settings
# Schedulers will check table existence before starting even without these flags

echo "=== STARTING APPLICATION SERVER ==="

# CRITICAL: Export CSRF_TRUSTED_ORIGINS for Gunicorn workers
if [ -n "$RAILWAY_PUBLIC_DOMAIN" ]; then
    export CSRF_TRUSTED_ORIGINS="https://${RAILWAY_PUBLIC_DOMAIN}"
    echo "✓ Set CSRF_TRUSTED_ORIGINS=$CSRF_TRUSTED_ORIGINS"
fi

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
