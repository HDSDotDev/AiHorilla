"""
Test Joseph Sy's Cutoff 2 payroll (Oct 14-28, 2025)
Expected to match Sprout's values:
- FULL contributions (not divided by 2)
- Tax: ₱2,713.27
"""
import os
import sys
import django
from datetime import date
from decimal import Decimal

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horilla.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from employee.models import Employee
from payroll.models.models import WorkRecord
from payroll.methods.philippines_payroll import philippines_payroll_calculation

print("=" * 80)
print("TESTING JOSEPH SY PAYROLL - CUTOFF 2")
print("Period: 2024-10-14 to 2024-10-28")
print("=" * 80)
print()

# Get Joseph Sy (Employee ID 3)
joseph = Employee.objects.get(id=3)

# Cutoff 2 period
start_date = date(2024, 10, 14)
end_date = date(2024, 10, 28)

# Run payroll with ALL enabled (Sprout uses full contributions in Cutoff 2)
result = philippines_payroll_calculation(
    employee=joseph,
    start_date=start_date,
    end_date=end_date,
    apply_sss=True,
    apply_philhealth=True,
    apply_pagibig=True,
    apply_tax=True,
    apply_allowances=True
)

print(f"Basic Pay: P{result['basic_pay']:,.2f}")
print(f"Gross Pay: P{result['gross_pay']:,.2f}")
print()

# Check all deductions
print("DEBUG - Available keys in result:")
print(result.keys())
print()

print("ALL DEDUCTIONS:")
for category in ['pretax_deductions', 'tax_deductions', 'post_tax_deductions']:
    if category in result:
        for ded in result[category]:
            print(f"  {ded['title']}: P{ded['amount']:,.2f}")
            if ded.get('description'):
                print(f"    → {ded['description']}")

print()
print(f"Net Pay: P{result['net_pay']:,.2f}")
print()

# Extract tax amount
tax_amount = 0.0
for ded in result.get('tax_deductions', []):
    if 'tax' in ded['title'].lower() or 'bir' in ded['title'].lower():
        tax_amount = ded['amount']

print("=" * 80)
print(f"TAX CALCULATED: P{tax_amount:,.2f}")
print("EXPECTED (Sprout): P2,713.27")
print(f"DIFFERENCE: P{abs(tax_amount - 2713.27):,.2f}")
print()

# Check contributions
sss_amount = philhealth_amount = pagibig_amount = 0.0
for category in ['pretax_deductions', 'tax_deductions', 'post_tax_deductions']:
    if category in result:
        for ded in result[category]:
            if 'SSS' in ded['title']:
                sss_amount = ded['amount']
            elif 'PhilHealth' in ded['title']:
                philhealth_amount = ded['amount']
            elif 'Pag-IBIG' in ded['title']:
                pagibig_amount = ded['amount']

print("CONTRIBUTIONS CALCULATED:")
print(f"  SSS: P{sss_amount:,.2f} (Expected: P1,750.00 = P1,000 + P750 MPF)")
print(f"  PhilHealth: P{philhealth_amount:,.2f} (Expected: P1,447.15)")
print(f"  Pag-IBIG: P{pagibig_amount:,.2f} (Expected: P200.00)")
print("=" * 80)
