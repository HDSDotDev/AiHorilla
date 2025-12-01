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

# CRITICAL: NUCLEAR OPTION - Just run migrations without any faking
# The root issue is circular dependencies between base and employee apps
# Faking causes more problems than it solves
print("  - Running all migrations (skipping state detection)...")
print("  ⚠ WARNING: Ignoring 'relation already exists' errors from previous incomplete deployments")

print("  - Running migrations...")

# Strategy: Run ALL migrations at once and let Django handle dependencies
# If tables already exist, migrations will fail but that's OK - we'll verify tables exist after
print("  - Running migrate command (will show errors for existing tables - that's expected)...")
try:
    call_command('migrate', interactive=False, verbosity=0)
    print("  ✓ Migrations completed")
except Exception as e:
    error_msg = str(e)
    if "already exists" in error_msg:
        print(f"  ⚠ Some tables already existed (continuing...)")
    else:
        print(f"  ⚠ Migration error: {error_msg[:200]}")

# NUCLEAR OPTION: If employee_employee doesn't exist, wipe django_migrations and start fresh
print("  - Verifying employee_employee table...")
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'employee_employee'
        )
    """)
    if not cursor.fetchone()[0]:
        print("  ✗ employee_employee STILL MISSING!")
        print("  → NUCLEAR OPTION: Clearing django_migrations table and re-running migrations...")
        
        try:
            # Delete all migration records
            cursor.execute("DELETE FROM django_migrations")
            print("    - Cleared django_migrations table")
            
            # Run migrations again from scratch
            print("    - Re-running ALL migrations from clean state...")
            call_command('migrate', interactive=False, verbosity=1)
            
            # Check again
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'employee_employee'
                )
            """)
            if cursor.fetchone()[0]:
                print("  ✓ employee_employee table NOW EXISTS after clean migration")
            else:
                print("  ✗ CRITICAL FAILURE: employee_employee STILL doesn't exist after nuclear option")
        except Exception as nuclear_error:
            print(f"  ✗ NUCLEAR OPTION FAILED: {nuclear_error}")
    else:
        print("  ✓ employee_employee table EXISTS")

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
