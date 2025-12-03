# Horilla Deployment & Troubleshooting Guide

**Last Updated:** December 3, 2025  
**Status:** Production-Tested on Railway with PostgreSQL

---

## Table of Contents
1. [Quick Start (Fresh Deployment)](#quick-start-fresh-deployment)
2. [Critical Architecture Understanding](#critical-architecture-understanding)
3. [Common Issues & Solutions](#common-issues--solutions)
4. [Demo Data Loader Deep Dive](#demo-data-loader-deep-dive)
5. [Migration Management](#migration-management)
6. [Performance Optimization](#performance-optimization)

---

## Quick Start (Fresh Deployment)

### Prerequisites
- Python 3.10+
- PostgreSQL database
- Django 4.2.21

### Standard Deployment (Empty Database)
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure database in horilla/settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'your_db_name',
        'USER': 'your_db_user',
        'PASSWORD': 'your_db_password',
        'HOST': 'your_db_host',
        'PORT': '5432',
    }
}

# 3. Apply migrations
python manage.py migrate

# 4. Start server
python manage.py runserver
```

### First Login
1. Navigate to `http://localhost:8000/login/`
2. You'll see **"Initialize Database"** and **"Load Demo Data"** buttons
3. Choose one:
   - **Initialize Database**: Create your own admin + company
   - **Load Demo Data**: Get pre-populated sample data

---

## Critical Architecture Understanding

### The Employee-User Relationship

**CRITICAL:** Every Django `User` that logs in **MUST** have an `Employee` record.

```python
# Django User Model (auth_user table)
User
  ├─ username
  ├─ password
  ├─ is_superuser
  └─ is_new_employee (custom field)

# Employee Model (employee_employee table)
Employee
  ├─ employee_user_id (OneToOne → User, related_name="employee_get")
  ├─ employee_first_name
  ├─ email (UNIQUE)
  ├─ phone
  └─ is_active

# EmployeeWorkInformation (employee_employeeworkinformation table)
EmployeeWorkInformation
  ├─ employee_id (OneToOne → Employee, related_name="employee_work_info")
  ├─ company_id (ForeignKey → Company) ⚠️ REQUIRED by CompanyMiddleware
  ├─ department_id
  └─ job_position_id
```

### Why This Matters

**Login Flow:**
```
1. User enters username/password
2. Django authenticates → User object
3. base/views.py line 680: employee = getattr(user, "employee_get", None)
4. If employee is None → ERROR: "An employee related to this user's credentials does not exist"
5. CompanyMiddleware checks: user.employee_get.employee_work_info.company_id
6. If missing → Logout + redirect to login
```

**Key Insight:** You cannot have a User without Employee + EmployeeWorkInformation in this system.

---

## Common Issues & Solutions

### Issue 1: "An employee related to this user's credentials does not exist"

**Symptoms:**
- User can authenticate (password correct)
- Gets error message on login
- Redirected back to login page

**Root Cause:**
- `User` exists in `auth_user` table
- `Employee` record missing or not linked via `employee_user_id`

**Solution:**
```python
# Check in Django shell
python manage.py shell

from django.contrib.auth.models import User
user = User.objects.get(username='admin')
print(hasattr(user, 'employee_get'))  # Should be True

# If False, create Employee:
from employee.models import Employee, EmployeeWorkInformation
from base.models import Company

employee = Employee.objects.create(
    employee_user_id=user,
    employee_first_name='Admin',
    employee_last_name='User',
    email='admin@example.com',
    phone='000-000-0000',
    badge_id='ADMIN001',
    is_active=True
)

# Create work info (REQUIRED)
company = Company.objects.first()  # Or create one
EmployeeWorkInformation.objects.create(
    employee_id=employee,
    company_id=company
)
```

### Issue 2: Login Success but Immediate Logout

**Symptoms:**
- Login succeeds briefly
- Immediately redirected back to login
- Message: "An employee related to this user's credentials does not exist"

**Root Cause:**
- `Employee` exists
- `EmployeeWorkInformation` missing or has no `company_id`
- `CompanyMiddleware` (base/middleware.py line 66) catches exception and logs out

**Solution:**
```python
from employee.models import Employee, EmployeeWorkInformation
from base.models import Company

employee = Employee.objects.get(email='admin@example.com')
company = Company.objects.first()

# Check if work info exists
if not hasattr(employee, 'employee_work_info'):
    EmployeeWorkInformation.objects.create(
        employee_id=employee,
        company_id=company
    )
else:
    # Update company_id if missing
    work_info = employee.employee_work_info
    work_info.company_id = company
    work_info.save()
```

### Issue 3: Initialize Database Buttons Still Showing After Demo Load

**Symptoms:**
- Clicked "Load Demo Data"
- Success message appears
- Login page still shows initialization buttons

**Root Cause:**
- Demo data loaded but admin User has no Employee record
- `initialize_database_condition()` checks: `hasattr(user, "employee_get")`
- Returns True → buttons still visible

**Solution:**
This was fixed in commit `fix: Create Employee record for admin user in demo data loader`.  
If you're using an older version, update `load_demo_sql.py` to include admin employee creation.

### Issue 4: Migration Conflicts

**Symptoms:**
```
django.db.utils.ProgrammingError: relation "table_name" already exists
```

**Root Cause:**
- Database has tables from previous deployment
- Migrations trying to create tables that exist

**Solution:**
```bash
# Option A: Fake the migrations (if tables match schema)
python manage.py migrate --fake

# Option B: Nuclear option (DESTROYS ALL DATA)
python manage.py flush
python manage.py migrate

# Option C: Check migration state
python manage.py showmigrations
```

---

## Demo Data Loader Deep Dive

### What `load_demo_sql.py` Creates

**Order of Operations:**
1. **Admin User** (`auth_user` table)
   - Username: `admin`
   - Password: `admin` (PBKDF2-SHA256 hash)
   - is_superuser: `true`

2. **Company** (`base_company` table)
   - Name: "BizBloqs Philippines"
   - Address: Manila, Philippines

3. **Admin Employee** (`employee_employee` table) ⚠️ CRITICAL
   - Linked to admin User via `employee_user_id_id`
   - Email: `admin@example.com`
   - Phone: `000-000-0000`

4. **Admin Work Info** (`employee_employeeworkinformation` table) ⚠️ CRITICAL
   - Linked to admin Employee via `employee_id_id`
   - Linked to Company via `company_id_id`

5. **Department** (`base_department` table)
   - Name: "Engineering"

6. **Job Position** (`base_jobposition` table)
   - Title: "Software Engineer"

7. **Sample Employees** (10 demo employees)
   - Username: firstname.lastname
   - Password: `Demo@2025`
   - Each has Employee + EmployeeWorkInformation

### Why Raw SQL Instead of ORM?

**Problem with ORM:**
```python
# This would trigger signals, middleware, and validation
employee = Employee.objects.create(...)
# Employee.save() has custom logic that may fail during setup
```

**Raw SQL Benefits:**
- ✅ Bypasses Django signals
- ✅ Bypasses middleware
- ✅ Bypasses model validation
- ✅ Faster bulk inserts
- ✅ Idempotent with `ON CONFLICT`

**Trade-off:**
- ❌ Must manually handle all relationships
- ❌ Must know exact table names and column names
- ❌ Must create ALL required records (Employee + EmployeeWorkInformation)

### Critical SQL Details

**ForeignKey Column Naming:**
```python
# Python model field
employee_user_id = models.OneToOneField(User, ...)

# Database column name (adds _id suffix)
employee_user_id_id  ⚠️ NOTE THE DOUBLE _id
```

**ON CONFLICT Strategy:**
```sql
-- For admin employee (allow re-linking to different user)
ON CONFLICT (email) DO UPDATE SET employee_user_id_id = EXCLUDED.employee_user_id_id

-- For company (idempotent, don't duplicate)
ON CONFLICT DO NOTHING
```

---

## Migration Management

### Current Migration Structure

```
base/migrations/
  ├─ 0001_initial.py          # Base models
  ├─ 0002_initial.py          # Cross-app relationships
  └─ 0003_add_is_new_employee_to_user.py  # Custom field patch

employee/migrations/
  ├─ 0001_initial.py          # Employee models
  ├─ 0002_add_philippines_payroll_fields.py  # Philippines payroll
  └─ 0003_remove_employee_employee_ph_region_idx.py  # Index cleanup
```

### Why Multiple "0001_initial" Migrations?

**Django Circular Dependency Handling:**
- `base` models depend on `employee` models
- `employee` models depend on `base` models
- Django splits into 0001 (models) + 0002 (relationships)

**Both are correct and expected.**

### Should You Squash Migrations?

**NO** - if you've already deployed to production.

**Why:**
- Production database has migrations applied
- `django_migrations` table tracks: `base.0001_initial`, `base.0002_initial`, etc.
- Squashing creates NEW migration files
- Django won't recognize them as equivalent
- You'll get conflicts

**When to Squash:**
- ✅ Starting completely fresh project
- ✅ No production databases exist yet
- ✅ Want cleaner history for new developers

**For Existing Deployments:**
- ✅ Keep current migrations
- ✅ New features add 0004, 0005, etc.
- ✅ Django skips already-applied migrations automatically

### Adding New Migrations

```bash
# 1. Make model changes in models.py
# 2. Generate migration
python manage.py makemigrations

# 3. Review generated file
# base/migrations/0004_your_new_feature.py

# 4. Apply to database
python manage.py migrate

# 5. Commit migration file to git
git add base/migrations/0004_your_new_feature.py
git commit -m "feat: Add new feature migration"
```

---

## Performance Optimization

### Railway-Specific Issues

**Symptoms:**
- Slow page loads (3-5+ seconds)
- Slow database queries
- Long deployment times (14-24 minutes)

**Causes:**
1. **Free/Hobby Tier Limitations**
   - CPU throttling
   - Memory constraints (512MB-1GB)
   - Shared database instance

2. **Network Latency**
   - App container → PostgreSQL network hop
   - External API calls

3. **Cold Starts**
   - Container hibernation on free tier
   - First request after idle is slow

### Quick Fixes

**1. Add Database Indexes**
```python
# In models.py
class Employee(models.Model):
    email = models.EmailField(unique=True, db_index=True)
    employee_user_id = models.OneToOneField(User, db_index=True)
```

**2. Enable Connection Pooling**
```python
# horilla/settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'CONN_MAX_AGE': 600,  # Reuse connections for 10 minutes
    }
}
```

**3. Add Caching**
```python
# horilla/settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'cache_table',
    }
}

# Run once
python manage.py createcachetable
```

**4. Optimize Middleware Order**
```python
# horilla/settings.py - Order matters!
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Serve static files fast
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.cache.UpdateCacheMiddleware',  # Cache responses
    # ... other middleware
    'django.middleware.cache.FetchFromCacheMiddleware',
]
```

### What Won't Help

- ❌ Squashing migrations (zero runtime impact)
- ❌ Optimizing demo data loader (runs once)
- ❌ Removing comments from code (Python compiles to bytecode)

### What Will Help

- ✅ Upgrade to Railway Pro ($5-20/month)
- ✅ Add Redis for caching
- ✅ Use `select_related()` and `prefetch_related()` in queries
- ✅ Add database indexes on foreign keys
- ✅ Enable query logging to find slow queries

---

## Debugging Checklist

### Login Issues
- [ ] User exists in `auth_user`?
- [ ] Password hash is correct format (PBKDF2)?
- [ ] User has `is_active=True`?
- [ ] Employee record exists with correct `employee_user_id_id`?
- [ ] EmployeeWorkInformation exists for employee?
- [ ] EmployeeWorkInformation has `company_id` set?
- [ ] Company exists and `is_active=True`?

### Database Issues
- [ ] All migrations applied? (`python manage.py showmigrations`)
- [ ] No pending migrations? (`python manage.py makemigrations --dry-run`)
- [ ] Database connection working? (`python manage.py dbshell`)
- [ ] Tables exist? (`\dt` in psql)

### Demo Data Issues
- [ ] Admin user created?
- [ ] Admin employee created?
- [ ] Admin work info created?
- [ ] Company created?
- [ ] All relationships correct?

---

## Emergency Recovery

### Reset Everything (Nuclear Option)

**⚠️ WARNING: DESTROYS ALL DATA**

```bash
# 1. Drop and recreate database
psql -U postgres
DROP DATABASE horilla_db;
CREATE DATABASE horilla_db;
\q

# 2. Reset migrations
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/*.pyc" -delete

# 3. Recreate migrations
python manage.py makemigrations

# 4. Apply migrations
python manage.py migrate

# 5. Load demo data
# Access /login/ and click "Load Demo Data"
```

### Partial Reset (Keep Data)

```bash
# 1. Backup database
pg_dump horilla_db > backup.sql

# 2. Try fixing migrations
python manage.py migrate --fake base zero
python manage.py migrate --fake employee zero
python manage.py migrate

# 3. If that fails, restore backup
psql horilla_db < backup.sql
```

---

## Production Deployment Checklist

- [ ] `DEBUG = False` in settings.py
- [ ] `ALLOWED_HOSTS` configured
- [ ] `SECRET_KEY` in environment variable (not hardcoded)
- [ ] Database credentials in environment variables
- [ ] Static files collected (`python manage.py collectstatic`)
- [ ] Migrations applied (`python manage.py migrate`)
- [ ] Superuser created or demo data loaded
- [ ] HTTPS enforced (`SECURE_SSL_REDIRECT = True`)
- [ ] Database backups configured
- [ ] Error logging configured (Sentry, etc.)
- [ ] Performance monitoring enabled

---

## Support & Resources

**Repository:** [HDSDotDev/AiHorilla](https://github.com/HDSDotDev/AiHorilla)  
**Branch:** Fork  
**Django Version:** 4.2.21  
**Python Version:** 3.10+  

**Key Files to Understand:**
- `base/views.py` - Login logic, initialize database
- `base/middleware.py` - CompanyMiddleware (requires employee_work_info)
- `load_demo_sql.py` - Demo data creation
- `employee/models.py` - Employee, EmployeeWorkInformation models

**Common Commands:**
```bash
# Django shell for debugging
python manage.py shell

# Check migrations
python manage.py showmigrations

# Create superuser manually
python manage.py createsuperuser

# Database shell
python manage.py dbshell

# Run development server
python manage.py runserver
```

---

**Last Updated:** December 3, 2025  
**Tested On:** Railway + PostgreSQL  
**Status:** ✅ Production-Ready
