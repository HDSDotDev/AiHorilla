"""
Quick test - does the tax calculation work?
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horilla.settings')
django.setup()

from datetime import date
from decimal import Decimal
from employee.models import Employee
from payroll.methods.philippines_payroll import philippines_payroll_calculation

# Test with Joseph Sy
joseph = Employee.objects.get(id=3)

# Oct 14 - Oct 28, 2024 (Cutoff 2 - FULL contributions)
start_date = date(2024, 10, 14)
end_date = date(2024, 10, 28)

print("=" * 80)
print("TESTING JOSEPH SY PAYROLL - CUTOFF 2")
print(f"Period: {start_date} to {end_date}")
print("=" * 80)
print()

# Run with ALL enabled (Cutoff 2 scenario - full contributions)
result = philippines_payroll_calculation(
    employee=joseph,
    start_date=start_date,
    end_date=end_date,
    apply_sss=True,         # Cutoff 2 has SSS
    apply_philhealth=True,  # Cutoff 2 has PhilHealth
    apply_pagibig=True,     # Cutoff 2 has Pag-IBIG
    apply_tax=True,         # AND TAX
    apply_allowances=True
)

print(f"Basic Pay: P{result['basic_pay']:,.2f}")
print(f"Gross Pay: P{result['gross_pay']:,.2f}")
print()

print("DEBUG - Available keys in result:")
print(list(result.keys()))
print()

# Check all deduction categories
all_deductions = []
all_deductions.extend(result.get('pretax_deductions', []))
all_deductions.extend(result.get('tax_deductions', []))
all_deductions.extend(result.get('post_tax_deductions', []))

print("ALL DEDUCTIONS:")
for d in all_deductions:
    print(f"  {d['title']}: P{d['amount']:,.2f}")
    if 'tax' in d['title'].lower() or 'bir' in d['title'].lower():
        print(f"    → {d.get('description', 'N/A')}")
print()

print(f"Net Pay: P{result['net_pay']:,.2f}")
print()

# Find tax
tax_amount = 0
for d in (result.get('pretax_deductions', []) + result.get('tax_deductions', []) + result.get('post_tax_deductions', [])):
    if 'tax' in d['title'].lower() or 'bir' in d['title'].lower():
        tax_amount = d['amount']
        break

print("=" * 80)
print(f"TAX CALCULATED: P{tax_amount:,.2f}")
print(f"EXPECTED (Sprout Cutoff 2): P2,713.27")
print(f"DIFFERENCE: P{abs(tax_amount - 2713.27):,.2f}")
print("=" * 80)
