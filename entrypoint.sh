#!/bin/bash
set -e  # Exit on any error

echo "=== Starting Horilla Deployment ==="

echo "Step 1: Running migrations..."
python3 manage.py migrate --noinput || {
    echo "Migration failed! Trying with --run-syncdb..."
    python3 manage.py migrate --run-syncdb --noinput
}

echo "Step 2: Collecting static files..."
python3 manage.py collectstatic --noinput

echo "Step 3: Creating admin user (if not exists)..."
python3 manage.py createhorillauser --first_name admin --last_name admin --username admin --password admin --email admin@example.com --phone 1234567890 || echo "Admin user already exists or creation failed"

echo "Step 4: Starting Gunicorn server on port ${PORT:-8000}..."
exec gunicorn --bind 0.0.0.0:${PORT:-8000} --workers 2 --timeout 120 --log-level info horilla.wsgi:application
