# Railway Deployment Checklist

This file documents a minimal, repeatable deployment process for Horilla on Railway.

Steps

1. Link repository in Railway and create a new service.

2. Add a PostgreSQL plugin / resource in Railway and copy the `DATABASE_URL`.

3. In Railway service settings, add the following environment variables:
   - `DATABASE_URL` (from the PostgreSQL resource)
   - `RAILWAY_PUBLIC_DOMAIN` (optional; set by Railway automatically)

4. Deploy.

5. The container `entrypoint.sh` will run initialization scripts and **apply migrations**.
   - The entrypoint blocks until `python manage.py migrate --noinput` succeeds.
   - If migrations fail, check container logs and run migrations manually in Railway shell:

```bash
# In Railway web shell or via CLI
cd /app/horilla
python manage.py migrate --noinput
```

6. If a migration cannot be applied because of missing tables due to inconsistent state,
   run the emergency helper (last-resort) and then re-run migrate:

```bash
python fix_database_tables.py
python manage.py migrate --noinput
```

7. After migrations succeed, visit the app URL. If you need demo data, use the web UI `Load Demo Data`.

Notes
- Always create a DB backup before performing destructive actions (dropping tables, deleting migration records).
- The CI workflow will block PRs that introduce model changes without migrations.
# Railway Deployment Guide for Horilla HR System

This guide will help you deploy the Horilla HR system to Railway.app successfully.

## Prerequisites

1. A Railway account (sign up at https://railway.app)
2. This Horilla application with all files committed to a Git repository (GitHub, GitLab, or Bitbucket)

## Quick Deployment Steps

### 1. Create a New Railway Project

1. Log in to Railway.app
2. Click "New Project"
3. Select "Deploy from GitHub repo" (or your git provider)
4. Select your Horilla repository
5. Railway will auto-detect the Dockerfile

### 2. Add PostgreSQL Database (Recommended)

1. In your Railway project, click "New"
2. Select "Database" → "Add PostgreSQL"
3. Railway will automatically create a `DATABASE_URL` environment variable

**Alternative**: Railway also supports MySQL if you prefer that over PostgreSQL.

### 3. Configure Environment Variables

In Railway, go to your service → Variables, and add:

#### Required Variables:
```
SECRET_KEY=your-very-long-random-secret-key-here-change-this
DJANGO_SETTINGS_MODULE=horilla.settings
ALLOWED_HOSTS=*.railway.app,yourapp.railway.app
DEBUG=False
PORT=8000
```

#### Optional but Recommended:
```
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@yourcompany.com
DJANGO_SUPERUSER_PASSWORD=SecurePassword123!
```

#### Database Configuration (if not using Railway PostgreSQL):
```
DB_ENGINE=django.db.backends.postgresql
DB_NAME=horilla_db
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=your_db_host
DB_PORT=5432
```

**Important**: If you added PostgreSQL through Railway, it automatically sets `DATABASE_URL` which is all you need!

### 4. Generate a Secure SECRET_KEY

Run this Python command locally to generate a secure key:
```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Or use:
```bash
openssl rand -base64 50
```

### 5. Deploy

1. Push your code to your Git repository
2. Railway will automatically build and deploy
3. Monitor the deployment logs for any errors

### 6. Access Your Application

Once deployed, Railway will provide a URL like: `https://yourapp.railway.app`

**Default Admin Credentials** (if auto-created):
- Username: `admin`
- Password: `admin`

**⚠️ IMPORTANT**: Change the admin password immediately after first login!

## Troubleshooting

### Migration Errors

If you see migration errors in the logs:

1. **Check Database Connection**: Ensure `DATABASE_URL` is set correctly
2. **Manual Migration**: Use Railway's terminal feature:
   ```bash
   python manage.py migrate --noinput
   ```

### "No such table" Errors

The entrypoint script handles this, but if issues persist:
```bash
python manage.py migrate --run-syncdb --noinput
```

### Static Files Not Loading

Ensure `ALLOWED_HOSTS` includes your Railway domain:
```
ALLOWED_HOSTS=*.railway.app,yourapp-production.railway.app
```

### Application Keeps Restarting

Check logs for specific errors:
1. Go to Railway project → Your service → Deployments
2. Click on the latest deployment
3. View logs for detailed error messages

Common causes:
- Missing environment variables
- Database connection issues
- Migration failures

## Environment Variable Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | Yes | - | Django secret key for security |
| `DEBUG` | No | False | Set to False in production |
| `ALLOWED_HOSTS` | Yes | - | Comma-separated list of allowed hosts |
| `DATABASE_URL` | Yes* | - | Auto-set by Railway PostgreSQL |
| `PORT` | No | 8000 | Port for the application (Railway sets this) |
| `DB_ENGINE` | No | sqlite3 | Database engine if not using DATABASE_URL |
| `DB_NAME` | No | - | Database name |
| `DB_USER` | No | - | Database username |
| `DB_PASSWORD` | No | - | Database password |
| `DB_HOST` | No | - | Database host |
| `DB_PORT` | No | - | Database port |

*Required if not using Railway's PostgreSQL service

## Post-Deployment Setup

### 1. Change Admin Password
```bash
# Using Railway's terminal
python manage.py changepassword admin
```

### 2. Create Additional Users
Access the admin panel at: `https://yourapp.railway.app/admin`

### 3. Configure Application Settings
- Set up departments
- Add employees
- Configure payroll settings
- Set up leave policies

## Scaling Recommendations

For production use:

1. **Database**: Use Railway's PostgreSQL (included)
2. **Workers**: Start with 2 workers (already configured in entrypoint.sh)
3. **Memory**: Monitor and adjust as needed (Railway auto-scales)
4. **Backups**: Set up regular database backups through Railway

## Security Checklist

- [ ] Change `SECRET_KEY` from default
- [ ] Set `DEBUG=False`
- [ ] Update `ALLOWED_HOSTS` with your actual domain
- [ ] Change default admin password
- [ ] Enable HTTPS (Railway provides this automatically)
- [ ] Set up regular database backups
- [ ] Review and restrict API access if needed

## Support

- Railway Documentation: https://docs.railway.app
- Horilla Issues: https://github.com/horilla-opensource/horilla/issues

## Cost Estimation

Railway offers:
- Free tier: $5/month credit (perfect for testing)
- Pro Plan: Pay-as-you-go starting at $5/month
- PostgreSQL: Included in project costs

Expected monthly cost for small-medium company: $10-20/month

## Monitoring

Monitor your application through:
1. Railway Dashboard → Your Service → Metrics
2. View logs in real-time: Dashboard → Deployments → Logs
3. Set up alerts for downtime or errors

---

**Last Updated**: November 2025
**Tested with**: Railway.app, Python 3.11, Django 4.2
