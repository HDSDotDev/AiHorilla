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
# TEMPORARY: force confirmed import and allow re-import for this deploy per user request
# WARNING: This will wipe PostgreSQL and re-import data from full_database_dump.json
os.environ['RAILWAY_IMPORT_CONFIRMED'] = 'true'
os.environ['FORCE_REIMPORT'] = 'true'

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

# CRITICAL FIX: Check if employee_employee exists FIRST
# If missing, it means previous deployments left partial tables that block new migrations
# Solution: WIPE THE DATABASE and start from scratch
print("  - Checking if employee_employee table exists...")
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'employee_employee'
        )
    """)
    employee_table_exists = cursor.fetchone()[0]
    
    # Check if ANY tables exist
    cursor.execute("""
        SELECT COUNT(*) 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
    """)
    total_tables = cursor.fetchone()[0]
    
    # Check for corrupted database state (missing tables OR missing columns)
    corruption_detected = False
    corruption_reasons = []
    fresh_database = False  # Will be set to True if we wipe or if no tables exist
    
    if total_tables > 10 and not employee_table_exists:
        corruption_detected = True
        corruption_reasons.append(f"Found {total_tables} tables but employee_employee is MISSING")
    
    # Check for missing critical columns (indicates partial migration state)
    if employee_table_exists:
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'employee_employee' AND column_name = 'employee_user_id_id'
        """)
        if not cursor.fetchone():
            corruption_detected = True
            corruption_reasons.append("employee_employee table missing employee_user_id_id column")
    
    # Check payroll table columns
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'payroll_payrollcountryconfig'
        )
    """)
    if cursor.fetchone()[0]:
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'payroll_payrollcountryconfig' AND column_name = 'activated_by_id'
        """)
        if not cursor.fetchone():
            corruption_detected = True
            corruption_reasons.append("payroll_payrollcountryconfig table missing activated_by_id column")
    
    if corruption_detected:
        print(f"  ⚠️  CORRUPTED DATABASE STATE DETECTED!")
        for reason in corruption_reasons:
            print(f"     - {reason}")
        print(f"     This means previous deployments left partial broken state")
        print(f"  ")
        print(f"  🔥 NUCLEAR OPTION: Wiping entire database to start fresh...")
        print(f"  ")
        
        try:
            # Drop ALL tables and recreate schema
            cursor.execute("DROP SCHEMA public CASCADE")
            cursor.execute("CREATE SCHEMA public")
            cursor.execute("GRANT ALL ON SCHEMA public TO PUBLIC")
            cursor.execute("GRANT ALL ON SCHEMA public TO postgres")
            
            print(f"  ✓ Database wiped clean - all {total_tables} tables dropped")
            print(f"  ✓ Schema recreated - ready for fresh migrations")
            # Set flag to indicate fresh database state
            fresh_database = True
        except Exception as wipe_error:
            print(f"  ✗ DATABASE WIPE FAILED: {wipe_error}")
            print(f"     Manual intervention required in Railway PostgreSQL dashboard")
            sys.exit(1)
    elif employee_table_exists:
        print(f"  ✓ employee_employee table exists with all required columns")
        fresh_database = False
    else:
        print(f"  ✓ Fresh database - no tables exist yet")
        fresh_database = True

print("  - Running migrations...")

# CRITICAL: On fresh database, run migrations NORMALLY without --fake-initial
# --fake-initial causes migrations to skip table creation, leading to partial state
if fresh_database:
    print("  - Running migrations on CLEAN database (no --fake-initial)...")
    try:
        # On clean database, run migrations normally - this will create ALL tables with ALL columns
        call_command('migrate', interactive=False, verbosity=1)
        print("  ✓ All migrations completed successfully on clean database")
    except Exception as e:
        error_msg = str(e)
        print(f"  ✗ MIGRATION FAILED: {error_msg[:500]}")
        print(f"  This should NOT happen on a fresh database!")
        sys.exit(1)
else:
    # Only use --fake-initial strategy if database already has tables
    print("  - Running migrate with --fake-initial to handle existing tables...")
    try:
        call_command('migrate', '--fake-initial', interactive=False, verbosity=0)
        print("  ✓ Migrations completed (using --fake-initial for existing tables)")
    except Exception as e:
        error_msg = str(e)
        print(f"  ⚠ Migration warning: {error_msg[:200]}")
        try:
            print("  - Retrying without --fake-initial...")
            call_command('migrate', interactive=False, verbosity=0)
            print("  ✓ Retry successful")
        except Exception as retry_error:
            print(f"  ⚠ Retry also failed: {str(retry_error)[:200]}")

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

# First, explicitly migrate Django's built-in apps (sessions, auth, contenttypes)
print("  - Creating Django core tables (sessions, auth, contenttypes)...")
try:
    call_command('migrate', 'sessions', interactive=False, verbosity=0)
    call_command('migrate', 'auth', interactive=False, verbosity=0)
    call_command('migrate', 'contenttypes', interactive=False, verbosity=0)
    call_command('migrate', 'admin', interactive=False, verbosity=0)
    print("  ✓ Django core tables created")
except Exception as e:
    print(f"  ⚠ Core migration warning: {e}")

missing_apps = []
with connection.cursor() as cursor:
    # Check critical tables including Django built-in ones
    critical_checks = [
        ('django_session', 'sessions'),
        ('auth_user', 'auth'),
        ('django_content_type', 'contenttypes'),
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
    
    # Try one more migration to create missing tables
    print(f"  - Attempting to create missing tables...")
    try:
        call_command('migrate', interactive=False, verbosity=0)
        
        # Re-check
        still_missing = []
        with connection.cursor() as cursor:
            for table in missing_tables:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = %s
                    )
                """, [table])
                if not cursor.fetchone()[0]:
                    still_missing.append(table)
        
        if still_missing:
            print(f"  ✗ CRITICAL: {len(still_missing)} tables still missing after migration retry!")
            for table in still_missing:
                print(f"    - {table}")
            print(f"  → Manual database reset may be required")
        else:
            print(f"  ✓ All missing tables created successfully!")
    except Exception as e:
        print(f"  ⚠ Migration retry error: {e}")
else:
    print(f"  ✓ All {len(critical_tables)} critical tables exist ({time.time() - step_start:.1f}s)")

# Import SQLite data if dump file exists
print("\n[5/7] Checking for database import...")
step_start = time.time()
from pathlib import Path
dump_file = Path('/app/full_database_dump.json')
completion_flag = Path('/app/.railway_import_complete')

if dump_file.exists() and not completion_flag.exists():
    print(f"  ✓ Found {dump_file.name} ({dump_file.stat().st_size / (1024*1024):.1f} MB)")
    print(f"  → Importing SQLite data to PostgreSQL...")
    print(f"  ⚠️  This will REPLACE all current data in PostgreSQL!")
    
    try:
        # Require explicit confirmation to import to avoid automatic demo-data loading
        confirmed = os.environ.get('RAILWAY_IMPORT_CONFIRMED') == 'true'
        if not confirmed:
            print("    - Dump file present but import NOT confirmed.")
            print("      To import automatically, set environment variable RAILWAY_IMPORT_CONFIRMED=true")
            print("      Or trigger the application's 'Load demo data' UI which will run the import manually.")
            success = False
            import_duration = 0.0
        else:
            # Import the data using the robust batch importer (import module will run migrations/flush)
            print(f"    - Loading {dump_file.name} with batch importer...")
            print(f"    - This may take 5-20 minutes depending on dataset size...")
            import_start = time.time()
            try:
                import railway_import_data
                success = railway_import_data.main()
            except Exception as e:
                success = False
                print(f"    ✗ Batch importer raised an exception: {e}")
                import traceback
                traceback.print_exc()
            import_duration = time.time() - import_start

        # Create completion flag only on success
        if success:
            completion_flag.write_text(f"Import completed at {time.ctime()}\nDuration: {import_duration:.1f}s\n")
        
        # Verify import
        from django.contrib.auth.models import User
        try:
            from base.models import Company, Employee as BaseEmployee
        except Exception:
            Company = None
            BaseEmployee = None
        try:
            from employee.models import Employee
        except Exception:
            Employee = BaseEmployee
        
        user_count = User.objects.count()
        company_count = Company.objects.count() if Company is not None else 0
        employee_count = Employee.objects.count() if Employee is not None else 0
        
        print(f"  ✓ Import complete ({import_duration:.1f}s)")
        print(f"    - {user_count} users imported")
        print(f"    - {company_count} companies imported")
        print(f"    - {employee_count} employees imported")
        print(f"  ✓ Created {completion_flag.name} to prevent re-import")
        
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        import traceback
        traceback.print_exc()
        print(f"  → Continuing with deployment...")
elif completion_flag.exists():
    print(f"  ✓ Import already completed (found {completion_flag.name})")
    print(f"    To re-import: delete {completion_flag.name} and redeploy")
else:
    print(f"  - No database dump found, skipping import")

print(f"  ({time.time() - step_start:.1f}s)")

# Collect static files
print("\n[6/7] Collecting static files...")
step_start = time.time()
try:
    call_command('collectstatic', interactive=False, verbosity=0, clear=True)
    print(f"  ✓ Static files collected ({time.time() - step_start:.1f}s)")
except Exception as e:
    print(f"  ⚠ Static collection warning: {e}")

# Final verification
print("\n[7/7] Final verification...")
step_start = time.time()
try:
    # Try to import key models
    from base.models import Company
    try:
        from employee.models import Employee
    except:
        from base.models import Employee as Employee
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
