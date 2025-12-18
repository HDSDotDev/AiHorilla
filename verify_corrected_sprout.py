#!/usr/bin/env python
"""Verify the corrected Sprout-matching calculation"""

monthly_basic = 57886
meal = 3000
annual_basic = monthly_basic * 12
annual_meal = meal * 12
annual_gross = annual_basic + annual_meal

# Fixed base deduction (13th month + de minimis)
fixed_base = 173508

# Normal monthly contributions
normal_contrib = 1125 + 1447.15 + 100
annual_normal_contrib = normal_contrib * 12

print("="*70)
print("CORRECTED SPROUT-MATCHING CALCULATION")
print("="*70)

print(f"\nAnnual Gross: ₱{annual_gross:,.2f}")
print(f"  Basic: ₱{annual_basic:,.2f}")
print(f"  Meal allowance: ₱{annual_meal:,.2f}")

# PERIOD 1: No contributions deducted
print(f"\n" + "="*70)
print("PERIOD 1 (No contributions deducted from paycheck)")
print("="*70)
taxable_p1 = annual_gross - fixed_base  # NO contribution deduction
base_tax = 50000
excess_p1 = taxable_p1 - 400000
annual_tax_p1 = base_tax + (excess_p1 * 0.20)
monthly_tax_p1 = annual_tax_p1 / 12
period_tax_p1 = monthly_tax_p1 * 0.5

print(f"Deductions from taxable income:")
print(f"  Fixed base (13th + de minimis): ₱{fixed_base:,.2f}")
print(f"  Government contributions: ₱0.00 (not deducted this period)")
print(f"  Total deductions: ₱{fixed_base:,.2f}")
print(f"\nTaxable annual: ₱{taxable_p1:,.2f}")
print(f"Annual tax: ₱{annual_tax_p1:,.2f}")
print(f"Monthly tax: ₱{monthly_tax_p1:,.2f}")
print(f"Period 1 tax (15 days): ₱{period_tax_p1:,.2f}")
print(f"\nSprout Period 1: ₱3,392.70")
print(f"Difference: ₱{abs(period_tax_p1 - 3392.70):.2f}")

# PERIOD 2: Contributions deducted
print(f"\n" + "="*70)
print("PERIOD 2 (Contributions deducted from paycheck)")
print("="*70)
taxable_p2 = annual_gross - fixed_base - annual_normal_contrib
excess_p2 = taxable_p2 - 400000
annual_tax_p2 = base_tax + (excess_p2 * 0.20)
monthly_tax_p2 = annual_tax_p2 / 12
period_tax_p2 = monthly_tax_p2 * 0.5

print(f"Deductions from taxable income:")
print(f"  Fixed base (13th + de minimis): ₱{fixed_base:,.2f}")
print(f"  Government contributions: ₱{annual_normal_contrib:,.2f}")
print(f"  Total deductions: ₱{fixed_base + annual_normal_contrib:,.2f}")
print(f"\nTaxable annual: ₱{taxable_p2:,.2f}")
print(f"Annual tax: ₱{annual_tax_p2:,.2f}")
print(f"Monthly tax: ₱{monthly_tax_p2:,.2f}")
print(f"Period 2 tax (15 days): ₱{period_tax_p2:,.2f}")
print(f"\nSprout Period 2: ₱2,713.27")
print(f"Difference: ₱{abs(period_tax_p2 - 2713.27):.2f}")

# Summary
print(f"\n" + "="*70)
print("SUMMARY")
print("="*70)
total_tax = period_tax_p1 + period_tax_p2
sprout_total = 3392.70 + 2713.27
print(f"Period 1: Horilla ₱{period_tax_p1:,.2f} vs Sprout ₱3,392.70 (diff: ₱{abs(period_tax_p1 - 3392.70):.2f})")
print(f"Period 2: Horilla ₱{period_tax_p2:,.2f} vs Sprout ₱2,713.27 (diff: ₱{abs(period_tax_p2 - 2713.27):.2f})")
print(f"Total: Horilla ₱{total_tax:,.2f} vs Sprout ₱{sprout_total:,.2f}")
print(f"\nBoth periods match: {abs(period_tax_p1 - 3392.70) < 1 and abs(period_tax_p2 - 2713.27) < 1}")
