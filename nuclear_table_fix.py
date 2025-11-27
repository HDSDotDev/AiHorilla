#!/usr/bin/env python3
"""
NUCLEAR OPTION: Completely wipe migration state and rebuild from scratch.
This will DELETE ALL MIGRATION RECORDS and re-apply everything.
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horilla.settings')
django.setup()

from django.core.management import call_command
from django.db import connection

def main():
    print("="*80)
    print("  NUCLEAR DATABASE FIX - COMPLETE RESET")
    print("="*80)
    
    cursor = connection.cursor()
    
    # Step 1: Show current state
    print("\n📊 CURRENT STATE:")
    cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
    print(f"   Tables: {cursor.fetchone()[0]}")
    cursor.execute("SELECT COUNT(*) FROM django_migrations")
    print(f"   Migration records: {cursor.fetchone()[0]}")
    
    # Step 2: Nuclear option - delete ALL migration records
    print("\n💣 STEP 1: DELETING ALL MIGRATION RECORDS...")
    cursor.execute("DELETE FROM django_migrations")
    deleted = cursor.rowcount
    connection.commit()
    print(f"   ✓ Deleted {deleted} migration records")
    
    # Step 3: Run migrate without any flags - this will apply ALL migrations fresh
    print("\n🔨 STEP 2: APPLYING ALL MIGRATIONS FROM SCRATCH...")
    print("   (This creates all tables - will take 2-3 minutes)")
    try:
        call_command('migrate', '--noinput', verbosity=2)
        print("\n   ✓ All migrations applied successfully")
    except Exception as e:
        print(f"\n   ⚠️  Error: {e}")
        print("   Continuing to check results...")
    
    # Step 4: Verify critical tables
    print("\n🔍 STEP 3: VERIFYING CRITICAL TABLES...")
    critical_tables = [
        'base_company', 'base_department', 'base_jobposition', 'base_worktype',
        'base_employeetype', 'base_employeeshift', 'employee_employee',
        'leave_leavetype', 'leave_leaverequest', 'attendance_attendance',
        'asset_asset', 'helpdesk_ticket', 'payroll_payrollsettings'
    ]
    
    cursor.execute("""
        SELECT tablename FROM pg_tables 
        WHERE schemaname = 'public' AND tablename NOT LIKE 'pg_%'
        ORDER BY tablename
    """)
    existing = {row[0] for row in cursor.fetchall()}
    
    missing = set(critical_tables) - existing
    present = set(critical_tables) & existing
    
    print(f"\n   Total tables: {len(existing)}")
    print(f"   Critical tables present: {len(present)}/{len(critical_tables)}")
    
    if missing:
        print(f"\n   ❌ Still missing {len(missing)} tables:")
        for table in sorted(missing):
            print(f"      - {table}")
        return 1
    else:
        print("\n✅ SUCCESS! All critical tables exist!")
        print("\n✓ Sample tables verified:")
        for table in sorted(present)[:10]:
            print(f"   ✓ {table}")
        return 0

if __name__ == '__main__':
    sys.exit(main())
