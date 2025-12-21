#!/bin/bash
set -e

# Force unbuffered output
export PYTHONUNBUFFERED=1

# Also capture all runtime output to a persistent file for post-mortem debugging
# This writes both stdout and stderr to /app/deploy_debug.log while preserving console output
exec > >(tee -a /app/deploy_debug.log) 2>&1

echo "=== FAST RAILWAY DEPLOYMENT ==="
echo "Target: <15 minutes total"
echo ""

# Set environment variables
export SKIP_SCHEDULERS=1
export SKIP_DB_INIT_IN_READY=1
export RAILWAY_ENVIRONMENT=1

# Set CSRF trusted origins
if [ -n "$RAILWAY_PUBLIC_DOMAIN" ]; then
    export CSRF_TRUSTED_ORIGINS="https://${RAILWAY_PUBLIC_DOMAIN}"
    echo "✓ Domain: $RAILWAY_PUBLIC_DOMAIN"
fi

# Check database
if [ -z "$DATABASE_URL" ]; then
    echo "✗ ERROR: DATABASE_URL not set"
    exit 1
fi
echo "✓ PostgreSQL configured"
echo ""

# Run single unified deployment script
echo "Running unified deployment (single django.setup)..."
python3 fast_railway_deploy.py

if [ $? -ne 0 ]; then
    echo "✗ Deployment failed"
    exit 1
fi

echo ""
echo "=== STARTING APPLICATION ==="
echo "Port: ${PORT:-8000}"
echo "Workers: ${GUNICORN_WORKERS:-2}"
echo ""

# Start Gunicorn
exec gunicorn \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers ${GUNICORN_WORKERS:-2} \
    --threads ${GUNICORN_THREADS:-4} \
    --timeout 120 \
    --log-level info \
    --access-logfile - \
    --error-logfile - \
    --worker-class sync \
    --preload \
    horilla.wsgi:application
