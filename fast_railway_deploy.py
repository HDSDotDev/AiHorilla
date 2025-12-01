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

# Set environment - CRITICAL: Set DJANGO_SETTINGS_MODULE first
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horilla.settings')
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

# CRITICAL: Verify migration files exist
print("\n[DEBUG] Checking migration files...")
import glob
employee_migrations = glob.glob('/app/employee/migrations/0*.py')
payroll_migrations = glob.glob('/app/payroll/migrations/0*.py')
print(f"  - Employee migrations found: {len(employee_migrations)}")
for mig in sorted(employee_migrations):
    print(f"    • {os.path.basename(mig)}")
print(f"  - Payroll migrations found: {len(payroll_migrations)}")
for mig in sorted(payroll_migrations)[:3]:  # First 3 only
    print(f"    • {os.path.basename(mig)}")
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

# Create all tables - force migrate with fake-initial to ensure all tables exist
print("\n[3/6] Creating database tables...")
step_start = time.time()

from django.core.management import call_command
from django.apps import apps

# CRITICAL: Check which tables actually exist
print("  - Checking for existing tables and migration state...")
with connection.cursor() as cursor:
    # Get list of all existing tables
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
    """)
    existing_table_names = {row[0] for row in cursor.fetchall()}
    
    # Check django_migrations table
    cursor.execute("SELECT COUNT(*) FROM django_migrations")
    migration_records = cursor.fetchone()[0]
    
    print(f"  - Found {len(existing_table_names)} total tables in database")
    print(f"  - Found {migration_records} migration records in django_migrations")
    
    # Check critical tables
    critical_missing = []
    critical_tables = {
        'employee_employee': 'employee',
        'base_company': 'base',
        'attendance_attendance': 'attendance',
        'leave_leaverequest': 'leave',
        'payroll_payslip': 'payroll'
    }
    
    for table_name, app_name in critical_tables.items():
        if table_name not in existing_table_names:
            critical_missing.append((table_name, app_name))
    
    if critical_missing:
        print(f"  ⚠ CRITICAL TABLES MISSING:")
        for table_name, app_name in critical_missing:
            print(f"    - {table_name} (from {app_name} app)")
        print(f"  → Will run migrations normally for these apps")
    elif len(existing_table_names) > 30 and migration_records < 50:
        print(f"  ⚠ MIGRATION STATE MISMATCH (tables exist but not tracked)")
        print(f"    Using --fake-initial to sync state...")
        try:
            # Use --fake-initial: fake only if tables already exist
            call_command('migrate', '--fake-initial', interactive=False, verbosity=1)
            print(f"  ✓ Migration state synchronized")
        except Exception as e:
            print(f"  ⚠ Warning during state sync: {e}")
    elif len(existing_table_names) == 0:
        print(f"  ✓ Fresh database - will create all tables")
    else:
        print(f"  ✓ Migration state appears correct")

print("  - Running migrations...")

# Run migrations with VERBOSE output to see what's failing
print("  - Migrating core Django apps...")
core_apps = ['contenttypes', 'auth', 'sessions', 'admin']
for app in core_apps:
    try:
        call_command('migrate', app, interactive=False, verbosity=1)
    except Exception as e:
        print(f"  ✗ {app} FAILED: {e}")

# Explicitly migrate critical apps with dependencies in order
print("  - Migrating critical application apps...")
critical_apps = [
    'horilla_audit',  # employee depends on this
    'base',           # employee depends on this
    'employee',       # CRITICAL - creates employee_employee
    'attendance', 
    'leave', 
    'payroll', 
    'recruitment'
]
for app in critical_apps:
    try:
        print(f"  - Migrating {app}...")
        call_command('migrate', app, interactive=False, verbosity=1)
        print(f"  ✓ {app} completed")
    except Exception as e:
        print(f"  ✗ {app} FAILED: {str(e)[:200]}")
        import traceback
        traceback.print_exc()

# Verify employee_employee table was created
print("  - Verifying employee_employee table...")
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'employee_employee'
        )
    """)
    if cursor.fetchone()[0]:
        print("  ✓ employee_employee table EXISTS")
    else:
        print("  ✗ employee_employee table MISSING - migration failed!")

# Migrate remaining apps
print("  - Migrating remaining apps...")
try:
    call_command('migrate', interactive=False, verbosity=0)
    print("  ✓ All migrations complete")
except Exception as e:
    print(f"  ⚠ Final migration warning: {e}")

# Then explicitly create any missing tables via fake migrations
print("  - Ensuring all app tables exist...")
missing_apps = []
with connection.cursor() as cursor:
    # Check critical tables
    critical_checks = [
        ('employee_employee', 'employee'),
        ('base_company', 'base'),
        ('attendance_attendance', 'attendance'),
        ('leave_leaverequest', 'leave'),
        ('payroll_payslip', 'payroll'),
    ]
    
    for table_name, app_name in critical_checks:
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = %s
            )
        """, [table_name])
        
        if not cursor.fetchone()[0]:
            missing_apps.append(app_name)
            print(f"  ⚠ Missing table: {table_name}")

# If any critical tables missing, try fake-initial then migrate
if missing_apps:
    print(f"  - Running fake-initial for {len(set(missing_apps))} apps...")
    for app in set(missing_apps):
        try:
            call_command('migrate', app, '--fake-initial', interactive=False, verbosity=0)
        except Exception as e:
            print(f"    ⚠ {app}: {e}")
    
    # Re-run migrate
    try:
        call_command('migrate', '--run-syncdb', interactive=False, verbosity=0)
    except Exception:
        pass

print(f"  ✓ Table creation complete ({time.time() - step_start:.1f}s)")

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
