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
    print("  CREATING MISSING TABLES")
    print("=" * 80)
    
    print("\nAttempting direct table creation (bypass migrations)...")
    print("   This uses Django schema_editor to create tables from models")
    
    # Import directly instead of subprocess (avoid timeout)
    try:
        print("   Importing schema editor...")
        from django.db.backends.base.schema import BaseDatabaseSchemaEditor
        from django.apps import apps
        
        created_count = 0
        error_count = 0
        
        with connection.schema_editor() as schema_editor:
            for app_label in ['base', 'employee', 'leave', 'asset', 'attendance', 'helpdesk', 'payroll']:
                try:
                    app_config = apps.get_app_config(app_label)
                    print(f"   {app_label}:", end=' ', flush=True)
                    
                    for model in app_config.get_models():
                        try:
                            schema_editor.create_model(model)
                            created_count += 1
                        except Exception as model_err:
                            if 'already exists' not in str(model_err).lower():
                                error_count += 1
                    
                    print(f"✓", flush=True)
                except Exception as app_err:
                    print(f"❌ {str(app_err)[:40]}", flush=True)
        
        print(f"\n   Created {created_count} tables ({error_count} errors)")
        
        # Mark migrations as faked
        print("   Marking migrations as applied...")
        for app_label in ['base', 'employee', 'leave', 'asset', 'attendance', 'helpdesk', 'payroll']:
            try:
                call_command('migrate', app_label, '--fake', '--noinput', verbosity=0)
            except:
                pass
        
        print("✅ Direct table creation completed!")
        
    except Exception as e:
        print(f"\n❌ Direct table creation failed: {e}")

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
