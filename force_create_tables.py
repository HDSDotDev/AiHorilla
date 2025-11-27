#!/usr/bin/env python3
"""
Emergency script to forcefully create ALL database tables.
Run this via Railway shell: python force_create_tables.py
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horilla.settings')
django.setup()

from django.core.management import call_command
from django.db import connection

def main():
    print("="*80)
    print("  FORCE CREATE ALL DATABASE TABLES")
    print("="*80)
    
    cursor = connection.cursor()
    
    # 1. Check current state
    cursor.execute("""
        SELECT tablename FROM pg_tables 
        WHERE schemaname = 'public' 
        AND tablename NOT LIKE 'pg_%'
        ORDER BY tablename
    """)
    existing = [row[0] for row in cursor.fetchall()]
    print(f"\n📊 Current tables: {len(existing)}")
    
    critical_tables = [
        'base_company', 'base_department', 'base_jobposition', 'base_worktype',
        'base_employeetype', 'base_employeeshift', 'base_shiftrequest',
        'employee_employee', 'employee_employeeworkinformation',
        'leave_leavetype', 'leave_leaverequest', 'leave_leaveallocation',
        'attendance_attendance', 'asset_asset', 'asset_assetassignment',
        'helpdesk_ticket', 'payroll_payrollsettings', 'payroll_payrollcountryconfig',
        'payroll_allowance', 'payroll_deduction', 'payroll_payslip',
        'recruitment_recruitment', 'recruitment_candidate', 'pms_performancegoal'
    ]
    
    missing = set(critical_tables) - set(existing)
    print(f"❌ Missing critical tables: {len(missing)}")
    if missing:
        print(f"   {', '.join(sorted(missing)[:10])}...")
    
    # 2. Nuclear option - clear ALL migrations and force syncdb
    print("\n⚠️  CLEARING ALL MIGRATION HISTORY...")
    cursor.execute("""
        DELETE FROM django_migrations 
        WHERE app NOT IN ('contenttypes', 'auth', 'admin', 'sessions')
    """)
    deleted = cursor.rowcount
    print(f"   Deleted {deleted} migration records")
    connection.commit()
    
    # 3. Force create ALL tables
    print("\n🔨 FORCING TABLE CREATION (migrate --run-syncdb)...")
    try:
        call_command('migrate', '--run-syncdb', '--noinput', verbosity=2)
        print("   ✓ Migrate command completed")
    except Exception as e:
        print(f"   ⚠️  Error during migrate: {e}")
    
    # 4. Verify results
    print("\n🔍 VERIFYING TABLES...")
    cursor.execute("""
        SELECT tablename FROM pg_tables 
        WHERE schemaname = 'public' 
        AND tablename NOT LIKE 'pg_%'
        ORDER BY tablename
    """)
    now_existing = {row[0] for row in cursor.fetchall()}
    print(f"📊 Total tables now: {len(now_existing)}")
    
    still_missing = set(critical_tables) - now_existing
    if still_missing:
        print(f"\n❌ STILL MISSING {len(still_missing)} CRITICAL TABLES:")
        for table in sorted(still_missing):
            print(f"   - {table}")
        
        # Try individual app migrations
        print("\n🔨 TRYING INDIVIDUAL APP MIGRATIONS...")
        apps_to_try = ['base', 'employee', 'leave', 'attendance', 'asset', 
                       'helpdesk', 'payroll', 'recruitment', 'pms']
        for app in apps_to_try:
            try:
                print(f"   Migrating {app}...")
                call_command('migrate', app, '--noinput', verbosity=1)
            except Exception as e:
                print(f"   ⚠️  {app} failed: {e}")
        
        # Final check
        cursor.execute("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public'
            AND tablename NOT LIKE 'pg_%'
        """)
        final_existing = {row[0] for row in cursor.fetchall()}
        final_missing = set(critical_tables) - final_existing
        
        if final_missing:
            print(f"\n❌ FAILED - {len(final_missing)} tables still missing")
            for table in sorted(final_missing):
                print(f"   - {table}")
            return 1
    
    # Success
    created_count = len(set(critical_tables) & now_existing)
    print(f"\n✅ SUCCESS - {created_count}/{len(critical_tables)} critical tables exist!")
    print(f"📊 Total database tables: {len(now_existing)}")
    
    # Show some key tables
    print("\n✓ Key tables verified:")
    for table in sorted(set(critical_tables) & now_existing)[:12]:
        print(f"   ✓ {table}")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
