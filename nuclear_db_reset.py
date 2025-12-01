#!/usr/bin/env python3
"""
NUCLEAR DATABASE RESET - Drop ALL tables and start from scratch
Use this ONCE to fix corrupted Railway database state
"""
import os
import sys
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horilla.settings')
django.setup()

print("=" * 80)
print("NUCLEAR DATABASE RESET")
print("=" * 80)
print()
print("⚠️  WARNING: This will DROP ALL TABLES in the database!")
print("⚠️  This cannot be undone!")
print()

with connection.cursor() as cursor:
    # Get all table names
    cursor.execute("""
        SELECT tablename 
        FROM pg_tables 
        WHERE schemaname = 'public'
    """)
    tables = [row[0] for row in cursor.fetchall()]
    
    if not tables:
        print("✓ Database is already empty")
        sys.exit(0)
    
    print(f"Found {len(tables)} tables to drop:")
    for table in sorted(tables)[:10]:
        print(f"  - {table}")
    if len(tables) > 10:
        print(f"  ... and {len(tables) - 10} more")
    print()
    
    print("Dropping all tables...")
    
    # Drop all tables in a single transaction
    cursor.execute("DROP SCHEMA public CASCADE")
    cursor.execute("CREATE SCHEMA public")
    cursor.execute("GRANT ALL ON SCHEMA public TO PUBLIC")
    
    print("✓ All tables dropped successfully")
    print()
    print("Database is now clean. Run migrations to rebuild schema:")
    print("  python manage.py migrate")
