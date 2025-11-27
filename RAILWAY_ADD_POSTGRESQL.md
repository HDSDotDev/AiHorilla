# Railway Deployment - Add PostgreSQL Database

## ⚠️ CRITICAL: You MUST add a PostgreSQL database to Railway!

Your logs show the app is using SQLite, which **will NOT persist data** on Railway's ephemeral filesystem.

## Steps to Add PostgreSQL:

### 1. In Railway Dashboard:
1. Go to your project: https://railway.app/project/[your-project-id]
2. Click the **"+ New"** button
3. Select **"Database"**
4. Choose **"PostgreSQL"**
5. Railway will provision the database (~30 seconds)

### 2. Database Auto-Links:
Railway automatically:
- Creates the PostgreSQL instance
- Sets the `DATABASE_URL` environment variable
- Links it to all services in the same project

### 3. Verify Connection:
After adding PostgreSQL, check deployment logs for:
```
DATABASE_URL: SET (PostgreSQL)
✓ PostgreSQL detected - running full initialization
✓ Database connected: django.db.backends.postgresql
```

### 4. Redeploy (if needed):
If the app doesn't automatically redeploy after adding PostgreSQL:
1. Go to your app service
2. Click "Redeploy" or push a new commit

## What the App Will Do:

Once PostgreSQL is connected, the `railway_init_db` command will:
1. ✓ Run all database migrations
2. ✓ Create tables for all apps
3. ✓ Create admin user (username: admin, password: admin)
4. ✓ Load Philippines payroll data
5. ✓ Collect static files

## Expected Deployment Logs:

```
=== RAILWAY DATABASE INITIALIZATION ===
DATABASE_URL: SET (PostgreSQL)
✓ PostgreSQL detected - running full initialization
================================================================================
Railway Database Initialization
================================================================================
✓ Database connected: django.db.backends.postgresql

[1/4] Running database migrations...
Operations to perform:
  Apply all migrations: admin, asset, attendance, auth, contenttypes, employee, leave, payroll, sessions
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  ...
  Applying payroll.0001_initial... OK
✓ Migrations completed

[2/4] Creating admin user...
✓ Admin user created

[3/4] Setting up Philippines payroll data...
✓ Philippines payroll data loaded

[4/4] Collecting static files...
✓ Static files collected

================================================================================
✓✓✓ Railway initialization complete!
================================================================================

Default credentials:
  Username: admin
  Password: admin
  ⚠️  CHANGE PASSWORD IMMEDIATELY AFTER FIRST LOGIN!

=== INITIALIZATION COMPLETE ===
=== STARTING APPLICATION SERVER ===
```

## Current Issue:

Your logs show:
```
django.db.utils.OperationalError: no such table: employee_disciplinaryaction
```

And the traceback shows:
```
File "/usr/local/lib/python3.11/site-packages/django/db/backends/sqlite3/base.py"
```

**This confirms SQLite is being used instead of PostgreSQL.**

## Solution:

**Add PostgreSQL database in Railway dashboard NOW**, then the next deployment will:
- Use PostgreSQL instead of SQLite
- Create all tables properly
- Persist data across deployments
- Work correctly

## Alternative (NOT RECOMMENDED):

If you absolutely cannot use PostgreSQL, you could use Railway's persistent volume storage, but:
- Costs money
- Slower than PostgreSQL
- Not recommended for production
- Railway PostgreSQL is free for hobby tier

## After Adding PostgreSQL:

1. Wait for deployment to complete
2. Visit your app URL
3. Login with: admin / admin
4. **IMMEDIATELY change the password**
5. Start using the app!
