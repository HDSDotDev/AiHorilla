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
    
    print("\nStep 1: NUCLEAR RESET - Deleting ALL migration records...")
    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM django_migrations")
            deleted = cursor.rowcount
            connection.commit()
            print(f"✓ Deleted {deleted} migration records (COMPLETE RESET)")
    except Exception as e:
        print(f"⚠ Could not clear migration history: {e}")
    
    print("\nStep 2: Running FULL migrate (no app filter)...")
    print("   This applies ALL migrations from scratch - creates all tables")
    print("   Takes 2-3 minutes...")
    try:
        call_command('migrate', '--noinput', verbosity=2)
        print("\n✓ Full migration completed")
    except Exception as e:
        print(f"\n⚠ Migration error: {e}")
        print("   Continuing to verify...")
    
    print("\nStep 3: Verifying tables were created...")
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
        print(f"\n❌ STILL MISSING {len(still_missing)} TABLES AFTER FULL MIGRATE:")
        for table in sorted(still_missing):
            print(f"  ❌ {table}")
        print("\n⚠️  Migrations failed to create tables!")
        print("   Attempting direct table creation from Django models...")
        
        # Last resort: Create tables directly
        import subprocess
        try:
            result = subprocess.run(
                ['python3', 'create_tables_sql.py'],
                capture_output=True,
                text=True,
                timeout=300
            )
            print(result.stdout)
            if result.returncode == 0:
                print("\n✅ Tables created via direct SQL!")
            else:
                print(f"\n❌ Direct table creation failed: {result.stderr[:200]}")
        except Exception as e:
            print(f"\n❌ Could not run direct table creation: {e}")
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
