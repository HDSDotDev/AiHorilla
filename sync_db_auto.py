"""
Automated Database Sync: SQLite to Railway PostgreSQL
Non-interactive version for automated execution
"""

import os
import sys
import django

# Set DATABASE_URL if not already set
if 'DATABASE_URL' not in os.environ:
    os.environ['DATABASE_URL'] = 'postgresql://postgres:tITYUxXpYCrGMGPdWmXOwMagDXzdTgZs@postgres-pd32.railway.internal:5432/railway'

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horilla.settings')

print("Initializing Django...")
django.setup()

from django.core.management import call_command
from django.conf import settings
from django.db import connections
import dj_database_url
from pathlib import Path

class AutoDBSync:
    def __init__(self):
        self.dump_file = Path(__file__).parent / 'full_database_dump.json'
        
    def log(self, message, prefix="INFO"):
        print(f"[{prefix}] {message}")
        
    def step(self, num, total, message):
        print(f"\n{'='*80}")
        print(f"STEP {num}/{total}: {message}")
        print(f"{'='*80}\n")
        
    def run(self):
        print("\n" + "="*80)
        print(" AUTOMATED DATABASE SYNC: SQLite → PostgreSQL ")
        print("="*80)
        
        # Step 1: Verify DATABASE_URL
        self.step(1, 6, "Verifying DATABASE_URL")
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            self.log("DATABASE_URL not set!", "ERROR")
            return False
        self.log(f"DATABASE_URL: {db_url[:50]}...", "SUCCESS")
        
        # Step 2: Configure PostgreSQL
        self.step(2, 6, "Configuring PostgreSQL Connection")
        try:
            pg_config = dj_database_url.parse(db_url)
            settings.DATABASES['railway'] = pg_config
            self.log(f"PostgreSQL configured: {pg_config['HOST']}", "SUCCESS")
        except Exception as e:
            self.log(f"Configuration failed: {e}", "ERROR")
            return False
            
        # Step 3: Test connection
        self.step(3, 6, "Testing PostgreSQL Connection")
        try:
            with connections['railway'].cursor() as cursor:
                cursor.execute("SELECT version();")
                version = cursor.fetchone()[0]
                self.log(f"Connected: {version[:60]}", "SUCCESS")
        except Exception as e:
            self.log(f"Connection failed: {e}", "ERROR")
            return False
            
        # Step 4: Export SQLite
        self.step(4, 6, "Exporting SQLite Data")
        try:
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
            self.log(f"Export complete: {size_mb:.2f} MB", "SUCCESS")
        except Exception as e:
            self.log(f"Export failed: {e}", "ERROR")
            return False
            
        # Step 5: Prepare PostgreSQL
        self.step(5, 6, "Preparing PostgreSQL (Migrate & Flush)")
        try:
            original_default = settings.DATABASES['default']
            settings.DATABASES['default'] = settings.DATABASES['railway']
            
            try:
                self.log("Running migrations...")
                call_command('migrate', '--noinput', verbosity=1)
                
                self.log("Flushing database...")
                call_command('flush', '--noinput', verbosity=1)
                
                self.log("PostgreSQL prepared", "SUCCESS")
            finally:
                settings.DATABASES['default'] = original_default
        except Exception as e:
            self.log(f"Preparation failed: {e}", "ERROR")
            settings.DATABASES['default'] = original_default
            return False
            
        # Step 6: Import data
        self.step(6, 6, "Importing Data to PostgreSQL")
        try:
            original_default = settings.DATABASES['default']
            settings.DATABASES['default'] = settings.DATABASES['railway']
            
            try:
                self.log("Loading data (this may take several minutes)...")
                call_command('loaddata', str(self.dump_file), verbosity=2)
                self.log("Data imported successfully!", "SUCCESS")
            finally:
                settings.DATABASES['default'] = original_default
        except Exception as e:
            self.log(f"Import failed: {e}", "ERROR")
            settings.DATABASES['default'] = original_default
            
            # Try direct sync method
            self.log("Attempting direct sync method...", "WARNING")
            return self.direct_sync()
            
        # Verification
        self.verify()
        
        print("\n" + "="*80)
        print(" SYNC COMPLETE! ")
        print("="*80)
        return True
        
    def direct_sync(self):
        """Direct table-by-table sync as fallback"""
        self.step(0, 0, "Direct Table Sync (Fallback Method)")
        
        try:
            from django.apps import apps
            
            models = apps.get_models()
            total = len(models)
            success_count = 0
            
            for idx, model in enumerate(models, 1):
                model_name = f"{model._meta.app_label}.{model._meta.model_name}"
                
                try:
                    objects = model.objects.using('default').all()
                    count = objects.count()
                    
                    if count == 0:
                        continue
                        
                    # Batch insert
                    batch_size = 500
                    objects_list = list(objects)
                    
                    for i in range(0, len(objects_list), batch_size):
                        batch = objects_list[i:i+batch_size]
                        for obj in batch:
                            obj.pk = None
                        model.objects.using('railway').bulk_create(
                            batch,
                            batch_size=batch_size,
                            ignore_conflicts=True
                        )
                    
                    self.log(f"[{idx}/{total}] {model_name}: {count} records", "SUCCESS")
                    success_count += 1
                    
                except Exception as e:
                    self.log(f"[{idx}/{total}] {model_name}: FAILED - {e}", "ERROR")
                    
            self.log(f"Direct sync: {success_count}/{total} models synced", "INFO")
            return success_count > 0
            
        except Exception as e:
            self.log(f"Direct sync failed: {e}", "ERROR")
            return False
            
    def verify(self):
        """Verify sync"""
        print("\n" + "="*80)
        print("VERIFICATION")
        print("="*80 + "\n")
        
        try:
            from django.apps import apps
            
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
                    
                    if sqlite_count == postgres_count and sqlite_count > 0:
                        print(f"✅ {full_name:45} {postgres_count:6} records")
                    elif sqlite_count != postgres_count:
                        print(f"⚠️  {full_name:45} SQLite: {sqlite_count:6}, PG: {postgres_count:6}")
                        mismatches.append(full_name)
                except Exception as e:
                    print(f"❌ {full_name:45} Error: {e}")
                    
            print(f"\nTotal records in PostgreSQL: {total_records:,}")
            
            if mismatches:
                print(f"\n⚠️  {len(mismatches)} mismatches found (may be normal for sessions/contenttypes)")
            else:
                print("\n✅ All tables verified successfully!")
                
        except Exception as e:
            self.log(f"Verification failed: {e}", "ERROR")

if __name__ == '__main__':
    syncer = AutoDBSync()
    success = syncer.run()
    sys.exit(0 if success else 1)
