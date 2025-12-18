#!/usr/bin/env python
"""Test if Sprout calculates tax on period income directly (non-annualized)"""

# 15-day period values
period_basic = 28943
period_meal = 1500
period_gross = period_basic + period_meal

# Period 2 contributions
period_sss = 875
period_philhealth = 723.575  # Monthly 1447.15 / 2
period_pagibig = 100
period_contrib_total = period_sss + period_philhealth + period_pagibig

print("="*70)
print("TESTING NON-ANNUALIZED (DIRECT PERIOD) CALCULATION")
print("="*70)

print(f"\n15-Day Period Values:")
print(f"  Basic pay: ₱{period_basic:,.2f}")
print(f"  Meal allowance: ₱{period_meal:,.2f}")
print(f"  Gross: ₱{period_gross:,.2f}")

print(f"\nPeriod 2 Contributions:")
print(f"  SSS: ₱{period_sss:,.2f}")
print(f"  PhilHealth: ₱{period_philhealth:,.2f}")
print(f"  Pag-IBIG: ₱{period_pagibig:,.2f}")
print(f"  Total: ₱{period_contrib_total:,.2f}")

# Try different base deduction amounts for 15 days
monthly_fixed_base = 173508 / 12
period_fixed_base = monthly_fixed_base / 2

print(f"\n15-Day Fixed Base Deduction: ₱{period_fixed_base:,.2f}")

# Period 1: No contributions
period_1_taxable = period_gross - period_fixed_base
print(f"\n" + "="*70)
print(f"PERIOD 1 (Direct calculation on 15-day income)")
print("="*70)
print(f"  Gross: ₱{period_gross:,.2f}")
print(f"  Less fixed base: ₱{period_fixed_base:,.2f}")
print(f"  Taxable: ₱{period_1_taxable:,.2f}")

# BIR tax brackets (semi-monthly equivalent)
# Annual 250,001-400,000: 20,833 + 20% of excess over 250,000
# Monthly 20,834-33,333: 1,736 + 20% 
# Semi-monthly 10,417-16,667: 868 + 20%

if period_1_taxable > 16667:
    # Over 20% bracket
    period_1_tax = 2500 + ((period_1_taxable - 16667) * 0.25)
    bracket = "25%"
elif period_1_taxable > 10417:
    # In 20% bracket
    period_1_tax = 868 + ((period_1_taxable - 10417) * 0.20)
    bracket = "20%"
else:
    period_1_tax = 0
    bracket = "0%"

print(f"  Tax bracket: {bracket}")
print(f"  Period 1 tax: ₱{period_1_tax:,.2f}")
print(f"  Expected: ₱3,392.70")
print(f"  Match: {abs(period_1_tax - 3392.70) < 1}")

# Period 2: With contributions
period_2_taxable = period_gross - period_fixed_base - period_contrib_total
print(f"\n" + "="*70)
print(f"PERIOD 2 (Direct calculation with contributions)")
print("="*70)
print(f"  Gross: ₱{period_gross:,.2f}")
print(f"  Less fixed base: ₱{period_fixed_base:,.2f}")
print(f"  Less contributions: ₱{period_contrib_total:,.2f}")
print(f"  Taxable: ₱{period_2_taxable:,.2f}")

if period_2_taxable > 16667:
    period_2_tax = 2500 + ((period_2_taxable - 16667) * 0.25)
    bracket = "25%"
elif period_2_taxable > 10417:
    period_2_tax = 868 + ((period_2_taxable - 10417) * 0.20)
    bracket = "20%"
else:
    period_2_tax = 0
    bracket = "0%"

print(f"  Tax bracket: {bracket}")
print(f"  Period 2 tax: ₱{period_2_tax:,.2f}")
print(f"  Expected: ₱2,713.27")
print(f"  Match: {abs(period_2_tax - 2713.27) < 1}")

print(f"\n" + "="*70)
print("SUMMARY")
print("="*70)
print(f"Period 1: ₱{period_1_tax:,.2f} vs ₱3,392.70 {'✓' if abs(period_1_tax - 3392.70) < 1 else '✗'}")
print(f"Period 2: ₱{period_2_tax:,.2f} vs ₱2,713.27 {'✓' if abs(period_2_tax - 2713.27) < 1 else '✗'}")
print(f"Total: ₱{period_1_tax + period_2_tax:,.2f} vs ₱6,105.97")
