# Database Sync Instructions: SQLite → PostgreSQL (Railway)

## Overview
This guide will help you sync your local SQLite database to Railway PostgreSQL, ensuring all data is transferred and migrations are handled properly.

## Prerequisites

1. **Railway PostgreSQL Database URL**
   - Get your DATABASE_URL from Railway dashboard
   - It should look like: `postgresql://user:password@host:port/database`

2. **Required Python Packages**
   ```bash
   pip install dj-database-url psycopg2-binary
   ```

## Quick Sync Process

### Method 1: Automatic Sync Script (Recommended)

1. Set your Railway DATABASE_URL:
   ```powershell
   $env:DATABASE_URL="your-railway-database-url-here"
   ```

2. Run the sync script:
   ```powershell
   python sync_databases.py
   ```

3. Follow the prompts to complete the sync.

### Method 2: Manual Sync

#### Step 1: Export SQLite Data
```powershell
python manage.py dumpdata --natural-foreign --natural-primary --exclude=contenttypes --exclude=auth.permission --indent=2 > sqlite_data.json
```

#### Step 2: Configure PostgreSQL Connection
Create a `.env` file in the horilla directory:
```env
DATABASE_URL=your-railway-postgresql-url
```

#### Step 3: Run Migrations on PostgreSQL
```powershell
python manage.py migrate --database=default
```

#### Step 4: Import Data
```powershell
python manage.py loaddata sqlite_data.json
```

## Troubleshooting

### Migration Conflicts
If you encounter migration conflicts:

```powershell
# Reset migrations on PostgreSQL
python manage.py migrate --fake-initial

# Or reset specific app
python manage.py migrate app_name --fake
```

### Circular Dependencies
If you see circular dependency errors:

1. Check `CIRCULAR_DEPENDENCY_FIX.md` for known fixes
2. Run migrations in specific order:
   ```powershell
   python manage.py migrate contenttypes
   python manage.py migrate auth
   python manage.py migrate base
   python manage.py migrate employee
   # ... continue with other apps
   ```

### Data Import Errors
If loaddata fails:

1. Try importing in smaller batches:
   ```powershell
   python manage.py dumpdata app_name > app_data.json
   python manage.py loaddata app_data.json
   ```

2. Use the direct sync method (included in sync_databases.py)

## Verification

After sync, verify data integrity:

```powershell
# Check table counts
python -c "
from django.apps import apps
from django.conf import settings
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horilla.settings')
import django
django.setup()

for model in apps.get_models():
    count = model.objects.count()
    print(f'{model._meta.app_label}.{model._meta.model_name}: {count}')
"
```

## Important Notes

⚠️ **WARNING**: This process will **DELETE ALL EXISTING DATA** in the PostgreSQL database!

✅ **Best Practices**:
- Always backup your PostgreSQL database before syncing
- Test the sync process in a development environment first
- Verify data integrity after sync
- Keep the sqlite_data.json file as backup

## Common Issues

### Issue: "Database connection failed"
**Solution**: Verify DATABASE_URL is correct and PostgreSQL is accessible

### Issue: "Migration already exists"
**Solution**: Use `--fake` flag or reset migration state

### Issue: "Integrity constraint violation"
**Solution**: Ensure migrations are run before loading data

## Support Files

- `sync_databases.py` - Automated sync script
- `fix_migration_state.py` - Fix migration conflicts
- `CIRCULAR_DEPENDENCY_FIX.md` - Known circular dependency fixes
