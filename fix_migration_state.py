#!/usr/bin/env python
"""
Fix Django migration state by marking all existing migrations as applied.
This resolves the "relation already exists" error when tables exist but 
django_migrations table is out of sync.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horilla.settings')
django.setup()

from django.core.management import call_command
from django.db import connection

def fix_migration_state():
    """Mark all migrations as applied without running them (fake)."""
    
    print("\n" + "="*80)
    print("FIXING DJANGO MIGRATION STATE")
    print("="*80)
    
    # Check if tables exist
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE '%\_%'
        """)
        table_count = cursor.fetchone()[0]
        print(f"\n✓ Found {table_count} existing tables in database")
    
    if table_count > 50:  # If many tables exist, assume previous deployment
        print("\n⚠ Database has existing tables but migrations are out of sync")
        print("  Marking all migrations as applied (--fake)...\n")
        
        try:
            # Fake all migrations to sync state
            call_command('migrate', '--fake', interactive=False, verbosity=2)
            print("\n✓ Migration state synchronized successfully!")
            return True
        except Exception as e:
            print(f"\n❌ Error syncing migrations: {e}")
            return False
    else:
        print("\n✓ Database appears fresh, no state fix needed")
        return True

if __name__ == '__main__':
    success = fix_migration_state()
    sys.exit(0 if success else 1)
