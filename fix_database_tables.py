#!/usr/bin/env python3
"""
Emergency database table creation script for Railway deployment.
This bypasses all migration complexities and directly creates tables from models.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horilla.settings')
sys.path.insert(0, '/app')

print("=" * 80)
print("  EMERGENCY DATABASE TABLE CREATION")
print("=" * 80)

django.setup()

from django.core.management import call_command
from django.db import connection

print("\n=== Checking Current Database State ===")
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT COUNT(*) FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
    """)
    table_count = cursor.fetchone()[0]
    print(f"Current table count: {table_count}")
    
    # Get list of existing tables
    cursor.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        ORDER BY table_name
        LIMIT 20
    """)
    existing = [row[0] for row in cursor.fetchall()]
    print(f"Sample tables: {', '.join(existing) if existing else 'NONE'}")

# Critical tables that MUST exist for demo data
critical_tables = [
    'base_company',
    'base_department', 
    'base_jobposition',
    'base_worktype',
    'base_employeeshift',
    'base_employeetype',
    'base_shiftrequest',
    'employee_employee',
    'employee_employeeworkinformation',
    'employee_employeebankdetails',
    'leave_leavetype',
    'leave_leaverequest',
    'leave_availableleave',
    'payroll_payrollsettings',
    'payroll_payrollcountryconfig',
    'asset_asset',
    'asset_assetassignment',
    'attendance_attendance',
    'helpdesk_ticket'
]

print(f"\n=== Checking for {len(critical_tables)} Critical Tables ===")
with connection.cursor() as cursor:
    placeholders = ', '.join([f"'{table}'" for table in critical_tables])
    cursor.execute(f"""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name IN ({placeholders})
        ORDER BY table_name
    """)
    existing_critical = {row[0] for row in cursor.fetchall()}
    
missing = set(critical_tables) - existing_critical
print(f"Existing: {len(existing_critical)}/{len(critical_tables)}")
print(f"Missing: {len(missing)}")

if missing:
    print(f"\nMissing critical tables:")
    for table in sorted(missing):
        print(f"  ❌ {table}")
else:
    print("\n✅ All critical tables exist!")

if len(missing) > 0:
    print("\n" + "=" * 80)
    print("  CREATING ALL MISSING TABLES")
    print("=" * 80)
    
    print("\nStep 1: Flushing migration history...")
    try:
        # Clear all migration records to start fresh
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM django_migrations WHERE app NOT IN ('contenttypes', 'auth', 'admin', 'sessions')")
            deleted = cursor.rowcount
            print(f"✓ Deleted {deleted} migration records")
    except Exception as e:
        print(f"⚠ Could not clear migration history: {e}")
    
    print("\nStep 2: Running full migrate with --run-syncdb...")
    try:
        # This should create ALL tables from ALL models
        call_command('migrate', '--run-syncdb', '--noinput', verbosity=2)
        print("✓ Syncdb completed")
    except Exception as e:
        print(f"⚠ Syncdb encountered errors: {e}")
        print("Continuing anyway...")
    
    print("\nStep 3: Verifying table creation...")
    with connection.cursor() as cursor:
        placeholders = ', '.join([f"'{table}'" for table in critical_tables])
        cursor.execute(f"""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ({placeholders})
            ORDER BY table_name
        """)
        now_existing = {row[0] for row in cursor.fetchall()}
    
    still_missing = set(critical_tables) - now_existing
    
    if still_missing:
        print(f"\n❌ STILL MISSING {len(still_missing)} TABLES:")
        for table in sorted(still_missing):
            print(f"  ❌ {table}")
        
        print("\nStep 4: Attempting individual app migrations...")
        apps_to_migrate = ['base', 'employee', 'leave', 'payroll', 'asset', 'attendance', 'helpdesk']
        for app in apps_to_migrate:
            try:
                print(f"  Migrating {app}...", end=' ', flush=True)
                call_command('migrate', app, '--run-syncdb', '--noinput', verbosity=0)
                print("✓")
            except Exception as e:
                print(f"⚠ {e}")
    else:
        print("\n✅ ALL CRITICAL TABLES NOW EXIST!")

print("\n" + "=" * 80)
print("  FINAL DATABASE STATE")
print("=" * 80)

with connection.cursor() as cursor:
    cursor.execute("""
        SELECT COUNT(*) FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
    """)
    final_count = cursor.fetchone()[0]
    print(f"Total tables: {final_count}")
    
    placeholders = ', '.join([f"'{table}'" for table in critical_tables])
    cursor.execute(f"""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name IN ({placeholders})
        ORDER BY table_name
    """)
    final_critical = {row[0] for row in cursor.fetchall()}

print(f"Critical tables: {len(final_critical)}/{len(critical_tables)}")

final_missing = set(critical_tables) - final_critical
if final_missing:
    print(f"\n❌ FAILED - Still missing {len(final_missing)} tables")
    for table in sorted(final_missing):
        print(f"  {table}")
    sys.exit(1)
else:
    print("\n✅ SUCCESS - All critical tables exist!")
    print("\nYou can now run 'Load Demo Data' from the web interface.")
    sys.exit(0)
