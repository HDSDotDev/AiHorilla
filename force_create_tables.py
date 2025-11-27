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
    
    # 2. Apply migrations properly (not syncdb - apps have migrations!)
    print("\n🔨 APPLYING ALL MIGRATIONS TO CREATE TABLES...")
    apps_to_migrate = [
        'base', 'employee', 'leave', 'asset', 'attendance', 'helpdesk',
        'payroll', 'recruitment', 'pms', 'onboarding', 'offboarding',
        'project', 'handbook', 'notifications', 'horilla_audit',
        'horilla_views', 'horilla_widgets', 'horilla_documents',
        'horilla_automations', 'biometric', 'geofencing', 'facedetection',
        'horilla_backup', 'horilla_crumbs', 'horilla_api', 'accessibility',
        'horilla_ldap', 'outlook_auth', 'dynamic_fields', 'report'
    ]
    
    for i, app in enumerate(apps_to_migrate, 1):
        try:
            print(f"   [{i:2d}/{len(apps_to_migrate)}] {app:25s} ", end='', flush=True)
            call_command('migrate', app, '--noinput', verbosity=0)
            print("✓")
        except Exception as e:
            error_str = str(e).lower()
            if 'no such table' in error_str or 'does not exist' in error_str:
                # Dependency issue - try with --fake-initial
                try:
                    call_command('migrate', app, '--fake-initial', '--noinput', verbosity=0)
                    print("✓ (faked)")
                except Exception as e2:
                    print(f"❌ {str(e2)[:40]}")
            else:
                print(f"⚠️  {str(e)[:40]}")
    
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
        
        # Try forcing with --fake-initial
        print("\n🔨 FORCING MIGRATIONS WITH --fake-initial...")
        problem_apps = ['base', 'employee', 'leave', 'attendance', 'asset', 
                       'helpdesk', 'payroll', 'recruitment', 'pms']
        for app in problem_apps:
            try:
                print(f"   Forcing {app:20s} ", end='', flush=True)
                call_command('migrate', app, '--fake-initial', '--noinput', verbosity=0)
                print("✓")
            except Exception as e:
                print(f"❌ {str(e)[:50]}")
        
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
