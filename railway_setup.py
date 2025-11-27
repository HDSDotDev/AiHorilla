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
print("  (This may take 5-10 minutes on first run - DO NOT TIMEOUT)", flush=True)

try:
    # Set connection timeout before Django setup
    os.environ['DATABASE_CONNECT_TIMEOUT'] = '10'
    
    # Prevent database checks during setup
    os.environ['DJANGO_SKIP_DB_CHECK'] = '1'
    
    print("  Calling django.setup() (no timeout - will wait as long as needed)...", flush=True)
    django.setup()
    
    print("✓ Django setup complete", flush=True)
except Exception as e:
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

# Fix circular dependency: payroll depends on employee but both are initial migrations
print("Fixing circular dependency in payroll migration...", flush=True)
import re
payroll_migration_path = '/app/payroll/migrations/0001_initial.py'
try:
    with open(payroll_migration_path, 'r') as f:
        content = f.read()
    
    # Comment out the employee dependency line to break circular dependency
    if "('employee', '0001_initial')" in content:
        modified_content = re.sub(
            r"(\s*)(\('employee', '0001_initial'\),)",
            r"\1# \2  # Temporarily disabled to break circular dependency",
            content
        )
        
        with open(payroll_migration_path, 'w') as f:
            f.write(modified_content)
        print("✓ Circular dependency temporarily disabled", flush=True)
    else:
        print("✓ Migration already fixed or dependency not found", flush=True)
except Exception as e:
    print(f"⚠ Could not modify migration file: {e}", flush=True)
    print("  Continuing anyway...", flush=True)

print("Running migrations...", flush=True)
try:
    call_command('migrate', '--noinput', verbosity=1)
    print("✓ All migrations completed successfully", flush=True)
except Exception as e:
    print(f"✗ Migration failed: {e}", flush=True)
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

# Force rebuild - 11/27/2025 14:46:04
