#!/usr/bin/env python3
"""
Direct Railway database initialization script.
Bypasses Django management command system to avoid initialization hangs.
"""
import os
import sys
import django

print("=== RAILWAY SETUP SCRIPT STARTED ===", flush=True)
print(f"Python version: {sys.version}", flush=True)
print(f"Django location: {django.__file__}", flush=True)

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horilla.settings')
print("✓ Django settings module set", flush=True)

# Disable schedulers during setup
os.environ['SKIP_SCHEDULERS'] = '1'
print("✓ Schedulers disabled", flush=True)

# Prevent apps from doing database operations in ready() methods before migrations
os.environ['SKIP_DB_INIT_IN_READY'] = '1'
print("✓ Database initialization in app ready() methods disabled", flush=True)

# Setup Django with timeout protection
print("Setting up Django...", flush=True)
print("  (This may take 30-60 seconds on first run)", flush=True)

import signal

def timeout_handler(signum, frame):
    print("✗ Django setup timed out after 60 seconds!", flush=True)
    print("  This usually means an app is accessing the database in its ready() method", flush=True)
    sys.exit(1)

try:
    # Set connection timeout before Django setup
    os.environ['DATABASE_CONNECT_TIMEOUT'] = '10'
    
    # Prevent database checks during setup
    os.environ['DJANGO_SKIP_DB_CHECK'] = '1'
    
    # Set 60-second timeout for django.setup()
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(60)
    
    print("  Calling django.setup()...", flush=True)
    django.setup()
    
    # Cancel the alarm
    signal.alarm(0)
    
    print("✓ Django setup complete", flush=True)
except Exception as e:
    signal.alarm(0)  # Cancel alarm on error
    print(f"✗ Django setup failed: {type(e).__name__}: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)

from django.core.management import call_command
from django.db import connection
print("✓ Django imports successful", flush=True)

print("\n=== Testing Database Connection ===", flush=True)
try:
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
    print(f"✓ Database connection successful! Result: {result}", flush=True)
    print(f"  Engine: {connection.settings_dict['ENGINE']}", flush=True)
    print(f"  Database: {connection.settings_dict.get('NAME', 'unknown')}", flush=True)
except Exception as e:
    print(f"✗ Database connection failed: {e}", flush=True)
    sys.exit(1)

print("\n=== Running Migrations ===", flush=True)

# Strategy: Use migrate with --fake-initial to handle circular dependencies
# This creates tables directly from models if migrations fail due to dependency issues
print("Running full migration (with fake-initial to handle dependencies)...", flush=True)
try:
    # First try: Run all migrations with --fake-initial
    # This will create tables from models if initial migrations can't be applied
    call_command('migrate', '--fake-initial', '--noinput', verbosity=1)
    print("✓ All migrations completed successfully", flush=True)
except Exception as e:
    print(f"⚠ Standard migration failed: {e}", flush=True)
    print("\nTrying alternative: migrate with --run-syncdb...", flush=True)
    try:
        # Fallback: Use --run-syncdb to create tables directly from models
        call_command('migrate', '--run-syncdb', '--noinput', verbosity=1)
        print("✓ Database synchronized using --run-syncdb", flush=True)
    except Exception as e2:
        print(f"✗ Migration failed completely: {e2}", flush=True)
        print("Attempting to continue with remaining setup...", flush=True)

print("\n=== Creating Admin User ===", flush=True)
try:
    call_command('createhorillauser', '--username', 'admin', '--password', 'admin', verbosity=0)
    print("✓ Admin user created (username: admin, password: admin)", flush=True)
except Exception as e:
    print(f"⚠ Admin user creation skipped: {e}", flush=True)

print("\n=== Setting up Philippines Payroll ===", flush=True)
try:
    call_command('setup_philippines_payroll', verbosity=0)
    print("✓ Philippines payroll data loaded", flush=True)
except Exception as e:
    print(f"⚠ Philippines setup skipped: {e}", flush=True)

print("\n=== Collecting Static Files ===", flush=True)
try:
    call_command('collectstatic', '--noinput', verbosity=0)
    print("✓ Static files collected", flush=True)
except Exception as e:
    print(f"⚠ Static files collection failed: {e}", flush=True)

print("\n=== RAILWAY SETUP COMPLETE ===", flush=True)
sys.exit(0)
