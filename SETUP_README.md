# Horilla HRMS - Philippines Payroll Edition
## Quick Setup Guide

This guide will get you from a fresh clone to a running server in under 10 minutes.

## Prerequisites

- **Python 3.8+** (Tested on 3.12.10)
- **pip** (Python package installer)
- **Git** (for cloning)
- **Windows/Linux/Mac** (All supported)

## Step 1: Clone the Repository

```bash
git clone https://github.com/HDSDotDev/AiHorilla.git
cd AiHorilla/horilla
```

## Step 2: Create Virtual Environment

### Windows (PowerShell)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Linux/Mac
```bash
python3 -m venv venv
source venv/bin/activate
```

## Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

**Note:** If you get errors, try upgrading pip first:
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Step 4: Run Setup Script

This script will:
- Apply all database migrations
- Create Philippines payroll tables
- Populate SSS, PhilHealth, Pag-IBIG, Tax brackets
- Set up regions, overtime rules, holidays
- Configure country-specific deductions

### Windows
```powershell
python setup_philippines_payroll.py
```

### Linux/Mac
```bash
python3 setup_philippines_payroll.py
```

**Expected Output:**
```
✅ Applying database migrations...
✅ Creating Philippines payroll models...
✅ Populating SSS contribution tables...
✅ Populating PhilHealth rates...
✅ Populating Pag-IBIG rates...
✅ Populating BIR tax brackets...
✅ Setting up 17 Philippine regions...
✅ Configuring overtime rules...
✅ Adding 2025 holidays...
✅ Updating deduction countries...

🎉 SUCCESS! Philippines payroll system is ready!
```

## Step 5: Create Superuser (Admin Account)

```bash
python manage.py createsuperuser
```

Follow prompts to create your admin account:
- Username: (your choice)
- Email: (your email)
- Password: (secure password)

## Step 6: Run the Server

```bash
python manage.py runserver
```

**Server will start at:** http://127.0.0.1:8000/

## Step 7: Configure Country (First Time Only)

1. **Go to Django Admin:** http://127.0.0.1:8000/admin/
2. **Login** with superuser credentials
3. **Navigate to:** Payroll → Payroll Country Configs
4. **Click "Add Payroll Country Config"**
5. **Select:** Philippines (PH)
6. **Check:** Is Active
7. **Click:** Save

**Alternative:** USA is active by default. Toggle to Philippines when needed.

## Verification Checklist

After setup, verify everything works:

### ✅ Database Check
```bash
python manage.py migrate --check
```
**Expected:** No migrations pending

### ✅ Philippines Data Check
```bash
python manage.py shell
```
```python
from payroll.models.country_models import *
print(f"SSS Brackets: {PhilippinesSSSContribution.objects.count()}")
print(f"Tax Brackets: {PhilippinesTaxBracket.objects.count()}")
print(f"Regions: {PhilippinesRegion.objects.count()}")
exit()
```
**Expected Output:**
```
SSS Brackets: 52
Tax Brackets: 6
Regions: 17
```

### ✅ Deduction Country Check
```bash
python manage.py shell
```
```python
from payroll.models.models import Deduction
print(f"USA Deductions: {Deduction.objects.filter(country='USA').count()}")
print(f"PH Deductions: {Deduction.objects.filter(country='PH').count()}")
print(f"Global Deductions: {Deduction.objects.filter(country='GLOBAL').count()}")
exit()
```
**Expected:** USA=3, PH=0 (calculated dynamically), Global=30+

### ✅ Server Check
Navigate to: http://127.0.0.1:8000/
- Should see login page
- No errors in console

## Troubleshooting

### Problem: `ModuleNotFoundError: No module named 'X'`
**Solution:**
```bash
pip install -r requirements.txt --force-reinstall
```

### Problem: `django.db.utils.OperationalError: no such table`
**Solution:**
```bash
python manage.py migrate --run-syncdb
python setup_philippines_payroll.py
```

### Problem: `Execution policy` error (Windows PowerShell)
**Solution:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
Then retry: `.\venv\Scripts\Activate.ps1`

### Problem: Setup script fails partway through
**Solution:**
```bash
# Reset database (WARNING: Deletes all data!)
rm TestDB_Horilla.sqlite3
python manage.py migrate
python setup_philippines_payroll.py
```

### Problem: Old payslips still show wrong deductions
**Solution:**
1. Go to **Payroll → View Payslips**
2. **Delete all payslips** (they have cached data)
3. **Regenerate** payslips
4. New payslips will use country filtering

## Project Structure

```
horilla/
├── manage.py                    # Django management script
├── requirements.txt             # Python dependencies
├── setup_philippines_payroll.py # Philippines setup script
├── horilla/                     # Main Django project settings
│   └── settings.py
├── payroll/                     # Payroll app
│   ├── models/
│   │   ├── models.py           # Core payroll models
│   │   └── country_models.py   # Philippines models (NEW)
│   ├── methods/
│   │   ├── payslip_calc.py     # Payroll calculations (MODIFIED)
│   │   └── philippines_payroll.py  # PH calculator (NEW)
│   ├── views/
│   │   ├── component_views.py  # Payroll routing (MODIFIED)
│   │   └── philippines_views.py    # PH frontend views (NEW)
│   ├── migrations/
│   │   ├── 0003_payrollcountryconfig_*.py  # PH models
│   │   └── 0004_add_country_to_deduction.py  # Country field (NEW)
│   ├── management/
│   │   └── commands/
│   │       ├── populate_ph_payroll.py       # Data population (NEW)
│   │       └── update_deduction_countries.py # Deduction update (NEW)
│   └── admin.py                # Enhanced admin (MODIFIED)
├── templates/                   # HTML templates
└── static/                      # CSS, JS, images
```

## What's New in Philippines Edition?

### 🇵🇭 Philippines Payroll Features

1. **Statutory Deductions (Auto-calculated)**
   - SSS Contribution (52 salary brackets)
   - PhilHealth Premium (4% of basic pay)
   - Pag-IBIG Contribution (1-2% of salary)
   - BIR Withholding Tax (TRAIN Law 2018)

2. **Regional Minimum Wage**
   - 17 Philippine regions configured
   - NCR, CAR, Regions I-XIII, BARMM, NIR, MIMAROPA

3. **Overtime Rules**
   - Regular day OT (125%)
   - Rest day OT (130%)
   - Special holiday OT (130%)
   - Regular holiday OT (200%)
   - Night differential (110%)

4. **Holidays (2025)**
   - 16 Philippine holidays configured
   - Regular and special non-working days

5. **13th Month Pay**
   - Automatic calculation tracking

6. **Country-Specific Deductions**
   - USA deductions (PF, PT, ESI) only show when USA active
   - PH deductions (SSS, PhilHealth, Pag-IBIG) only show when PH active
   - Global deductions work for all countries

### 🔧 System Enhancements

1. **Country Toggle System**
   - Admin can switch between USA/Philippines
   - Sidebar menus change based on active country
   - Deductions filtered by country automatically

2. **Enhanced Admin Interface**
   - Deduction admin shows country column
   - Easy filtering by country
   - Organized fieldsets

3. **Frontend Views**
   - SSS contribution tables
   - PhilHealth rates
   - Pag-IBIG information
   - Tax bracket calculator
   - Holiday calendar
   - Region minimum wages

## Configuration Options

### Change Database

By default, uses SQLite (`TestDB_Horilla.sqlite3`). To use PostgreSQL/MySQL:

**Edit `horilla/settings.py`:**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'horilla_db',
        'USER': 'postgres',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### Change Country Default

To make Philippines the default country:

**Edit `payroll/models/country_models.py` (line ~25):**
```python
class PayrollCountryConfig(models.Model):
    country = models.CharField(
        max_length=20,
        choices=COUNTRY_CHOICES,
        default='PH',  # Changed from 'USA'
        unique=True
    )
```

### Customize Deductions

**Via Django Admin:**
1. http://127.0.0.1:8000/admin/payroll/deduction/
2. Add/Edit deductions
3. Set **Country** field (USA/PH/Global)

**Via Frontend:**
1. http://127.0.0.1:8000/payroll/view-deduction/
2. Create new deduction
3. Assign to country

## For Production Deployment

### Additional Steps Required:

1. **Change SECRET_KEY** in `settings.py`
2. **Set DEBUG = False** in `settings.py`
3. **Configure ALLOWED_HOSTS** in `settings.py`
4. **Use production database** (PostgreSQL recommended)
5. **Collect static files:** `python manage.py collectstatic`
6. **Use production server** (Gunicorn, uWSGI)
7. **Set up nginx/Apache** as reverse proxy
8. **Enable HTTPS** with SSL certificate
9. **Set up backups** for database
10. **Configure logging** and monitoring

**See Django deployment checklist:**
```bash
python manage.py check --deploy
```

## Support & Documentation

- **Main README:** `README.md`
- **Philippines Setup Guide:** `PHILIPPINES_QUICK_SETUP.md`
- **Country Deductions Guide:** `COUNTRY_DEDUCTIONS_GUIDE.md`
- **Solution Summary:** `SOLUTION_SUMMARY.md`
- **Original Horilla Docs:** https://github.com/horilla-opensource/horilla

## License

This project is licensed under the same license as Horilla HRMS.

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Submit pull request

---

**🎉 You're all set! Happy payroll processing!**
