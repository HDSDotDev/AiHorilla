#!/usr/bin/env python3
"""
Emergency database table creation script for Railway deployment.
TWO-PASS APPROACH to break circular FK dependencies:
  Pass 1: Create all tables WITHOUT foreign key constraints
  Pass 2: Add foreign key constraints after all tables exist
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horilla.settings')
sys.path.insert(0, '/app')

print("=" * 80)
print("  EMERGENCY DATABASE TABLE CREATION (Two-Pass Method)")
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
    print("  CREATING MISSING TABLES (Two-Pass Method)")
    print("=" * 80)
    
    print("\nPASS 1: Creating tables WITHOUT foreign key constraints...")
    print("  (This breaks the circular dependency deadlock)")
    
    try:
        from django.apps import apps
        from django.db.models import ForeignKey, OneToOneField, ManyToManyField
        
        pass1_created = 0
        pass1_errors = []
        deferred_fks = []  # Store FK info for pass 2
        
        # Create a custom schema editor that skips FK constraint creation
        class NoFKSchemaEditor(connection.schema_editor().__class__):
            def _create_fk_sql(self, model, field, suffix):
                # Store FK for later, but don't create constraint yet
                deferred_fks.append((model, field))
                return None
            
            def add_field(self, model, field):
                # For FK fields, create the column but not the constraint
                if isinstance(field, (ForeignKey, OneToOneField)):
                    # Save original db_constraint
                    original_constraint = field.db_constraint
                    field.db_constraint = False
                    try:
                        super().add_field(model, field)
                    finally:
                        field.db_constraint = original_constraint
                else:
                    super().add_field(model, field)
        
        # PASS 1: Create tables without FK constraints
        for app_label in ['horilla_audit', 'base', 'employee', 'payroll', 'leave', 'asset', 'attendance', 'helpdesk']:
            try:
                app_config = apps.get_app_config(app_label)
            except LookupError:
                print(f"  {app_label}: NOT INSTALLED", flush=True)
                continue

            print(f"  {app_label}:", end=' ', flush=True)
            app_created = 0
            
            for model in app_config.get_models():
                # Skip abstract and proxy models
                if model._meta.abstract or model._meta.proxy:
                    continue
                    
                table_name = model._meta.db_table
                
                # Check if table already exists
                try:
                    connection.ensure_connection()
                    with connection.cursor() as cursor:
                        existing = list_tables(cursor)
                        if table_name in existing:
                            continue
                except Exception:
                    pass
                
                try:
                    # Temporarily disable FK constraints on all FK fields
                    fk_fields = [f for f in model._meta.local_fields 
                                if isinstance(f, (ForeignKey, OneToOneField))]
                    original_constraints = {}
                    
                    for fk_field in fk_fields:
                        original_constraints[fk_field.name] = fk_field.db_constraint
                        fk_field.db_constraint = False
                    
                    try:
                        with connection.schema_editor() as schema_editor:
                            schema_editor.create_model(model)
                        pass1_created += 1
                        app_created += 1
                    finally:
                        # Restore original constraints
                        for fk_field in fk_fields:
                            fk_field.db_constraint = original_constraints[fk_field.name]
                            
                except Exception as model_err:
                    try:
                        connection.rollback()
                    except Exception:
                        pass
                    err_str = str(model_err)
                    pass1_errors.append((model._meta.label, err_str))
                    print(f"❌ {model.__name__}", end=' ', flush=True)
            
            if app_created:
                print(f"✓ ({app_created} tables)", flush=True)
            else:
                print("✓ (skipped)", flush=True)
        
        print(f"\nPASS 1 COMPLETE: {pass1_created} tables created")
        if pass1_errors:
            print(f"  Errors: {len(pass1_errors)}")
            for label, err in pass1_errors[:5]:
                print(f"    - {label}: {err[:150]}")
        
        # PASS 2: Add FK constraints
        print("\nPASS 2: Adding foreign key constraints...")
        print("  (Now that all tables exist, we can create FK relationships)")
        
        pass2_added = 0
        pass2_errors = []
        
        for app_label in ['horilla_audit', 'base', 'employee', 'payroll', 'leave', 'asset', 'attendance', 'helpdesk']:
            try:
                app_config = apps.get_app_config(app_label)
            except LookupError:
                continue
            
            for model in app_config.get_models():
                if model._meta.abstract or model._meta.proxy:
                    continue
                
                # Find all FK fields that need constraints
                fk_fields = [f for f in model._meta.local_fields 
                            if isinstance(f, (ForeignKey, OneToOneField)) and f.db_constraint]
                
                for fk_field in fk_fields:
                    try:
                        with connection.cursor() as cursor:
                            table_name = model._meta.db_table
                            column_name = fk_field.column
                            related_table = fk_field.related_model._meta.db_table
                            related_column = fk_field.related_model._meta.pk.column
                            
                            # Check if constraint already exists
                            if connection.vendor == 'postgresql':
                                cursor.execute("""
                                    SELECT COUNT(*) FROM information_schema.table_constraints 
                                    WHERE table_name = %s 
                                    AND constraint_type = 'FOREIGN KEY'
                                    AND constraint_name LIKE %s
                                """, [table_name, f"%{column_name}%"])
                                exists = cursor.fetchone()[0] > 0
                            else:
                                exists = False
                            
                            if not exists:
                                # Create FK constraint
                                constraint_name = f"{table_name}_{column_name}_fkey"
                                sql = f"""
                                    ALTER TABLE "{table_name}"
                                    ADD CONSTRAINT "{constraint_name}"
                                    FOREIGN KEY ("{column_name}")
                                    REFERENCES "{related_table}" ("{related_column}")
                                    DEFERRABLE INITIALLY DEFERRED
                                """
                                cursor.execute(sql)
                                pass2_added += 1
                    except Exception as fk_err:
                        try:
                            connection.rollback()
                        except Exception:
                            pass
                        # Only log if it's a real error (not "already exists")
                        if "already exists" not in str(fk_err).lower():
                            pass2_errors.append((f"{model._meta.label}.{fk_field.name}", str(fk_err)))
        
        print(f"PASS 2 COMPLETE: {pass2_added} FK constraints added")
        if pass2_errors:
            print(f"  Errors: {len(pass2_errors)}")
            for label, err in pass2_errors[:5]:
                print(f"    - {label}: {err[:150]}")

        # Mark migrations as faked
        print("\nMarking migrations as applied (faked)...")
        for app_label in ['horilla_audit', 'base', 'employee', 'payroll', 'leave', 'asset', 'attendance', 'helpdesk']:
            try:
                call_command('migrate', app_label, '--fake', '--noinput', verbosity=0)
            except Exception:
                pass

        if pass1_errors or pass2_errors:
            print("\n⚠ Table creation completed with some errors")
        else:
            print("\n✅ Two-pass table creation completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Two-pass table creation failed: {e}")
        import traceback
        traceback.print_exc()

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
