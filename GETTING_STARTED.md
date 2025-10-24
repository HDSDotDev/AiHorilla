# 🚀 Quick Start for New Developers

## Getting Started (Fresh GitHub Clone)

### Step 1: Install Dependencies

```bash
cd horilla
pip install -r requirements.txt
```

**Windows PowerShell:**
```powershell
cd horilla
python -m pip install -r requirements.txt
```

### Step 2: Run One-Command Setup

```bash
python first_time_setup.py
```

This automated script does EVERYTHING:
- ✅ Applies all database migrations
- ✅ Creates Philippines payroll models
- ✅ Populates SSS, PhilHealth, Pag-IBIG data
- ✅ Sets up tax brackets, regions, holidays
- ✅ Configures country-specific deductions
- ✅ Activates Philippines payroll
- ✅ Sets Philippine Peso (₱) currency

**Time: 2-3 minutes**

### Step 3: Create Admin Account

```bash
python manage.py createsuperuser
```

Enter username, email, password when prompted.

### Step 4: Start Server

```bash
python manage.py runserver
```

Server starts at: **http://127.0.0.1:8000/**

### Step 5: Login & Use

- **Application:** http://127.0.0.1:8000/
- **Django Admin:** http://127.0.0.1:8000/admin/

---

## ✅ You're Done!

Your Philippines payroll system is now fully configured with:
- 52 SSS contribution brackets
- PhilHealth & Pag-IBIG rates
- 6 BIR tax brackets (TRAIN Law 2018)
- 17 Philippine regions with minimum wage
- 7 overtime calculation rules
- 16 Philippine holidays (2025)
- Country-filtered deductions (USA deductions won't appear on PH payslips!)

---

## Troubleshooting

### Error: `ModuleNotFoundError: No module named 'X'`

```bash
pip install -r requirements.txt --force-reinstall
```

### Error: Database/migration errors

```bash
# Reset database (WARNING: Deletes all data)
rm TestDB_Horilla.sqlite3  # or del on Windows
python first_time_setup.py
```

### Error: Setup script fails

Run steps manually:
```bash
python manage.py migrate
python manage.py populate_ph_payroll
python manage.py update_deduction_countries
```

### Windows: Execution policy error

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## Documentation

| Document | Purpose |
|----------|---------|
| `SETUP_README.md` | Complete setup guide with all options |
| `PHILIPPINES_PAYROLL_GUIDE.md` | Philippines features explained |
| `COUNTRY_DEDUCTIONS_GUIDE.md` | How country filtering works |
| `SOLUTION_SUMMARY.md` | Technical implementation details |

---

## What's New?

### 🇵🇭 Philippines Payroll Features

**Statutory Deductions (Auto-calculated):**
- SSS Contribution (salary-based brackets)
- PhilHealth Premium (4% of basic pay)
- Pag-IBIG Contribution (1-2% of salary)
- BIR Withholding Tax (TRAIN Law)

**Regional Support:**
- 17 Philippine regions configured
- Minimum wage per region

**Overtime & Differentials:**
- Regular OT: 125%
- Rest day OT: 130%
- Holiday OT: 130-200%
- Night differential: 110%

**Other Features:**
- 13th month pay tracking
- COLA (Cost of Living Allowance)
- 16 Philippine holidays (2025)

### 🌍 Country-Specific Deductions

**The Key Innovation:**
- USA deductions (Provident Fund, Professional Tax, ESI) **only apply when USA is active**
- Philippines deductions (SSS, PhilHealth, Pag-IBIG) **only apply when Philippines is active**
- Global deductions apply to all countries

**No more confusion!** Philippines employees won't see USA deductions on their payslips.

---

## Need Help?

1. Check **SETUP_README.md** for detailed instructions
2. Review **PHILIPPINES_PAYROLL_GUIDE.md** for feature details
3. See **COUNTRY_DEDUCTIONS_GUIDE.md** for deduction configuration

---

**Happy payroll processing! 🇵🇭**
