#!/usr/bin/env python3
"""
Railway Deployment Diagnostics Script
Run this to diagnose deployment issues
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horilla.settings')
django.setup()

from django.core.management import call_command
from django.db import connection
from django.db.migrations.executor import MigrationExecutor


def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")


def check_database_connection():
    """Check if database connection is working"""
    print_header("1. Database Connection Check")
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
        print("✓ Database connection: SUCCESS")
        print(f"  Database: {connection.settings_dict['ENGINE']}")
        print(f"  Name: {connection.settings_dict.get('NAME', 'N/A')}")
        return True
    except Exception as e:
        print(f"✗ Database connection: FAILED")
        print(f"  Error: {e}")
        return False


def check_migrations():
    """Check migration status"""
    print_header("2. Migration Status Check")
    try:
        executor = MigrationExecutor(connection)
        targets = executor.loader.graph.leaf_nodes()
        plan = executor.migration_plan(targets)
        
        if not plan:
            print("✓ All migrations applied: UP TO DATE")
        else:
            print(f"⚠ Pending migrations: {len(plan)} migration(s) need to be applied")
            print("\nPending migrations:")
            for migration, backwards in plan[:10]:  # Show first 10
                print(f"  - {migration}")
            if len(plan) > 10:
                print(f"  ... and {len(plan) - 10} more")
        
        return True
    except Exception as e:
        print(f"✗ Migration check: FAILED")
        print(f"  Error: {e}")
        return False


def check_models():
    """Check if all models can be imported"""
    print_header("3. Model Import Check")
    
    apps_to_check = [
        'base',
        'employee',
        'payroll',
        'attendance',
        'leave',
        'asset',
    ]
    
    failed = []
    for app_name in apps_to_check:
        try:
            __import__(f'{app_name}.models')
            print(f"✓ {app_name}.models: OK")
        except Exception as e:
            print(f"✗ {app_name}.models: FAILED - {e}")
            failed.append(app_name)
    
    if not failed:
        print("\n✓ All models imported successfully")
    else:
        print(f"\n⚠ {len(failed)} app(s) failed to import")
    
    return len(failed) == 0


def check_environment():
    """Check environment variables"""
    print_header("4. Environment Variables Check")
    
    required_vars = [
        'SECRET_KEY',
        'DJANGO_SETTINGS_MODULE',
    ]
    
    optional_vars = [
        'DATABASE_URL',
        'DEBUG',
        'ALLOWED_HOSTS',
        'PORT',
    ]
    
    print("Required variables:")
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            masked = value[:10] + '...' if len(value) > 10 else value
            print(f"  ✓ {var}: {masked}")
        else:
            print(f"  ✗ {var}: NOT SET")
    
    print("\nOptional variables:")
    for var in optional_vars:
        value = os.environ.get(var)
        if value:
            if var == 'DATABASE_URL':
                # Mask sensitive database URL
                print(f"  ✓ {var}: <set>")
            else:
                print(f"  ✓ {var}: {value}")
        else:
            print(f"  ⚠ {var}: not set")


def check_tables():
    """Check if tables exist in database"""
    print_header("5. Database Tables Check")
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            tables = cursor.fetchall()
            
        if tables:
            print(f"✓ Found {len(tables)} tables in database")
            print("\nSample tables:")
            for table in tables[:10]:
                print(f"  - {table[0]}")
            if len(tables) > 10:
                print(f"  ... and {len(tables) - 10} more")
        else:
            print("⚠ No tables found in database")
            print("  This is normal for a fresh deployment")
        
        return True
    except Exception as e:
        # Try SQLite query if PostgreSQL query fails
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' 
                    ORDER BY name
                """)
                tables = cursor.fetchall()
                
            if tables:
                print(f"✓ Found {len(tables)} tables in database (SQLite)")
                print("\nSample tables:")
                for table in tables[:10]:
                    print(f"  - {table[0]}")
            else:
                print("⚠ No tables found in database")
            return True
        except Exception as e2:
            print(f"✗ Could not list tables: {e2}")
            return False


def main():
    print("\n" + "="*60)
    print("  HORILLA RAILWAY DEPLOYMENT DIAGNOSTICS")
    print("="*60)
    
    checks = [
        check_environment,
        check_database_connection,
        check_models,
        check_migrations,
        check_tables,
    ]
    
    results = []
    for check in checks:
        try:
            result = check()
            results.append(result)
        except Exception as e:
            print(f"\n✗ Check failed with error: {e}")
            results.append(False)
    
    # Summary
    print_header("SUMMARY")
    passed = sum(results)
    total = len(results)
    
    print(f"Checks passed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ All checks passed! Your deployment should work.")
    else:
        print("\n⚠ Some checks failed. Review the output above for details.")
        print("\nTroubleshooting tips:")
        print("1. Ensure DATABASE_URL is set correctly")
        print("2. Run migrations: python manage.py migrate")
        print("3. Check Railway logs for detailed error messages")
    
    print("\n" + "="*60)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDiagnostics interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        sys.exit(1)
