#!/usr/bin/env python3
"""
Startup verification script - runs before Gunicorn to diagnose issues
"""
import os
import sys
import time

print("=" * 80)
print("HORILLA STARTUP VERIFICATION")
print("=" * 80)
print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")
print(f"Python: {sys.version}")
print(f"Python Path: {sys.executable}")
print()

# Check environment
print("=== Environment Variables ===")
important_vars = [
    'DATABASE_URL',
    'RAILWAY_ENVIRONMENT', 
    'RAILWAY_PUBLIC_DOMAIN',
    'PORT',
    'GUNICORN_WORKERS',
    'CSRF_TRUSTED_ORIGINS',
    'PYTHONUNBUFFERED',
]

for var in important_vars:
    value = os.environ.get(var)
    if var == 'DATABASE_URL' and value:
        # Mask password in DATABASE_URL
        print(f"{var}: {'SET (PostgreSQL)' if 'postgresql' in value.lower() else 'SET'}")
    elif value:
        print(f"{var}: {value}")
    else:
        print(f"{var}: NOT SET")
print()

# Test Django setup
print("=== Testing Django Setup ===")
try:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horilla.settings')
    import django
    print(f"✓ Django imported: version {django.get_version()}")
    
    print("  Calling django.setup()...", flush=True)
    django.setup()
    print("✓ Django setup complete")
    
    # Test database connection
    print("  Testing database connection...", flush=True)
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
    print(f"✓ Database connection successful: {result}")
    
    # Test WSGI application
    print("  Loading WSGI application...", flush=True)
    from horilla.wsgi import application
    print(f"✓ WSGI application loaded: {type(application)}")
    
    # Check critical tables
    print("  Checking critical tables...", flush=True)
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        table_count = cursor.fetchone()[0]
    print(f"✓ Database has {table_count} tables")
    
    print()
    print("=" * 80)
    print("✓ ALL CHECKS PASSED - READY TO START GUNICORN")
    print("=" * 80)
    sys.exit(0)
    
except Exception as e:
    print()
    print("=" * 80)
    print(f"✗ STARTUP VERIFICATION FAILED")
    print("=" * 80)
    print(f"Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    print()
    print("This error will prevent Gunicorn from starting.")
    print("Check the error above and fix the issue.")
    print("=" * 80)
    sys.exit(1)
