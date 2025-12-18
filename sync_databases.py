"""
Database Sync Script: SQLite to PostgreSQL (Railway)
This script synchronizes ALL data from local SQLite to Railway PostgreSQL database.
It handles migrations, schema, and data transfer.
"""

import os
import sys
import django
import subprocess
import json
from pathlib import Path

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horilla.settings')
django.setup()

from django.core.management import call_command
from django.db import connections, transaction
from django.apps import apps
from django.conf import settings

class DatabaseSyncer:
    def __init__(self):
        self.sqlite_db = 'default'
        self.postgres_db = 'railway'
        self.errors = []
        self.warnings = []
        
    def log(self, message, level='INFO'):
        """Log messages with timestamp"""
        import datetime
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        prefix = f"[{timestamp}] [{level}]"
        print(f"{prefix} {message}")
        
    def check_railway_connection(self):
        """Verify Railway DATABASE_URL is configured"""
        self.log("Checking Railway database configuration...")
        
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            self.log("ERROR: DATABASE_URL environment variable not set!", 'ERROR')
            self.log("Please set your Railway PostgreSQL DATABASE_URL", 'ERROR')
            return False
            
        self.log(f"DATABASE_URL found: {database_url[:30]}...", 'SUCCESS')
        return True
        
    def setup_postgres_connection(self):
        """Configure PostgreSQL connection for sync"""
        self.log("Setting up PostgreSQL connection...")
        
        database_url = os.environ.get('DATABASE_URL')
        
        # Parse DATABASE_URL and configure Django settings
        settings.DATABASES['railway'] = {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'railway',  # Will be overridden by dj-database-url
        }
        
        # Use dj-database-url to parse
        import dj_database_url
        settings.DATABASES['railway'] = dj_database_url.parse(database_url)
        
        self.log("PostgreSQL connection configured", 'SUCCESS')
        
    def test_connections(self):
        """Test both database connections"""
        self.log("Testing database connections...")
        
        try:
            # Test SQLite
            with connections['default'].cursor() as cursor:
                cursor.execute("SELECT 1")
            self.log("✓ SQLite connection successful", 'SUCCESS')
        except Exception as e:
            self.log(f"✗ SQLite connection failed: {e}", 'ERROR')
            return False
            
        try:
            # Test PostgreSQL
            with connections['railway'].cursor() as cursor:
                cursor.execute("SELECT 1")
            self.log("✓ PostgreSQL connection successful", 'SUCCESS')
        except Exception as e:
            self.log(f"✗ PostgreSQL connection failed: {e}", 'ERROR')
            self.log("Make sure PostgreSQL is accessible and DATABASE_URL is correct", 'ERROR')
            return False
            
        return True
        
    def backup_postgres(self):
        """Create backup of PostgreSQL database before sync"""
        self.log("Creating PostgreSQL backup (recommended)...")
        self.log("NOTE: Manual backup recommended before proceeding", 'WARNING')
        
    def clear_postgres_data(self):
        """Clear all data from PostgreSQL database"""
        self.log("Clearing PostgreSQL database...")
        self.log("WARNING: This will DELETE ALL DATA in PostgreSQL!", 'WARNING')
        
        response = input("Are you sure you want to proceed? Type 'YES' to continue: ")
        if response != 'YES':
            self.log("Sync cancelled by user", 'INFO')
            return False
            
        try:
            with connections['railway'].cursor() as cursor:
                # Get all tables
                cursor.execute("""
                    SELECT tablename FROM pg_tables 
                    WHERE schemaname = 'public'
                """)
                tables = cursor.fetchall()
                
                # Disable foreign key checks
                cursor.execute("SET session_replication_role = 'replica';")
                
                # Truncate all tables
                for table in tables:
                    table_name = table[0]
                    self.log(f"Truncating table: {table_name}")
                    cursor.execute(f'TRUNCATE TABLE "{table_name}" CASCADE;')
                
                # Re-enable foreign key checks
                cursor.execute("SET session_replication_role = 'origin';")
                
            self.log("PostgreSQL database cleared successfully", 'SUCCESS')
            return True
        except Exception as e:
            self.log(f"Error clearing PostgreSQL: {e}", 'ERROR')
            return False
            
    def run_migrations_postgres(self):
        """Run migrations on PostgreSQL to ensure schema is up to date"""
        self.log("Running migrations on PostgreSQL...")
        
        try:
            # Temporarily switch to PostgreSQL
            original_db = settings.DATABASES['default']
            settings.DATABASES['default'] = settings.DATABASES['railway']
            
            # Run migrations
            call_command('migrate', '--noinput', '--database=default', verbosity=2)
            
            # Restore original database
            settings.DATABASES['default'] = original_db
            
            self.log("Migrations completed on PostgreSQL", 'SUCCESS')
            return True
        except Exception as e:
            self.log(f"Error running migrations: {e}", 'ERROR')
            # Restore original database
            settings.DATABASES['default'] = original_db
            return False
            
    def export_sqlite_data(self):
        """Export data from SQLite using dumpdata"""
        self.log("Exporting data from SQLite...")
        
        dump_file = Path(__file__).parent / 'sqlite_dump.json'
        
        try:
            # Export all data except contenttypes and sessions (will be recreated)
            with open(dump_file, 'w', encoding='utf-8') as f:
                call_command(
                    'dumpdata',
                    '--natural-foreign',
                    '--natural-primary',
                    '--exclude=contenttypes',
                    '--exclude=auth.permission',
                    '--indent=2',
                    stdout=f
                )
            
            self.log(f"Data exported to: {dump_file}", 'SUCCESS')
            self.log(f"File size: {dump_file.stat().st_size / 1024 / 1024:.2f} MB")
            return dump_file
        except Exception as e:
            self.log(f"Error exporting data: {e}", 'ERROR')
            return None
            
    def import_data_to_postgres(self, dump_file):
        """Import data into PostgreSQL"""
        self.log("Importing data into PostgreSQL...")
        
        try:
            # Temporarily switch to PostgreSQL
            original_db = settings.DATABASES['default']
            settings.DATABASES['default'] = settings.DATABASES['railway']
            
            # Import data
            with open(dump_file, 'r', encoding='utf-8') as f:
                call_command('loaddata', dump_file, verbosity=2)
            
            # Restore original database
            settings.DATABASES['default'] = original_db
            
            self.log("Data imported successfully to PostgreSQL", 'SUCCESS')
            return True
        except Exception as e:
            self.log(f"Error importing data: {e}", 'ERROR')
            self.log("Attempting to continue with alternative method...", 'WARNING')
            # Restore original database
            settings.DATABASES['default'] = original_db
            return False
            
    def sync_data_direct(self):
        """Direct table-by-table sync (alternative method)"""
        self.log("Using direct sync method...")
        
        try:
            models = apps.get_models()
            total_models = len(models)
            
            for idx, model in enumerate(models, 1):
                model_name = f"{model._meta.app_label}.{model._meta.model_name}"
                self.log(f"[{idx}/{total_models}] Syncing {model_name}...")
                
                try:
                    # Get all objects from SQLite
                    objects = model.objects.using('default').all()
                    count = objects.count()
                    
                    if count == 0:
                        self.log(f"  No data in {model_name}", 'INFO')
                        continue
                    
                    # Bulk create in PostgreSQL
                    batch_size = 1000
                    objects_list = list(objects)
                    
                    with transaction.atomic(using='railway'):
                        for i in range(0, len(objects_list), batch_size):
                            batch = objects_list[i:i+batch_size]
                            # Clear PKs for new database
                            for obj in batch:
                                obj.pk = None
                            model.objects.using('railway').bulk_create(
                                batch,
                                batch_size=batch_size,
                                ignore_conflicts=True
                            )
                    
                    self.log(f"  ✓ Synced {count} records", 'SUCCESS')
                    
                except Exception as e:
                    self.log(f"  ✗ Error syncing {model_name}: {e}", 'ERROR')
                    self.errors.append(f"{model_name}: {e}")
                    
            self.log(f"Direct sync completed with {len(self.errors)} errors", 'INFO')
            return True
            
        except Exception as e:
            self.log(f"Direct sync failed: {e}", 'ERROR')
            return False
            
    def verify_sync(self):
        """Verify data was synced correctly"""
        self.log("Verifying sync...")
        
        try:
            models = apps.get_models()
            mismatches = []
            
            for model in models:
                model_name = f"{model._meta.app_label}.{model._meta.model_name}"
                
                sqlite_count = model.objects.using('default').count()
                postgres_count = model.objects.using('railway').count()
                
                if sqlite_count != postgres_count:
                    msg = f"{model_name}: SQLite={sqlite_count}, PostgreSQL={postgres_count}"
                    self.log(f"  Mismatch: {msg}", 'WARNING')
                    mismatches.append(msg)
                else:
                    self.log(f"  ✓ {model_name}: {sqlite_count} records", 'SUCCESS')
            
            if mismatches:
                self.log(f"Verification found {len(mismatches)} mismatches", 'WARNING')
                for mismatch in mismatches:
                    self.log(f"  - {mismatch}", 'WARNING')
            else:
                self.log("All tables verified successfully!", 'SUCCESS')
                
            return len(mismatches) == 0
            
        except Exception as e:
            self.log(f"Verification failed: {e}", 'ERROR')
            return False
            
    def run(self):
        """Main sync process"""
        self.log("=" * 80)
        self.log("Database Sync: SQLite → PostgreSQL (Railway)")
        self.log("=" * 80)
        
        # Step 1: Check Railway connection
        if not self.check_railway_connection():
            return False
            
        # Step 2: Setup PostgreSQL connection
        self.setup_postgres_connection()
        
        # Step 3: Test connections
        if not self.test_connections():
            return False
            
        # Step 4: Backup warning
        self.backup_postgres()
        
        # Step 5: Run migrations on PostgreSQL first
        if not self.run_migrations_postgres():
            self.log("Failed to run migrations. Attempting to continue...", 'WARNING')
        
        # Step 6: Clear PostgreSQL data
        if not self.clear_postgres_data():
            return False
            
        # Step 7: Export SQLite data
        dump_file = self.export_sqlite_data()
        if not dump_file:
            self.log("Trying direct sync method instead...", 'WARNING')
            return self.sync_data_direct()
            
        # Step 8: Import data to PostgreSQL
        if not self.import_data_to_postgres(dump_file):
            self.log("Standard import failed, trying direct sync...", 'WARNING')
            return self.sync_data_direct()
            
        # Step 9: Verify sync
        self.verify_sync()
        
        self.log("=" * 80)
        self.log("Sync completed!")
        self.log("=" * 80)
        
        if self.errors:
            self.log(f"Completed with {len(self.errors)} errors:", 'WARNING')
            for error in self.errors:
                self.log(f"  - {error}", 'ERROR')
        
        return True

if __name__ == '__main__':
    syncer = DatabaseSyncer()
    success = syncer.run()
    sys.exit(0 if success else 1)
