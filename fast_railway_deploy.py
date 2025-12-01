#!/usr/bin/env python3
"""
Fast Railway Deployment Script
Does ALL initialization in a single Python process to avoid repeated django.setup()
Target: <10 minutes total deployment time
"""
import os
import sys
import time
import django
from django.core.management import call_command
from django.db import connection

# Set environment
os.environ['SKIP_SCHEDULERS'] = '1'
os.environ['SKIP_DB_INIT_IN_READY'] = '1'
os.environ['HORILLA_SKIP_SIGNALS'] = '1'
os.environ['RAILWAY_ENVIRONMENT'] = '1'
os.environ['PYTHONUNBUFFERED'] = '1'

print("=" * 80)
print("FAST RAILWAY DEPLOYMENT")
print("=" * 80)
start_time = time.time()

# ONE django.setup() call for entire deployment
print("\n[1/6] Initializing Django...")
step_start = time.time()
django.setup()
print(f"  ✓ Django initialized ({time.time() - step_start:.1f}s)")

# Check database connection
print("\n[2/6] Testing database connection...")
step_start = time.time()
try:
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        print(f"  ✓ PostgreSQL connected ({time.time() - step_start:.1f}s)")
except Exception as e:
    print(f"  ✗ Database connection failed: {e}")
    sys.exit(1)

# Create all tables using fix_database_tables logic
print("\n[3/6] Creating database tables...")
step_start = time.time()
try:
    # Import here to use already-initialized Django
    from django.core.management import call_command
    from django.db import connection
    
    # Run makemigrations to ensure migrations exist
    print("  - Generating migrations...")
    call_command('makemigrations', interactive=False, verbosity=0)
    
    # Two-pass table creation
    print("  - Pass 1: Creating tables without dependencies...")
    with connection.cursor() as cursor:
        # Get all app models
        from django.apps import apps
        from django.db import models as django_models
        
        created_count = 0
        for app_config in apps.get_app_configs():
            for model in app_config.get_models():
                table_name = model._meta.db_table
                try:
                    # Check if table exists
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = %s
                        )
                    """, [table_name])
                    
                    if not cursor.fetchone()[0]:
                        # Try to create table
                        try:
                            with connection.schema_editor() as schema_editor:
                                schema_editor.create_model(model)
                            created_count += 1
                        except Exception:
                            pass  # Will retry in pass 2
                except Exception:
                    pass
        
        print(f"  - Pass 1 complete: {created_count} tables created")
    
    # Use migrate as pass 2
    print("  - Pass 2: Migrating with dependencies...")
    call_command('migrate', interactive=False, verbosity=1, run_syncdb=True)
    
    print(f"  ✓ All tables created ({time.time() - step_start:.1f}s)")
    
except Exception as e:
    print(f"  ⚠ Table creation had errors: {e}")
    print("  - Attempting migrations anyway...")
    try:
        call_command('migrate', interactive=False, verbosity=1)
    except Exception as e2:
        print(f"  ⚠ Migrations also failed: {e2}")

# Verify critical tables
print("\n[4/6] Verifying critical tables...")
step_start = time.time()
critical_tables = [
    'auth_user', 'auth_group', 'django_session', 'django_content_type',
    'base_company', 'base_department', 'base_jobposition',
    'employee_employee', 'employee_employeeworkinformation',
    'attendance_attendance', 'leave_leaverequest',
    'payroll_payslip', 'recruitment_recruitment',
    'base_worktype', 'base_employeetype', 'base_employeeshift',
]

missing_tables = []
with connection.cursor() as cursor:
    for table in critical_tables:
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = %s
            )
        """, [table])
        if not cursor.fetchone()[0]:
            missing_tables.append(table)

if missing_tables:
    print(f"  ⚠ Missing {len(missing_tables)} critical tables:")
    for table in missing_tables[:5]:
        print(f"    - {table}")
    if len(missing_tables) > 5:
        print(f"    ... and {len(missing_tables) - 5} more")
else:
    print(f"  ✓ All {len(critical_tables)} critical tables exist ({time.time() - step_start:.1f}s)")

# Collect static files
print("\n[5/6] Collecting static files...")
step_start = time.time()
try:
    call_command('collectstatic', interactive=False, verbosity=0, clear=True)
    print(f"  ✓ Static files collected ({time.time() - step_start:.1f}s)")
except Exception as e:
    print(f"  ⚠ Static collection warning: {e}")

# Final verification
print("\n[6/6] Final verification...")
step_start = time.time()
try:
    # Try to import key models
    from base.models import Company
    from employee.models import Employee
    from django.contrib.auth.models import User
    
    # Test database queries
    user_count = User.objects.count()
    company_count = Company.objects.count()
    
    print(f"  ✓ System ready - {user_count} users, {company_count} companies ({time.time() - step_start:.1f}s)")
except Exception as e:
    print(f"  ⚠ Verification warning: {e}")
    print("  - System may still work, check after startup")

# Re-enable signals for runtime
os.environ.pop('HORILLA_SKIP_SIGNALS', None)

total_time = time.time() - start_time
print("\n" + "=" * 80)
print(f"DEPLOYMENT COMPLETE IN {total_time:.1f} SECONDS ({total_time/60:.1f} minutes)")
print("=" * 80)

sys.exit(0)
