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
def list_tables(cursor):
    # Return all user table names for the current DB backend.
    # If a previous operation left the DB in an aborted transaction state
    # we must rollback first so introspection queries succeed.
    try:
        connection.rollback()
    except Exception:
        pass

    try:
        from django.db import connection as _conn
        return list(_conn.introspection.table_names())
    except Exception:
        # If introspection fails (e.g., aborted transaction), make another
        # attempt after a rollback and then fallback to vendor-specific SQL.
        try:
            connection.rollback()
        except Exception:
            pass
        vendor = connection.vendor
        if vendor == 'postgresql':
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            return [row[0] for row in cursor.fetchall()]
        elif vendor == 'sqlite':
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            return [row[0] for row in cursor.fetchall()]
        else:
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            return [row[0] for row in cursor.fetchall()]

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
def existing_tables_set(cursor):
    # Use introspection to find which critical tables already exist.
    try:
        from django.db import connection as _conn
        tables = set(_conn.introspection.table_names())
        return tables.intersection(set(critical_tables))
    except Exception:
        # Fallback: list all tables then intersect.
        all_tables = set(list_tables(cursor))
        return all_tables.intersection(set(critical_tables))


with connection.cursor() as cursor:
    existing_critical = existing_tables_set(cursor)
    
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
        
        errors = []
        from django.apps import apps

        for app_label in ['horilla_audit', 'base', 'employee', 'leave', 'asset', 'attendance', 'helpdesk', 'payroll']:
            try:
                app_config = apps.get_app_config(app_label)
            except LookupError:
                print(f"   {app_label}: NOT INSTALLED", flush=True)
                continue

            print(f"   {app_label}:", end=' ', flush=True)
            app_created = 0
            for model in app_config.get_models():
                table_name = model._meta.db_table
                try:
                    # Create each model in its own schema_editor context to isolate SQL errors
                    with connection.schema_editor() as schema_editor:
                        schema_editor.create_model(model)
                    created_count += 1
                    app_created += 1
                except Exception as model_err:
                    # Rollback to clear failed transaction and continue
                    try:
                        connection.rollback()
                    except Exception:
                        pass
                    err_str = str(model_err)
                    errors.append((model._meta.label, err_str))
                    print(f"❌ {model.__name__}", flush=True)
            if app_created:
                print(f"✓ ({app_created} tables)", flush=True)
            else:
                print("✓ (no new tables)", flush=True)
        
        print(f"\n   Created {created_count} tables; Errors: {len(errors)}")
        if errors:
            print("   Some models failed to create:")
            for label, err in errors[:10]:
                print(f"     - {label}: {err[:200]}")

        # Mark migrations as faked for apps we attempted
        print("   Marking migrations as applied (faked)...")
        for app_label in ['horilla_audit', 'base', 'employee', 'leave', 'asset', 'attendance', 'helpdesk', 'payroll']:
            try:
                call_command('migrate', app_label, '--fake', '--noinput', verbosity=0)
            except Exception:
                pass

        if errors:
            print("\n❌ Direct table creation completed with errors")
        else:
            print("✅ Direct table creation completed!")
        
    except Exception as e:
        print(f"\n❌ Direct table creation failed: {e}")

print("\n" + "=" * 80)
print("  FINAL DATABASE STATE")
print("=" * 80)

# Clear any aborted transaction state by rolling back
try:
    from django.db import transaction
    if transaction.get_connection().in_atomic_block:
        transaction.set_rollback(True)
    connection.rollback()
except Exception:
    pass

try:
    # Ensure connection is alive
    connection.ensure_connection()
    
    with connection.cursor() as cursor:
        tables_now = list_tables(cursor)
        final_count = len(tables_now)
        print(f"Total tables: {final_count}")
        
        final_critical = set()
        for t in critical_tables:
            if t in tables_now:
                final_critical.add(t)

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
except Exception as e:
    print(f"\n❌ FAILED - Could not verify final state: {e}")
    sys.exit(1)
