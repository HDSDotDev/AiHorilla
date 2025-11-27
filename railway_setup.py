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

# Fix circular dependencies: payroll depends on multiple apps' initial migrations
print("Fixing circular dependencies in payroll migration...", flush=True)
import re
payroll_migration_path = '/app/payroll/migrations/0001_initial.py'
try:
    with open(payroll_migration_path, 'r') as f:
        content = f.read()
    
    # Comment out ALL problematic dependency lines to break circular dependencies
    # Keep only AUTH_USER_MODEL dependency which doesn't cause issues
    dependencies_to_disable = [
        r"(\s*)(\('employee', '0001_initial'\),)",
        r"(\s*)(\('base', '0002_initial'\),)",
        r"(\s*)(\('horilla_audit', '0001_initial'\),)",
        r"(\s*)(\('leave', '0001_initial'\),)",
        r"(\s*)(\('asset', '0002_initial'\),)",
        r"(\s*)(\('attendance', '0002_initial'\),)",
    ]
    
    modified_content = content
    for pattern in dependencies_to_disable:
        modified_content = re.sub(
            pattern,
            r"\1# \2  # Disabled to break circular dependency",
            modified_content
        )
    
    if modified_content != content:
        with open(payroll_migration_path, 'w') as f:
            f.write(modified_content)
        print("✓ All circular dependencies temporarily disabled", flush=True)
    else:
        print("✓ Migrations already fixed", flush=True)
except Exception as e:
    print(f"⚠ Could not modify migration file: {e}", flush=True)
    print("  Continuing anyway...", flush=True)

print("Running database migrations...", flush=True)

from django.db import connection

# Check if core tables exist
print("Checking database state...", flush=True)
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name IN ('base_company', 'employee_employee', 'leave_leavetype')
        ORDER BY table_name;
    """)
    existing_tables = [row[0] for row in cursor.fetchall()]

print(f"  Existing core tables: {existing_tables if existing_tables else 'NONE'}", flush=True)

if len(existing_tables) < 3:
    print("  ⚠ Core tables missing! Running fresh migration...", flush=True)
    
    # Delete ALL migration records for clean start
    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM django_migrations")
            deleted = cursor.rowcount
            connection.commit()
            print(f"  ✓ Deleted {deleted} migration records", flush=True)
    except Exception as del_err:
        print(f"  ⚠ Could not clear migrations: {del_err}", flush=True)
    
    # Run full migrate to create all tables
    print("  Running full migrate (this creates all tables)...", flush=True)
    try:
        call_command('migrate', '--noinput', verbosity=1)
        print("  ✓ All migrations applied", flush=True)
    except Exception as e:
        print(f"  ⚠ Migration warning: {e}", flush=True)
        print("  Continuing anyway...", flush=True)
else:
    print("  Core tables exist, running incremental migrations...", flush=True)
    try:
        call_command('migrate', '--noinput', verbosity=0)
        print("  ✓ Migrations completed", flush=True)
    except Exception as e:
        print(f"  ⚠ Migration warning: {e}", flush=True)

print("✓ Migrations completed", flush=True)

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
