#!/usr/bin/env python
"""Find what Sprout is actually doing with contributions"""

monthly_basic = 57886
meal = 3000
monthly_gross = monthly_basic + meal

# Period contributions (what's deducted from paycheck each period)
period_sss = 1750 / 2  # Half per period
period_philhealth = 1447.15 / 2
period_pagibig = 200 / 2
period_contrib = period_sss + period_philhealth + period_pagibig

print("="*70)
print("ANALYZING SPROUT'S LOGIC")
print("="*70)

print(f"\nMonthly gross: ₱{monthly_gross:,.2f}")
print(f"Period gross (15 days): ₱{monthly_gross / 2:,.2f}")

print(f"\nPeriod contributions:")
print(f"  SSS: ₱{period_sss:,.2f}")
print(f"  PhilHealth: ₱{period_philhealth / 2:,.2f}")  
print(f"  Pag-IBIG: ₱{period_pagibig:,.2f}")
print(f"  Total per period: ₱{period_contrib:,.2f}")

# Known facts from Sprout
period_1_tax = 3392.70
period_2_tax = 2713.27
tax_difference = period_1_tax - period_2_tax

print(f"\n" + "="*70)
print("KNOWN SPROUT VALUES")
print("="*70)
print(f"Period 1 tax: ₱{period_1_tax:,.2f}")
print(f"Period 2 tax: ₱{period_2_tax:,.2f}")
print(f"Tax difference: ₱{tax_difference:,.2f}")
print(f"Period 2 contributions: ₱{period_contrib:,.2f}")
print(f"Ratio: {tax_difference / period_contrib:.6f}")

# Theory: Sprout annualizes ONLY the amount deducted in that specific period
print(f"\n" + "="*70)
print("THEORY: Annualize only period-specific contributions")
print("="*70)

fixed_base = 173508
annual_gross = monthly_gross * 12

# Period 1: No contributions
taxable_p1 = annual_gross - fixed_base
tax_p1 = 50000 + (taxable_p1 - 400000) * 0.20
monthly_tax_p1 = tax_p1 / 12
period_tax_p1 = monthly_tax_p1 / 2

print(f"\nPeriod 1 (no contributions):")
print(f"  Annual taxable: ₱{taxable_p1:,.2f}")
print(f"  Annual tax: ₱{tax_p1:,.2f}")
print(f"  Monthly tax: ₱{monthly_tax_p1:,.2f}")
print(f"  Period tax: ₱{period_tax_p1:,.2f}")
print(f"  Expected: ₱{period_1_tax:,.2f}")
print(f"  Match: {abs(period_tax_p1 - period_1_tax) < 1}")

# Period 2: Annualize ONLY this period's contribution
annual_period_contrib = period_contrib * 24  # 24 periods per year
taxable_p2 = annual_gross - fixed_base - annual_period_contrib
tax_p2 = 50000 + (taxable_p2 - 400000) * 0.20
monthly_tax_p2 = tax_p2 / 12
period_tax_p2 = monthly_tax_p2 / 2

print(f"\nPeriod 2 (with ₱{period_contrib:,.2f} contribution):")
print(f"  Annualized contribution: ₱{annual_period_contrib:,.2f}")
print(f"  Annual taxable: ₱{taxable_p2:,.2f}")
print(f"  Annual tax: ₱{tax_p2:,.2f}")
print(f"  Monthly tax: ₱{monthly_tax_p2:,.2f}")
print(f"  Period tax: ₱{period_tax_p2:,.2f}")
print(f"  Expected: ₱{period_2_tax:,.2f}")
print(f"  Match: {abs(period_tax_p2 - period_2_tax) < 1}")

print(f"\n" + "="*70)
print("VERIFICATION")
print("="*70)
print(f"Period 1: ₱{period_tax_p1:,.2f} {'✓' if abs(period_tax_p1 - period_1_tax) < 1 else '✗'}")
print(f"Period 2: ₱{period_tax_p2:,.2f} {'✓' if abs(period_tax_p2 - period_2_tax) < 1 else '✗'}")
print(f"Total: ₱{period_tax_p1 + period_tax_p2:,.2f}")
print(f"Expected: ₱{period_1_tax + period_2_tax:,.2f}")
