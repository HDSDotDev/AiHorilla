"""
Simplified Database Sync: SQLite to Railway PostgreSQL
This script provides a step-by-step database sync process with error handling.
"""

import os
import sys
import django
import subprocess
from pathlib import Path

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horilla.settings')

print("Initializing Django...")
try:
    django.setup()
except Exception as e:
    print(f"Error setting up Django: {e}")
    sys.exit(1)

from django.core.management import call_command, execute_from_command_line
from django.conf import settings
from django.db import connections
import dj_database_url

class SimpleDBSync:
    def __init__(self):
        self.dump_file = Path(__file__).parent / 'full_database_dump.json'
        
    def step(self, num, total, message):
        """Print step header"""
        print(f"\n{'='*80}")
        print(f"STEP {num}/{total}: {message}")
        print(f"{'='*80}\n")
        
    def check_database_url(self):
        """Check if DATABASE_URL is set"""
        self.step(1, 7, "Checking Railway DATABASE_URL")
        
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            print("❌ DATABASE_URL environment variable not set!")
            print("\nPlease set it using one of these methods:")
            print("\n1. PowerShell (current session):")
            print('   $env:DATABASE_URL="postgresql://user:pass@host:port/dbname"')
            print("\n2. Create .env file in horilla directory with:")
            print('   DATABASE_URL=postgresql://user:pass@host:port/dbname')
            print("\n3. Run the configuration helper:")
            print('   python configure_railway_db.py')
            return False
            
        print(f"✅ DATABASE_URL found: {db_url[:40]}...")
        
        # Parse and validate
        try:
            parsed = dj_database_url.parse(db_url)
            print(f"   Database: {parsed.get('NAME', 'unknown')}")
            print(f"   Host: {parsed.get('HOST', 'unknown')}")
            print(f"   Engine: {parsed.get('ENGINE', 'unknown')}")
        except Exception as e:
            print(f"⚠️  Warning: Could not parse DATABASE_URL: {e}")
            
        return True
        
    def export_sqlite(self):
        """Export all data from SQLite"""
        self.step(2, 7, "Exporting SQLite Database")
        
        print(f"Exporting data to: {self.dump_file}")
        print("This may take a few minutes...")
        
        try:
            # Use Django's dumpdata command
            with open(self.dump_file, 'w', encoding='utf-8') as f:
                call_command(
                    'dumpdata',
                    '--natural-foreign',
                    '--natural-primary',
                    '--exclude=contenttypes',
                    '--exclude=auth.permission',
                    '--indent=2',
                    stdout=f,
                    verbosity=1
                )
            
            size_mb = self.dump_file.stat().st_size / (1024 * 1024)
            print(f"✅ Export complete: {size_mb:.2f} MB")
            return True
            
        except Exception as e:
            print(f"❌ Export failed: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    def configure_postgres(self):
        """Configure PostgreSQL connection"""
        self.step(3, 7, "Configuring PostgreSQL Connection")
        
        db_url = os.environ.get('DATABASE_URL')
        
        # Parse the DATABASE_URL and add to settings
        try:
            pg_config = dj_database_url.parse(db_url)
            settings.DATABASES['railway'] = pg_config
            print("✅ PostgreSQL configured")
            print(f"   Host: {pg_config['HOST']}")
            print(f"   Database: {pg_config['NAME']}")
            return True
        except Exception as e:
            print(f"❌ Configuration failed: {e}")
            return False
            
    def test_postgres_connection(self):
        """Test PostgreSQL connection"""
        self.step(4, 7, "Testing PostgreSQL Connection")
        
        try:
            # Test connection
            with connections['railway'].cursor() as cursor:
                cursor.execute("SELECT version();")
                version = cursor.fetchone()[0]
                print(f"✅ PostgreSQL connected successfully!")
                print(f"   Version: {version[:80]}")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            print("\nTroubleshooting:")
            print("1. Check if DATABASE_URL is correct")
            print("2. Verify PostgreSQL service is running on Railway")
            print("3. Check firewall/network settings")
            return False
            
    def prepare_postgres(self):
        """Prepare PostgreSQL database"""
        self.step(5, 7, "Preparing PostgreSQL Database")
        
        print("⚠️  WARNING: This will DELETE ALL existing data in PostgreSQL!")
        print(f"   Database: {settings.DATABASES['railway']['NAME']}")
        print(f"   Host: {settings.DATABASES['railway']['HOST']}")
        
        response = input("\nType 'DELETE ALL DATA' to continue: ")
        if response != 'DELETE ALL DATA':
            print("❌ Sync cancelled")
            return False
            
        try:
            # Flush the database
            print("\nFlushing PostgreSQL database...")
            
            # Temporarily point default to railway for management commands
            original_default = settings.DATABASES['default']
            settings.DATABASES['default'] = settings.DATABASES['railway']
            
            try:
                # Run migrations first to ensure schema exists
                print("Running migrations...")
                call_command('migrate', '--noinput', verbosity=1)
                
                # Flush all data
                print("Clearing all data...")
                call_command('flush', '--noinput', verbosity=1)
                
                print("✅ PostgreSQL prepared successfully")
                return True
                
            finally:
                # Restore original default
                settings.DATABASES['default'] = original_default
                
        except Exception as e:
            print(f"❌ Preparation failed: {e}")
            import traceback
            traceback.print_exc()
            # Restore original default
            settings.DATABASES['default'] = original_default
            return False
            
    def import_to_postgres(self):
        """Import data into PostgreSQL"""
        self.step(6, 7, "Importing Data to PostgreSQL")
        
        if not self.dump_file.exists():
            print(f"❌ Dump file not found: {self.dump_file}")
            return False
            
        try:
            # Temporarily point default to railway
            original_default = settings.DATABASES['default']
            settings.DATABASES['default'] = settings.DATABASES['railway']
            
            try:
                print(f"Loading data from: {self.dump_file}")
                print("This may take several minutes...")
                
                # Load the data
                call_command('loaddata', str(self.dump_file), verbosity=2)
                
                print("✅ Data imported successfully!")
                return True
                
            finally:
                # Restore original default
                settings.DATABASES['default'] = original_default
                
        except Exception as e:
            print(f"❌ Import failed: {e}")
            print("\nAttempting alternative import method...")
            import traceback
            traceback.print_exc()
            
            # Restore original default
            settings.DATABASES['default'] = original_default
            return False
            
    def verify_sync(self):
        """Verify the sync completed successfully"""
        self.step(7, 7, "Verifying Database Sync")
        
        try:
            from django.apps import apps
            
            print("Comparing record counts between SQLite and PostgreSQL...\n")
            
            mismatches = []
            total_records = 0
            
            for model in apps.get_models():
                app_label = model._meta.app_label
                model_name = model._meta.model_name
                full_name = f"{app_label}.{model_name}"
                
                try:
                    sqlite_count = model.objects.using('default').count()
                    postgres_count = model.objects.using('railway').count()
                    total_records += postgres_count
                    
                    if sqlite_count == postgres_count:
                        if sqlite_count > 0:
                            print(f"✅ {full_name:50} {postgres_count:6} records")
                    else:
                        mismatch = f"❌ {full_name:50} SQLite: {sqlite_count:6}, PostgreSQL: {postgres_count:6}"
                        print(mismatch)
                        mismatches.append(mismatch)
                        
                except Exception as e:
                    print(f"⚠️  {full_name:50} Error: {e}")
                    
            print(f"\n{'='*80}")
            print(f"Total records in PostgreSQL: {total_records:,}")
            
            if mismatches:
                print(f"\n⚠️  Found {len(mismatches)} mismatches:")
                for mismatch in mismatches:
                    print(f"   {mismatch}")
                print("\nNote: Some differences may be expected (e.g., sessions, contenttypes)")
            else:
                print("\n✅ All tables verified successfully!")
                
            return len(mismatches) == 0
            
        except Exception as e:
            print(f"❌ Verification failed: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    def run(self):
        """Execute the full sync process"""
        print("\n" + "="*80)
        print(" SQLite → PostgreSQL Database Sync ")
        print("="*80)
        
        try:
            # Step 1: Check DATABASE_URL
            if not self.check_database_url():
                return False
                
            # Step 2: Export SQLite
            if not self.export_sqlite():
                return False
                
            # Step 3: Configure PostgreSQL
            if not self.configure_postgres():
                return False
                
            # Step 4: Test connection
            if not self.test_postgres_connection():
                return False
                
            # Step 5: Prepare PostgreSQL
            if not self.prepare_postgres():
                return False
                
            # Step 6: Import data
            if not self.import_to_postgres():
                return False
                
            # Step 7: Verify
            self.verify_sync()
            
            print("\n" + "="*80)
            print(" SYNC COMPLETE! ")
            print("="*80)
            print("\nYour Railway PostgreSQL database now contains all data from SQLite.")
            print(f"Backup file saved at: {self.dump_file}")
            
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
    syncer = SimpleDBSync()
    success = syncer.run()
    sys.exit(0 if success else 1)
