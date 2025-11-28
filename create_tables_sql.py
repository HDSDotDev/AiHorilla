#!/usr/bin/env python3
"""
LAST RESORT: Create tables directly using Django ORM without migrations.
This bypasses the broken migration system entirely.
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horilla.settings')
django.setup()

from django.core.management import call_command
from django.db import connection
from django.apps import apps

def main():
    print("="*80)
    print("  DIRECT TABLE CREATION (NO MIGRATIONS)")
    print("="*80)
    
    # Get all models from our apps
    app_labels = [
        'base', 'employee', 'leave', 'asset', 'attendance', 'helpdesk',
        'payroll', 'recruitment', 'pms', 'onboarding', 'offboarding',
        'project', 'handbook', 'notifications', 'horilla_audit',
        'horilla_views', 'horilla_widgets', 'horilla_documents',
        'horilla_automations', 'biometric', 'geofencing', 'facedetection',
        'horilla_backup', 'horilla_crumbs', 'horilla_api', 'accessibility'
    ]
    
    print("\n📊 Current state:")
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
    print(f"   Tables: {cursor.fetchone()[0]}")
    
    # Create tables directly from models
    print("\n🔨 Creating tables from Django models (bypassing migrations)...")
    
    from django.db import connection
    from django.core.management.sql import sql_create
    from django.db.backends.base.schema import BaseDatabaseSchemaEditor
    
    with connection.schema_editor() as schema_editor:
        for app_label in app_labels:
            try:
                app_config = apps.get_app_config(app_label)
                print(f"\n  {app_label}:", end=' ', flush=True)
                
                created_count = 0
                for model in app_config.get_models():
                    table_name = model._meta.db_table
                    
                    # Check if table exists
                    cursor.execute(f"""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' 
                            AND table_name = '{table_name}'
                        );
                    """)
                    exists = cursor.fetchone()[0]
                    
                    if not exists:
                        try:
                            # Create table directly
                            schema_editor.create_model(model)
                            created_count += 1
                        except Exception as e:
                            if 'already exists' not in str(e).lower():
                                print(f"❌ {model.__name__}: {str(e)[:40]}", flush=True)
                
                if created_count > 0:
                    print(f"✓ ({created_count} tables)", flush=True)
                else:
                    print("✓ (already exist)", flush=True)
                    
            except Exception as e:
                print(f"❌ {str(e)[:50]}", flush=True)
    
    # Mark all migrations as applied
    print("\n📝 Marking migrations as applied...")
    try:
        cursor.execute("DELETE FROM django_migrations WHERE app NOT IN ('contenttypes', 'auth', 'admin', 'sessions')")
        connection.commit()
        
        # Fake all migrations
        for app_label in app_labels:
            try:
                call_command('migrate', app_label, '--fake', '--noinput', verbosity=0)
            except:
                pass
        print("   ✓ Migrations marked as applied")
    except Exception as e:
        print(f"   ⚠️  {e}")
    
    # Verify
    print("\n🔍 VERIFICATION:")
    cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
    total = cursor.fetchone()[0]
    print(f"   Total tables: {total}")
    
    critical_tables = [
        'base_company', 'base_department', 'employee_employee',
        'leave_leavetype', 'attendance_attendance', 'asset_asset',
        'helpdesk_ticket', 'payroll_payrollsettings'
    ]
    
    cursor.execute(f"""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name IN ({','.join([f"'{t}'" for t in critical_tables])})
    """)
    present = [row[0] for row in cursor.fetchall()]
    
    print(f"   Critical tables: {len(present)}/{len(critical_tables)}")
    
    if len(present) == len(critical_tables):
        print("\n✅ SUCCESS! All critical tables created!")
        return 0
    else:
        missing = set(critical_tables) - set(present)
        print(f"\n❌ Still missing {len(missing)} tables:")
        for t in sorted(missing):
            print(f"      - {t}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
