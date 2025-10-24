# Country-Specific Deductions System

## Overview

The Philippines payroll system now includes **country-specific deduction filtering**! This means:

- **USA deductions** (PF, Professional Tax, ESI) only apply when USA is active
- **Philippines deductions** (SSS, PhilHealth, Pag-IBIG) only apply when Philippines is active  
- **Global deductions** apply to all countries

## What Changed?

### 1. **New Country Field on Deductions**

Every deduction now has a `country` field with three options:
- **United States** - Only applies when USA is active
- **Philippines** - Only applies when Philippines is active
- **All Countries** - Applies regardless of active country

### 2. **Automatic Filtering**

The payroll calculation system automatically filters deductions based on the active country:

```python
# In payslip_calc.py
active_country = get_active_country()  # Gets 'USA' or 'PH' from PayrollCountryConfig

# All deduction queries now filter by country
Deduction.objects.filter(...).filter(country__in=[active_country, 'GLOBAL'])
```

### 3. **Migration & Setup**

**Step 1: Apply Migration**

```powershell
cd horilla
python manage.py migrate payroll
```

**Step 2: Update Existing Deductions**

```powershell
python manage.py update_deduction_countries
```

This command will:
- Mark Provident Fund, Professional Tax, ESI as **USA-specific**
- Leave other deductions as **All Countries** (GLOBAL)

## How to Use

### For Administrators

1. **Go to Payroll → Deductions**
2. **Edit each deduction**
3. **Set the Country field:**
   - **Provident Fund (PF)** → United States
   - **Professional Tax** → United States  
   - **ESI** → United States
   - **Federal Tax** → United States
   - Keep custom deductions as **All Countries**

4. **Create new payslips** - old deductions won't appear!

### For Developers

**Creating Country-Specific Deductions:**

```python
from payroll.models.models import Deduction

# USA deduction
usa_deduction = Deduction.objects.create(
    title="Federal Tax",
    country="USA",  # Only applies when USA is active
    is_tax=True,
    # ... other fields
)

# Philippines deduction (already handled by philippines_payroll.py)
# SSS, PhilHealth, Pag-IBIG are calculated automatically

# Global deduction (applies everywhere)
global_deduction = Deduction.objects.create(
    title="Company Uniform Fee",
    country="GLOBAL",  # Applies to all countries
    amount=500,
    # ... other fields
)
```

## Benefits

### ✅ Clean Separation
- Philippines payslips show **only** SSS, PhilHealth, Pag-IBIG, BIR tax
- USA payslips show **only** PF, Professional Tax, ESI, Federal Tax
- No more confusing foreign deductions!

### ✅ No Code Changes Needed
- Philippines payroll calculator still works unchanged
- Just set deduction countries in admin/database

### ✅ Flexible
- Add country-specific deductions anytime
- Create universal deductions that apply everywhere
- Easy to add new countries (just add to country_choice)

## Technical Details

### Files Modified

1. **`payroll/models/models.py`** (line ~1075)
   - Added `country` field to `Deduction` model
   - Choices: USA, PH, GLOBAL

2. **`payroll/methods/payslip_calc.py`**
   - Added `get_active_country()` helper function
   - Modified 3 deduction queries:
     - `calculate_tax_deduction()` (line ~459)
     - `calculate_pre_tax_deduction()` (line ~525)
     - `calculate_post_tax_deduction()` (line ~633)

3. **`payroll/migrations/0002_add_country_to_deduction.py`**
   - Migration to add country field

4. **`payroll/management/commands/update_deduction_countries.py`**
   - Management command to update existing deductions

### Database Schema

```sql
-- Before
CREATE TABLE payroll_deduction (
    id INTEGER PRIMARY KEY,
    title VARCHAR(255),
    -- ... other fields
);

-- After  
CREATE TABLE payroll_deduction (
    id INTEGER PRIMARY KEY,
    title VARCHAR(255),
    country VARCHAR(10) DEFAULT 'GLOBAL',  -- NEW!
    -- ... other fields
);
```

### Query Pattern

```python
# Old (applied ALL deductions regardless of country)
deductions = Deduction.objects.filter(
    include_active_employees=True,
    is_pretax=True
)

# New (filters by active country)
active_country = get_active_country()  # 'USA' or 'PH'
deductions = Deduction.objects.filter(
    include_active_employees=True,
    is_pretax=True
).filter(country__in=[active_country, 'GLOBAL'])
```

## Troubleshooting

### Issue: Old deductions still appearing

**Solution:**
1. Run migration: `python manage.py migrate payroll`
2. Update deductions: `python manage.py update_deduction_countries`
3. Go to **Payroll → Deductions** and verify country field
4. **Delete old payslips** and generate new ones

### Issue: Philippines deductions not showing

**Check:**
1. Is Philippines active? **Django Admin → Payroll → Payroll Country Configs**
2. Are SSS/PhilHealth/Pag-IBIG models populated? Run `python setup_philippines_payroll.py`
3. Are employee salaries within SSS brackets? (₱4,000 - ₱30,000)

### Issue: Migration fails

**Error: `duplicate column name`**

This means the migration was already applied. Run:

```powershell
python manage.py migrate payroll --fake 0002_add_country_to_deduction
```

## Next Steps

1. ✅ **Apply migration** → Add country field to Deduction model
2. ✅ **Run update command** → Mark USA deductions
3. ✅ **Test payslips** → Generate for Philippines employee
4. ✅ **Verify** → Only PH deductions appear

## Comparison: Before vs After

### Before (The Problem)
```
Philippines Payslip for John Doe
--------------------------------
Gross Pay:           ₱25,000.00

DEDUCTIONS:
- SSS Contribution:  ₱1,125.00  ✅ Correct (Philippines)
- PhilHealth:        ₱437.50    ✅ Correct (Philippines)  
- Pag-IBIG:          ₱100.00    ✅ Correct (Philippines)
- Withholding Tax:   ₱1,466.67  ✅ Correct (Philippines)
- Provident Fund:    ₱3,000.00  ❌ WRONG! (USA deduction)
- Professional Tax:  ₱500.00    ❌ WRONG! (USA deduction)
- ESI:               ₱187.50    ❌ WRONG! (USA deduction)
--------------------------------
Net Pay:             ₱18,183.33  ❌ INCORRECT
```

### After (The Solution)
```
Philippines Payslip for John Doe
--------------------------------
Gross Pay:           ₱25,000.00

DEDUCTIONS:
- SSS Contribution:  ₱1,125.00  ✅ Philippines
- PhilHealth:        ₱437.50    ✅ Philippines
- Pag-IBIG:          ₱100.00    ✅ Philippines
- Withholding Tax:   ₱1,466.67  ✅ Philippines
--------------------------------
Net Pay:             ₱21,870.83  ✅ CORRECT!
```

**Why USA deductions are gone:**
- Provident Fund has `country='USA'` → Filtered out when Philippines active
- Professional Tax has `country='USA'` → Filtered out when Philippines active
- ESI has `country='USA'` → Filtered out when Philippines active

## Summary

You were absolutely right! The Deductions tab is **configurable** and we should have used it from the start. 

The solution was to:
1. Add a `country` field to the Deduction model
2. Filter deductions by active country during payslip generation
3. Mark existing USA deductions (PF, PT, ESI) as USA-specific
4. Philippines calculations (SSS, PhilHealth, Pag-IBIG) already work via `philippines_payroll.py`

Now when you toggle countries:
- **Philippines active** → Only Philippines deductions apply
- **USA active** → Only USA deductions apply
- **Global deductions** → Always apply

**No more duplicate/foreign deductions on payslips!** ✨
