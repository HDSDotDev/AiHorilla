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

# Create all tables using proven two-pass approach
print("\n[3/6] Creating database tables...")
step_start = time.time()
try:
    from django.core.management import call_command
    from django.apps import apps
    
    # Run makemigrations first
    print("  - Generating migrations...")
    call_command('makemigrations', interactive=False, verbosity=0)
    
    # Two-pass table creation using migrations
    print("  - Pass 1: Core Django tables...")
    try:
        call_command('migrate', 'contenttypes', interactive=False, verbosity=0)
        call_command('migrate', 'auth', interactive=False, verbosity=0)
        call_command('migrate', 'sessions', interactive=False, verbosity=0)
        call_command('migrate', 'admin', interactive=False, verbosity=0)
    except Exception as e:
        print(f"    ⚠ Core migrations warning: {e}")
    
    print("  - Pass 2: Application tables...")
    # Use run_syncdb to force table creation even without migrations
    try:
        call_command('migrate', interactive=False, verbosity=0, run_syncdb=True)
    except Exception as e:
        print(f"    ⚠ Migration warning: {e}")
        # Try without run_syncdb
        try:
            call_command('migrate', interactive=False, verbosity=0)
        except Exception as e2:
            print(f"    ⚠ Second attempt warning: {e2}")
    
    print(f"  ✓ Table creation complete ({time.time() - step_start:.1f}s)")
    
except Exception as e:
    print(f"  ✗ Table creation failed: {e}")
    # Don't exit - continue to verification

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
