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
    num = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    if not check_postgres():
        return 1
    if not clear_database_noninteractive():
        return 2
    ok = run_population(num)
    if ok:
        write_completion_flag()
        print("[PH POSTGRES LOADER] Population complete")
        return 0
    else:
        print("[PH POSTGRES LOADER] Population failed")
        return 3

if __name__ == '__main__':
    sys.exit(main())
