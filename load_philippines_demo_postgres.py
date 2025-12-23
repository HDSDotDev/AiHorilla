#!/usr/bin/env python3
"""
Postgres-targeted Philippines demo loader.

Clears the database (flush + migrate) and then runs the comprehensive
ORM `load_philippines_demo` generator.

This script is intended to be launched from the web UI's "Load demo data"
button; it requires the `RAILWAY_IMPORT_CONFIRMED=true` environment variable
when running non-interactively so that destructive operations are explicit.
"""

import os
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horilla.settings')

# Ensure schedulers/auditlog disabled during population
os.environ.setdefault('SKIP_SCHEDULERS', '1')
os.environ.setdefault('DJANGO_DISABLE_AUDITLOG', '1')

import django
print("[PH POSTGRES LOADER] Initializing Django...")
try:
    django.setup()
except Exception as e:
    print(f"❌ Django setup failed: {e}")
    sys.exit(1)

# Try to disable auditlog receivers if present
try:
    import auditlog.receivers
    auditlog.receivers.log_create = lambda *a, **k: None
    auditlog.receivers.log_update = lambda *a, **k: None
    auditlog.receivers.log_delete = lambda *a, **k: None
    print("[PH POSTGRES LOADER] Auditlog receivers disabled")
except Exception:
    pass

from django.core.management import call_command
from django.conf import settings
from django.db import connections
from django.db import connection

def check_postgres():
    db = settings.DATABASES.get('default', {})
    engine = db.get('ENGINE', '')
    if 'postgresql' not in engine:
        print(f"❌ This loader is intended for PostgreSQL. Current engine: {engine}")
        return False
    try:
        with connections['default'].cursor() as cursor:
            cursor.execute('SELECT 1')
    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        return False
    return True

def clear_database_noninteractive():
    """Flush and re-run migrations. Requires explicit confirmation in non-interactive mode."""
    print("[PH POSTGRES LOADER] Clearing database: flush + migrate")
    # If interactive, ask user
    if sys.stdin.isatty():
        resp = input("This will DELETE ALL DATA. Type YES to continue: ")
        if resp != 'YES':
            print("Cancelled by user")
            return False
    else:
        # Non-interactive: require explicit env var confirmation
        if os.environ.get('RAILWAY_IMPORT_CONFIRMED', '').lower() != 'true':
            print("❌ Non-interactive run requires RAILWAY_IMPORT_CONFIRMED=true")
            return False
        print("✅ Confirmed via RAILWAY_IMPORT_CONFIRMED")

    try:
        call_command('flush', '--noinput')
        call_command('migrate', '--noinput')
        print("[PH POSTGRES LOADER] Database flushed and migrations applied")
        
        # CRITICAL CHECK: Verify that critical tables exist after migration
        from django.db import connection
        critical_tables = ['employee_employee', 'base_company', 'recruitment_candidate']
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
            print(f"❌ CRITICAL: Tables still missing after migrate: {missing_tables}")
            print("🔥 NUCLEAR OPTION: Wiping database and starting fresh...")
            
            # Nuclear wipe like in fast_railway_deploy.py
            with connection.cursor() as cursor:
                cursor.execute("DROP SCHEMA public CASCADE")
                cursor.execute("CREATE SCHEMA public")
                cursor.execute("GRANT ALL ON SCHEMA public TO PUBLIC")
                cursor.execute("GRANT ALL ON SCHEMA public TO postgres")
            
            print("✅ Database wiped, re-running migrations...")
            call_command('migrate', '--noinput')
            print("✅ Migrations completed after nuclear wipe")
            
            # Verify again
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
                print(f"❌ FATAL: Tables still missing after nuclear wipe: {missing_tables}")
                return False
            else:
                print("✅ All critical tables exist after nuclear wipe")
        
        return True
    except Exception as e:
        print(f"❌ Clearing database failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_population(num_employees=40):
    print(f"[PH POSTGRES LOADER] Starting population for {num_employees} employees...")
    try:
        # Import the existing comprehensive generator and reuse it
        from load_philippines_demo import load_philippines_demo
        success = load_philippines_demo(num_employees)
        return success
    except Exception as e:
        print(f"❌ Population failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def write_completion_flag():
    try:
        flag = project_root / '.railway_import_complete'
        flag.write_text('completed')
        print(f"[PH POSTGRES LOADER] Wrote completion flag: {flag}")
    except Exception:
        pass

def main():
    # Default to 41 employees to mirror local/demo SQLite population
    num = int(sys.argv[1]) if len(sys.argv) > 1 else 41
    # Ensure deterministic seed to mirror local generator when possible
    os.environ.setdefault('DEMO_DATA_SEED', os.environ.get('DEMO_DATA_SEED', '123456'))
    if not check_postgres():
        return 1
    # Acquire a Postgres advisory lock to prevent concurrent destructive imports
    LOCK_KEY = 987654321
    locked = False
    try:
        with connection.cursor() as cur:
            cur.execute('SELECT pg_try_advisory_lock(%s);', [LOCK_KEY])
            row = cur.fetchone()
            locked = bool(row and row[0])
        if not locked:
            print("❌ Another import appears to be running. Aborting to avoid deadlocks.")
            return 4
        print("[PH POSTGRES LOADER] Acquired advisory lock for import")
    except Exception as e:
        print(f"[PH POSTGRES LOADER] Warning: could not acquire advisory lock: {e}")
        # Proceeding without advisory lock is risky but allowed in fallback
    if not clear_database_noninteractive():
        return 2
    try:
        ok = run_population(num)
    finally:
        # Release advisory lock if held
        try:
            if locked:
                with connection.cursor() as cur:
                    cur.execute('SELECT pg_advisory_unlock(%s);', [LOCK_KEY])
                print("[PH POSTGRES LOADER] Released advisory lock")
        except Exception:
            pass
    if ok:
        write_completion_flag()
        print("[PH POSTGRES LOADER] Population complete")
        return 0
    else:
        print("[PH POSTGRES LOADER] Population failed")
        return 3

if __name__ == '__main__':
    sys.exit(main())
