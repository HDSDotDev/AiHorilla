#!/usr/bin/env python3
"""
Railway Data Import Script
This script runs on Railway to import the SQLite database dump into PostgreSQL.
It should be run once after deployment with the full_database_dump.json file.
"""

import os
import sys
import django
from pathlib import Path

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horilla.settings')

print("="*80)
print(" RAILWAY DATABASE IMPORT - SQLite to PostgreSQL")
print("="*80)

print("\nInitializing Django...")
try:
    django.setup()
except Exception as e:
    print(f"❌ Error setting up Django: {e}")
    sys.exit(1)

from django.core.management import call_command
from django.conf import settings
from django.db import connections
from django.apps import apps

def check_database():
    """Verify we're using PostgreSQL on Railway"""
    print("\n[1/5] Checking Database Configuration...")
    
    db_config = settings.DATABASES['default']
    engine = db_config['ENGINE']
    
    if 'postgresql' not in engine:
        print(f"❌ Not using PostgreSQL! Current engine: {engine}")
        print("This script should only run on Railway with PostgreSQL.")
        return False
    
    print(f"✅ PostgreSQL configured")
    print(f"   Database: {db_config.get('NAME', 'unknown')}")
    print(f"   Host: {db_config.get('HOST', 'unknown')}")
    
    # Test connection
    try:
        with connections['default'].cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            print(f"   Version: {version[:60]}...")
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def check_dump_file():
    """Check if the dump file exists"""
    print("\n[2/5] Checking for Data Dump File...")
    
    dump_file = Path(__file__).parent / 'full_database_dump.json'
    
    if not dump_file.exists():
        print(f"❌ Dump file not found: {dump_file}")
        print("\nThe full_database_dump.json file must be present in the repository.")
        return None
    
    size_mb = dump_file.stat().st_size / (1024 * 1024)
    print(f"✅ Dump file found: {size_mb:.2f} MB")
    
    return dump_file

def clear_database():
    """Clear existing data from PostgreSQL"""
    print("\n[3/5] Clearing Existing Data...")
    
    print("⚠️  This will DELETE ALL existing data in the Railway PostgreSQL database!")
    
    # Check if we're in an interactive terminal
    if sys.stdin.isatty():
        response = input("\nType 'YES' to continue: ")
        if response != 'YES':
            print("❌ Import cancelled")
            return False
    else:
        # Non-interactive (Railway deployment) - check for environment flag
        if os.environ.get('RAILWAY_IMPORT_CONFIRMED') != 'true':
            print("❌ Import not confirmed. Set RAILWAY_IMPORT_CONFIRMED=true to proceed.")
            return False
        print("✅ Auto-confirmed via RAILWAY_IMPORT_CONFIRMED environment variable")
    
    try:
        print("\nRunning migrations first...")
        call_command('migrate', '--noinput', verbosity=1)
        
        print("\nFlushing database...")
        call_command('flush', '--noinput', verbosity=1)
        
        print("✅ Database cleared")
        return True
        
    except Exception as e:
        print(f"❌ Clear failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def import_data(dump_file):
    """Import data from JSON dump"""
    print("\n[4/5] Importing Data...")
    
    print(f"Loading data from: {dump_file.name}")
    print("This may take 5-10 minutes for large datasets...")
    print("(Railway deployments have a 30-minute timeout)")
    
    try:
        call_command('loaddata', str(dump_file), verbosity=2)
        print("\n✅ Data imported successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        
        # Try to provide helpful error messages
        if 'duplicate key' in str(e).lower():
            print("\nError: Duplicate key detected. The database may not have been fully cleared.")
        elif 'does not exist' in str(e).lower():
            print("\nError: Table or relation missing. Migrations may not have run correctly.")
        
        return False

def verify_import():
    """Verify data was imported correctly"""
    print("\n[5/5] Verifying Import...")
    
    try:
        total_records = 0
        tables_with_data = 0
        
        print("\nRecord counts by model:")
        print("-" * 80)
        
        for model in apps.get_models():
            try:
                count = model.objects.count()
                if count > 0:
                    app_label = model._meta.app_label
                    model_name = model._meta.model_name
                    full_name = f"{app_label}.{model_name}"
                    print(f"  {full_name:45} {count:6,} records")
                    total_records += count
                    tables_with_data += 1
            except Exception:
                pass
        
        print("-" * 80)
        print(f"\n✅ Import Verification Complete!")
        print(f"   Total records: {total_records:,}")
        print(f"   Tables with data: {tables_with_data}")
        
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

def create_completion_flag():
    """Create a flag file to indicate successful import"""
    try:
        flag_file = Path(__file__).parent / '.railway_import_complete'
        flag_file.write_text(f"Import completed at: {os.popen('date').read()}")
        print(f"\n✅ Created completion flag: {flag_file}")
    except Exception as e:
        print(f"⚠️  Could not create completion flag: {e}")

def main():
    """Execute the import process"""
    try:
        # Check if already imported
        flag_file = Path(__file__).parent / '.railway_import_complete'
        if flag_file.exists() and os.environ.get('FORCE_REIMPORT') != 'true':
            print("\n⚠️  Import already completed (found .railway_import_complete)")
            print("To re-import, set FORCE_REIMPORT=true environment variable")
            return True
        
        # Step 1: Check database
        if not check_database():
            return False
        
        # Step 2: Check dump file
        dump_file = check_dump_file()
        if not dump_file:
            return False
        
        # Step 3: Clear database
        if not clear_database():
            return False
        
        # Step 4: Import data
        if not import_data(dump_file):
            return False
        
        # Step 5: Verify
        verify_import()
        
        # Create completion flag
        create_completion_flag()
        
        print("\n" + "="*80)
        print(" IMPORT COMPLETE! ")
        print("="*80)
        print("\nYour Railway PostgreSQL database now matches your local SQLite database.")
        print("The application can now be started.")
        
        return True
        
    except KeyboardInterrupt:
        print("\n\n❌ Import cancelled by user")
        return False
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
