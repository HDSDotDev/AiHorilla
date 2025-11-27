# Payroll Calculation Error Handling - Testing Guide

## Changes Made

All calls to `payroll_calculation()` now properly handle `ValidationError` exceptions that are raised when:
- Philippines payroll module is missing/broken
- Employee is missing required PH data (TIN, SSS, PhilHealth, Pag-IBIG)
- Payroll system configuration is invalid

## Files Updated

### 1. `payroll/views/component_views.py`
- Added imports: `logging`, `ValidationError`
- Added logger instance
- Updated 3 view functions with try-catch blocks:
  - `generate_payslip()` - Bulk payslip generation
  - `update_payslip()` - Single payslip update
  - `view_individual_payslip()` - View individual payslip

### 2. `payroll/scheduler.py`
- Added imports: `logging`, `ValidationError`
- Added logger instance
- Updated `generate_payslip()` scheduled task with try-catch

## User Experience Changes

### Before (Dangerous Behavior)
```
Employee missing TIN → Silent fallback to USA calculations → Wrong taxes deducted
PH module broken → Silent fallback to USA calculations → Legal compliance violation
```

### After (Safe Behavior)
```
Employee missing TIN → Red error message: "Failed to generate payslip for Juan Dela Cruz: TIN is required"
PH module broken → Red error message: "Philippines payroll system is active but calculation module is not installed"
```

## Error Messages

### User-Facing Messages (in UI)
1. **Validation Error**: 
   - "Failed to generate payslip for [Employee Name]: [specific validation error]"
   - Examples:
     - "TIN (Tax Identification Number) is required"
     - "No active SSS contribution tables configured"

2. **System Error**:
   - "Unexpected error generating payslip. Please contact support."

### Log Messages (for admins)
1. **INFO**: "Using Philippines payroll calculation for employee 123"
2. **WARNING**: "Employee 123 missing PH data: TIN is required"
3. **ERROR**: "Payslip calculation failed for employee 123: ..."
4. **CRITICAL**: "Philippines payroll module not found! System is configured for PH but module is missing"

## Testing Scenarios

### Test 1: Missing Employee Data
```python
# Create employee without TIN
from employee.models import Employee
emp = Employee.objects.create(
    employee_first_name="Test",
    employee_last_name="Employee"
    # No TIN, SSS, PhilHealth, Pag-IBIG
)

# Try to generate payslip
# Expected: Red error message about missing TIN
```

### Test 2: Bulk Generation with Mixed Data
```python
# Generate payslips for 10 employees
# 5 have complete PH data, 5 are missing TIN
# Expected:
# - 5 payslips generated successfully
# - 5 error messages displayed (one per employee)
# - Bulk operation continues, doesn't crash
```

### Test 3: Scheduled Payroll Generation
```python
# Run scheduled task with employee missing data
# Expected:
# - Error logged to payroll.log
# - Other employees still get payslips
# - No crash, scheduler continues
```

### Test 4: Philippines Module Missing (Extreme Case)
```python
# Temporarily rename philippines_payroll.py
# Try to generate payslip for PH employee
# Expected:
# - Critical error: "Philippines payroll system is active but calculation module is not installed"
# - No payslip created
# - No fallback to USA calculations
```

## Monitoring & Logs

### Where to Check Logs
```powershell
# Django application logs
type logs\horilla.log | Select-String "payroll"

# Or if using Python logging to console
python manage.py runserver 2>&1 | Select-String "payroll"
```

### Key Log Patterns to Monitor
```
ERROR - Payslip calculation failed for employee
CRITICAL - Philippines payroll module not found
WARNING - Employee missing PH data
```

## Admin Actions

### If You See Validation Errors

1. **"TIN is required"**
   - Go to Employee → Edit Employee → Add TIN number

2. **"No active SSS contribution tables"**
   - Go to Payroll → Philippines Config → SSS Tables → Add/Activate

3. **"Philippines payroll module is not installed"**
   - Check `payroll/methods/philippines_payroll.py` exists
   - Run: `python manage.py validate_payroll_system`

### Preventive Checks
```powershell
# Before monthly payroll run
python manage.py validate_payroll_system

# Check employee data completeness
python manage.py shell
>>> from payroll.validators import validate_ph_employee_data
>>> from employee.models import Employee
>>> for emp in Employee.objects.all():
...     try:
...         validate_ph_employee_data(emp)
...     except ValidationError as e:
...         print(f"{emp.get_full_name()}: {e}")
```

## Rollback Plan (If Issues Arise)

If the new error handling causes problems:

1. **Quick Fix**: Wrap validation calls in try-catch
```python
try:
    from payroll.validators import validate_ph_employee_data
    validate_ph_employee_data(employee)
except ImportError:
    pass  # Validators module not found, skip validation
except ValidationError:
    pass  # Continue anyway (old behavior)
```

2. **Full Rollback**: Revert these files:
   - `payroll/views/component_views.py`
   - `payroll/scheduler.py`

## Support Contacts

If you encounter issues after deployment:
1. Check logs first: `logs/horilla.log`
2. Run validation: `python manage.py validate_payroll_system`
3. Check employee data completeness
4. If critical: Temporarily disable validation (see Rollback Plan)

---

**Last Updated**: November 1, 2025
**Applied By**: AI Agent - Critical Security Fix
**Ticket**: PH Payroll Silent Fallback Bug
