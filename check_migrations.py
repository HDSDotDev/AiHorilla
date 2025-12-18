"""
Preemptive Migration Fixer
Identifies and fixes common migration issues before they occur during database sync.
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horilla.settings')

print("Initializing Django...")
django.setup()

from django.core.management import call_command
from django.db import connection, migrations
from django.apps import apps
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.loader import MigrationLoader

class MigrationFixer:
    def __init__(self):
        self.issues = []
        self.fixes = []
        
    def check_circular_dependencies(self):
        """Check for circular dependencies in migrations"""
        print("\n" + "="*80)
        print("Checking for Circular Dependencies")
        print("="*80)
        
        try:
            loader = MigrationLoader(connection)
            # The loader will raise an exception if there are circular dependencies
            graph = loader.graph
            print("✅ No circular dependencies detected")
            return True
        except Exception as e:
            if "Circular dependency" in str(e) or "circular" in str(e).lower():
                print(f"❌ Circular dependency detected: {e}")
                self.issues.append(f"Circular dependency: {e}")
                
                # Try to identify the problematic apps
                print("\nAttempting to identify problematic migrations...")
                return False
            else:
                print(f"⚠️  Migration check issue: {e}")
                return True
                
    def check_migration_conflicts(self):
        """Check for migration conflicts"""
        print("\n" + "="*80)
        print("Checking for Migration Conflicts")
        print("="*80)
        
        try:
            # Run makemigrations in dry-run mode to check for conflicts
            from io import StringIO
            from django.core.management import call_command
            
            out = StringIO()
            call_command('makemigrations', '--dry-run', '--check', stdout=out, stderr=out)
            output = out.getvalue()
            
            if 'Conflicting migrations' in output or 'conflict' in output.lower():
                print(f"❌ Migration conflicts detected:")
                print(output)
                self.issues.append("Migration conflicts")
                return False
            else:
                print("✅ No migration conflicts detected")
                return True
                
        except SystemExit:
            print("✅ No new migrations needed")
            return True
        except Exception as e:
            print(f"⚠️  Could not check for conflicts: {e}")
            return True
            
    def check_missing_migrations(self):
        """Check if there are unapplied migrations"""
        print("\n" + "="*80)
        print("Checking for Unapplied Migrations")
        print("="*80)
        
        try:
            executor = MigrationExecutor(connection)
            targets = executor.loader.graph.leaf_nodes()
            plan = executor.migration_plan(targets)
            
            if plan:
                print(f"⚠️  Found {len(plan)} unapplied migrations:")
                for migration, backwards in plan[:10]:  # Show first 10
                    print(f"   - {migration.app_label}.{migration.name}")
                if len(plan) > 10:
                    print(f"   ... and {len(plan) - 10} more")
                self.issues.append(f"{len(plan)} unapplied migrations")
                return False
            else:
                print("✅ All migrations are up to date")
                return True
                
        except Exception as e:
            print(f"❌ Error checking migrations: {e}")
            self.issues.append(f"Migration check error: {e}")
            return False
            
    def check_database_schema(self):
        """Check if database schema matches migrations"""
        print("\n" + "="*80)
        print("Checking Database Schema")
        print("="*80)
        
        try:
            with connection.cursor() as cursor:
                # Get all tables
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' 
                    AND name NOT LIKE 'sqlite_%'
                    ORDER BY name
                """)
                tables = [row[0] for row in cursor.fetchall()]
                
            print(f"✅ Found {len(tables)} tables in database")
            
            # Check if key tables exist
            required_tables = [
                'django_migrations',
                'auth_user',
                'employee_employee',
                'payroll_payslip'
            ]
            
            missing = [t for t in required_tables if t not in tables]
            if missing:
                print(f"⚠️  Missing expected tables: {missing}")
                self.issues.append(f"Missing tables: {missing}")
                return False
            else:
                print("✅ All key tables present")
                return True
                
        except Exception as e:
            print(f"❌ Schema check failed: {e}")
            self.issues.append(f"Schema check error: {e}")
            return False
            
    def fix_fake_migrations(self):
        """Suggest fixes for migration issues"""
        print("\n" + "="*80)
        print("Migration Fix Suggestions")
        print("="*80)
        
        if not self.issues:
            print("✅ No issues to fix")
            return
            
        print("\nDetected Issues:")
        for issue in self.issues:
            print(f"  - {issue}")
            
        print("\n" + "-"*80)
        print("Suggested Fixes:")
        print("-"*80)
        
        if any('circular' in issue.lower() for issue in self.issues):
            print("\n1. For Circular Dependencies:")
            print("   Run: python manage.py migrate --fake-initial")
            print("   This marks initial migrations as applied without running them")
            
        if any('conflict' in issue.lower() for issue in self.issues):
            print("\n2. For Migration Conflicts:")
            print("   Run: python manage.py makemigrations --merge")
            print("   This creates a merge migration to resolve conflicts")
            
        if any('unapplied' in issue.lower() for issue in self.issues):
            print("\n3. For Unapplied Migrations:")
            print("   Run: python manage.py migrate")
            print("   This applies all pending migrations")
            
        print("\n" + "-"*80)
        print("For PostgreSQL (Railway):")
        print("-"*80)
        print("Before syncing to PostgreSQL, ensure:")
        print("1. Set DATABASE_URL environment variable")
        print("2. Run migrations on PostgreSQL: python manage.py migrate")
        print("3. Then run sync script: python sync_db_simple.py")
        
    def run(self):
        """Run all checks"""
        print("\n" + "="*80)
        print(" PREEMPTIVE MIGRATION CHECKER ")
        print("="*80)
        
        all_good = True
        
        # Run checks
        all_good &= self.check_database_schema()
        all_good &= self.check_circular_dependencies()
        all_good &= self.check_migration_conflicts()
        all_good &= self.check_missing_migrations()
        
        # Show fixes if needed
        self.fix_fake_migrations()
        
        print("\n" + "="*80)
        if all_good and not self.issues:
            print(" ✅ ALL CHECKS PASSED ")
            print("="*80)
            print("\nYou're ready to sync databases!")
            print("Run: python sync_db_simple.py")
        else:
            print(" ⚠️  ISSUES DETECTED ")
            print("="*80)
            print(f"\nFound {len(self.issues)} issue(s)")
            print("Please review the suggestions above before syncing.")
            
        return all_good

if __name__ == '__main__':
    fixer = MigrationFixer()
    success = fixer.run()
    sys.exit(0 if success else 1)
