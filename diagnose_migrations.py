#!/usr/bin/env python3
"""
Diagnostic script to understand why migrations aren't creating tables.
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horilla.settings')
django.setup()

from django.apps import apps
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

def main():
    print("="*80)
    print("  MIGRATION SYSTEM DIAGNOSTICS")
    print("="*80)
    
    # Check installed apps
    print("\n1. INSTALLED_APPS:")
    for app in ['base', 'employee', 'leave', 'asset', 'attendance', 'payroll']:
        try:
            app_config = apps.get_app_config(app)
            print(f"   ✓ {app}: {app_config.path}")
        except LookupError:
            print(f"   ❌ {app}: NOT FOUND")
    
    # Check migration files
    print("\n2. MIGRATION FILES:")
    import importlib
    for app in ['base', 'employee', 'leave']:
        try:
            migrations_module = importlib.import_module(f'{app}.migrations')
            migrations_path = os.path.dirname(migrations_module.__file__)
            files = [f for f in os.listdir(migrations_path) if f.endswith('.py') and f != '__init__.py']
            print(f"   {app}: {len(files)} migration files")
            print(f"      Path: {migrations_path}")
            if len(files) > 0:
                print(f"      First: {files[0]}")
        except Exception as e:
            print(f"   {app}: ❌ {e}")
    
    # Check migration executor
    print("\n3. MIGRATION EXECUTOR:")
    try:
        executor = MigrationExecutor(connection)
        print(f"   Connection: {connection.settings_dict['ENGINE']}")
        print(f"   Database: {connection.settings_dict['NAME']}")
        
        # Get migration plan
        targets = executor.loader.graph.leaf_nodes()
        print(f"   Leaf nodes (target migrations): {len(targets)}")
        
        plan = executor.migration_plan(targets)
        print(f"   Migration plan: {len(plan)} migrations to apply")
        
        if len(plan) > 0:
            print("\n   First 10 migrations in plan:")
            for migration, backwards in plan[:10]:
                print(f"      {'⬅️ ' if backwards else '➡️ '} {migration.app_label}.{migration.name}")
        else:
            print("   ⚠️  No migrations in plan - all already applied?")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Check applied migrations
    print("\n4. APPLIED MIGRATIONS:")
    cursor = connection.cursor()
    cursor.execute("SELECT app, name FROM django_migrations ORDER BY id DESC LIMIT 10")
    rows = cursor.fetchall()
    if rows:
        print(f"   Last 10 applied migrations:")
        for app, name in rows:
            print(f"      {app}.{name}")
    else:
        print("   ⚠️  No migrations applied yet")
    
    # Check if models are properly defined
    print("\n5. MODEL DEFINITIONS:")
    for app_label in ['base', 'employee', 'leave']:
        try:
            app_config = apps.get_app_config(app_label)
            models = app_config.get_models()
            print(f"   {app_label}: {len(models)} models")
            for model in list(models)[:3]:
                print(f"      - {model.__name__} → {model._meta.db_table}")
        except Exception as e:
            print(f"   {app_label}: ❌ {e}")
    
    # Check database state
    print("\n6. DATABASE TABLES:")
    cursor.execute("""
        SELECT COUNT(*) FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
    """)
    print(f"   Total tables: {cursor.fetchone()[0]}")
    
    cursor.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name LIKE 'base_%'
        ORDER BY table_name
    """)
    base_tables = [row[0] for row in cursor.fetchall()]
    if base_tables:
        print(f"   Base app tables ({len(base_tables)}): {', '.join(base_tables[:5])}")
    else:
        print("   ❌ No base app tables found")
    
    print("\n" + "="*80)

if __name__ == '__main__':
    main()
