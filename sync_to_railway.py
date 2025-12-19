"""
Sync Local SQLite to Railway PostgreSQL
This script imports the exported SQLite data into Railway PostgreSQL.
"""

import os
import sys
import django

# Get DATABASE_URL from command line argument
if len(sys.argv) < 2:
    print("Usage: python sync_to_railway.py <DATABASE_URL>")
    print("\nExample:")
    print('python sync_to_railway.py "postgresql://postgres:password@host:port/dbname"')
    sys.exit(1)

database_url = sys.argv[1]

# Set DATABASE_URL environment variable
os.environ['DATABASE_URL'] = database_url

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horilla.settings')

print("Initializing Django with Railway PostgreSQL...")
try:
    django.setup()
except Exception as e:
    print(f"Error setting up Django: {e}")
    sys.exit(1)

from django.core.management import call_command
from django.conf import settings
from django.db import connections
from pathlib import Path
import dj_database_url

def print_step(num, total, message):
    """Print step header"""
    print(f"\n{'='*80}")
    print(f"STEP {num}/{total}: {message}")
    print(f"{'='*80}\n")

def test_connection():
    """Test PostgreSQL connection"""
    print_step(1, 4, "Testing Railway PostgreSQL Connection")
    
    try:
        with connections['default'].cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            print(f"✅ PostgreSQL connected successfully!")
            print(f"   Version: {version[:80]}")
            
            # Get database info
            cursor.execute("SELECT current_database(), current_user;")
            dbname, user = cursor.fetchone()
            print(f"   Database: {dbname}")
            print(f"   User: {user}")
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check if DATABASE_URL is correct")
        print("2. Verify PostgreSQL service is running on Railway")
        print("3. Check if you're running this from Railway deployment")
        return False

def prepare_database():
    """Run migrations and clear existing data"""
    print_step(2, 4, "Preparing PostgreSQL Database")
    
    try:
        # Run migrations
        print("Running migrations...")
        call_command('migrate', '--noinput', verbosity=1)
        print("✅ Migrations complete")
        
        # Ask for confirmation
        print("\n⚠️  WARNING: This will DELETE ALL existing data in PostgreSQL!")
        parsed = dj_database_url.parse(database_url)
        print(f"   Database: {parsed.get('NAME', 'unknown')}")
        print(f"   Host: {parsed.get('HOST', 'unknown')}")
        
        response = input("\nType 'DELETE ALL DATA' to continue: ")
        if response != 'DELETE ALL DATA':
            print("❌ Sync cancelled")
            return False
        
        # Flush the database
        print("\nClearing all data...")
        call_command('flush', '--noinput', verbosity=1)
        print("✅ Database cleared")
        
        return True
        
    except Exception as e:
        print(f"❌ Preparation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def import_data():
    """Import data from JSON dump"""
    print_step(3, 4, "Importing SQLite Data to PostgreSQL")
    
    dump_file = Path(__file__).parent / 'full_database_dump.json'
    
    if not dump_file.exists():
        print(f"❌ Dump file not found: {dump_file}")
        print("\nPlease run the export first:")
        print("python manage.py dumpdata --natural-foreign --natural-primary --exclude=contenttypes --exclude=auth.permission --indent=2 > full_database_dump.json")
        return False
    
    size_mb = dump_file.stat().st_size / (1024 * 1024)
    print(f"Loading data from: {dump_file} ({size_mb:.2f} MB)")
    print("This may take several minutes...")
    
    try:
        call_command('loaddata', str(dump_file), verbosity=2)
        print("✅ Data imported successfully!")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_import():
    """Verify data was imported"""
    print_step(4, 4, "Verifying Data Import")
    
    try:
        from django.apps import apps
        
        print("Counting records in PostgreSQL...\n")
        
        total_records = 0
        tables_with_data = 0
        
        for model in apps.get_models():
            try:
                count = model.objects.count()
                if count > 0:
                    app_label = model._meta.app_label
                    model_name = model._meta.model_name
                    print(f"✅ {app_label}.{model_name:40} {count:6} records")
                    total_records += count
                    tables_with_data += 1
            except Exception:
                pass
        
        print(f"\n{'='*80}")
        print(f"Total records imported: {total_records:,}")
        print(f"Tables with data: {tables_with_data}")
        print("✅ Import verified!")
        
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Execute the sync process"""
    print("\n" + "="*80)
    print(" SQLite → Railway PostgreSQL Sync ")
    print("="*80)
    
    try:
        # Step 1: Test connection
        if not test_connection():
            return False
        
        # Step 2: Prepare database
        if not prepare_database():
            return False
        
        # Step 3: Import data
        if not import_data():
            return False
        
        # Step 4: Verify
        verify_import()
        
        print("\n" + "="*80)
        print(" SYNC COMPLETE! ")
        print("="*80)
        print("\nYour Railway PostgreSQL database now contains all data from SQLite.")
        
        return True
        
    except KeyboardInterrupt:
        print("\n\n❌ Sync cancelled by user")
        return False
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
