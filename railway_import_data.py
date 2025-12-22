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
        # Flush existing data first to avoid FK conflicts during migrate/post_migrate
        # (some environments contain stale permission/contenttype rows that cause
        # migrations to fail when Django attempts to create permissions).
        print("\nFlushing database (remove existing rows)...")
        call_command('flush', '--noinput', verbosity=1)

        print("\nRunning migrations to recreate schema and core rows...")
        call_command('migrate', '--noinput', verbosity=1)

        print("✅ Database cleared and migrations applied")
        return True
        
    except Exception as e:
        print(f"❌ Clear failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def import_data(dump_file):
    """Import data from JSON dump"""
    import json
    from django.apps import apps
    from django.db import transaction
    BATCH_SIZE = 500
    print("\n[4/5] Importing Data (batch mode)...")
    print(f"Loading data from: {dump_file.name}")
    print("This may take 5-20 minutes for large datasets...")
    print("(Railway deployments have a 30-minute timeout)")
    try:
        with open(dump_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"Loaded JSON: {len(data):,} objects")
        # Group by model
        from collections import defaultdict
        model_map = defaultdict(list)
        for obj in data:
            model_map[obj["model"]].append(obj)
        print(f"Found {len(model_map)} models in dump.")
        # Ensure content types import first to satisfy FK from auth.Permission
        prioritized = []
        if 'contenttypes.contenttype' in model_map:
            prioritized.append('contenttypes.contenttype')
        if 'auth.permission' in model_map:
            # defer auth.permission until after contenttypes
            pass
        # iterate prioritized first, then the rest
        ordered_models = prioritized + [k for k in model_map.keys() if k not in prioritized]
        # rebuild model_map iteration order using ordered_models
        from collections import defaultdict as _dd
        m2m_queues = _dd(list)

        from django.db import models as _djmodels

        def _resolve_fk_value(val, related_model):
            """
            Resolve a foreign-key-like identifier to a PK.
            Accepts numeric IDs, single-element lists, and common natural-key strings.
            Special-cases ContentType natural-key tuples (app_label, model).
            Returns integer PK or None.
            """
            if val is None:
                return None

            # Handle list/tuple natural-key wrappers (dumpdata sometimes stores as ["x"])
            if isinstance(val, (list, tuple)):
                if len(val) == 0:
                    return None
                if len(val) == 1:
                    val = val[0]
                else:
                    # Possibly a ContentType natural key (app_label, model)
                    try:
                        from django.contrib.contenttypes.models import ContentType
                        if related_model is ContentType:
                            ct = ContentType.objects.get_by_natural_key(val[0], val[1])
                            return ct.pk
                    except Exception:
                        pass
                    # fall through and try other heuristics

            # numeric primary key (string of digits or actual int)
            try:
                return int(val)
            except Exception:
                pass

            # try to find instance by common unique fields
            common = ['username', 'code', 'slug', 'email', 'name']
            for field_name in common:
                try:
                    related_model._meta.get_field(field_name)
                except Exception:
                    continue
                inst = related_model.objects.filter(**{field_name: val}).first()
                if inst:
                    return inst.pk
            return None

        for model_label in ordered_models:
            objects = model_map.get(model_label, [])
            app_label, model_name = model_label.split(".")
            model = apps.get_model(app_label, model_name)
            if not model:
                print(f"  ⚠️  Model not found: {model_label}, skipping...")
                continue
            print(f"\nImporting {model_label}: {len(objects):,} records...")
            # Prepare objects for bulk_create
            to_create = []
            for i, obj in enumerate(objects, 1):
                fields = obj["fields"]
                # Set PK if present
                if "pk" in obj:
                    fields[model._meta.pk.name] = obj["pk"]

                # Extract many-to-many fields and queue them to apply after insert
                m2m_data = {}
                for m2m_field in model._meta.many_to_many:
                    fname = m2m_field.name
                    if fname in fields:
                        m2m_data[fname] = fields.pop(fname)

                # Resolve foreign keys to PKs and extract many-to-many fields
                from django.db import models

                # Resolve FK fields (non-m2m) to PKs when values are non-numeric/natural keys
                for field_obj in model._meta.fields:
                    fname = field_obj.name
                    if getattr(field_obj, 'remote_field', None) and not getattr(field_obj, 'many_to_many', False):
                        # Accept either the field name (e.g., 'company') or the attname (e.g., 'company_id')
                        attname = getattr(field_obj, 'attname', fname)
                        if fname in fields or attname in fields:
                            # Prefer explicit attname if present
                            if attname in fields:
                                val = fields.pop(attname)
                            else:
                                val = fields.pop(fname)

                            if val is None:
                                # leave as None (will rely on DB constraints)
                                fields[attname] = None
                                continue

                            # If the value is a list/tuple or non-numeric, attempt to resolve to PK
                            resolved = None
                            if isinstance(val, (int,)):
                                resolved = int(val)
                            else:
                                resolved = _resolve_fk_value(val, field_obj.remote_field.model)

                            if resolved is not None:
                                # Assign to the attname (e.g., company_id) so Django accepts integer PKs
                                fields[attname] = resolved
                            else:
                                # unresolved reference -> set None and log
                                print(f"    ⚠️  Could not resolve FK {fname}='{val}' for {model_label} record {i}; setting NULL")
                                fields[attname] = None

                # Truncate string fields to field.max_length to avoid DB errors
                truncated = 0
                for fname, fval in list(fields.items()):
                    if isinstance(fval, str):
                        try:
                            field_obj = model._meta.get_field(fname)
                        except Exception:
                            field_obj = None
                        if field_obj is not None and getattr(field_obj, 'max_length', None):
                            maxlen = field_obj.max_length
                            if maxlen and len(fval) > maxlen:
                                fields[fname] = fval[:maxlen]
                                truncated += 1

                if truncated:
                    print(f"    ⚠️  Truncated {truncated} field(s) on {model_label} record {i} to fit DB max_length")

                to_create.append(model(**fields))

                # record queued m2m relations for this object by PK (if any)
                if m2m_data:
                    pk_val = fields.get(model._meta.pk.name) if model._meta.pk.name in fields else obj.get('pk')
                    m2m_queues[model_label].append((pk_val, m2m_data))
                if len(to_create) >= BATCH_SIZE:
                    try:
                        with transaction.atomic():
                            model.objects.bulk_create(to_create, batch_size=BATCH_SIZE, ignore_conflicts=True)
                        print(f"    Imported {i}/{len(objects)} records...")
                    except Exception as e:
                        print(f"    ❌ Error importing batch ending at {i}: {e}")
                    to_create = []
            # Final batch
            if to_create:
                try:
                    with transaction.atomic():
                        model.objects.bulk_create(to_create, batch_size=BATCH_SIZE, ignore_conflicts=True)
                    print(f"    Imported {len(objects)}/{len(objects)} records (final batch).")
                except Exception as e:
                    print(f"    ❌ Error importing final batch: {e}")

            # Apply any many-to-many relations queued for this model
            if m2m_queues.get(model_label):
                print(f"    Applying many-to-many relations for {model_label} ({len(m2m_queues[model_label])} entries)...")
                for pk_val, m2m_fields in m2m_queues[model_label]:
                    try:
                        if pk_val is None:
                            continue
                        instance = model.objects.filter(pk=pk_val).first()
                        if not instance:
                            continue
                        for fname, vals in m2m_fields.items():
                            try:
                                # resolve m2m member identifiers to PKs when necessary
                                rel_field = getattr(model, fname).field if hasattr(getattr(model, fname), 'field') else None
                                related_model = None
                                try:
                                    related_model = model._meta.get_field(fname).remote_field.model
                                except Exception:
                                    related_model = None

                                resolved_vals = []
                                if isinstance(vals, list):
                                    for v in vals:
                                        if isinstance(v, int):
                                            resolved_vals.append(v)
                                            continue
                                        if related_model:
                                            rv = _resolve_fk_value(v, related_model)
                                            if rv is not None:
                                                resolved_vals.append(rv)
                                else:
                                    # single value
                                    if isinstance(vals, int):
                                        resolved_vals = [vals]
                                    elif related_model:
                                        rv = _resolve_fk_value(vals, related_model)
                                        if rv is not None:
                                            resolved_vals = [rv]

                                if resolved_vals:
                                    getattr(instance, fname).set(resolved_vals)
                                else:
                                    getattr(instance, fname).clear()
                            except Exception as e:
                                print(f"      ⚠️  Could not set m2m {fname} on {model_label} pk={pk_val}: {e}")
                    except Exception as e:
                        print(f"      ⚠️  Error applying m2m for pk={pk_val}: {e}")
        print("\n✅ Data imported successfully (batch mode)!")
        return True
    except Exception as e:
        print(f"\n❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
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
