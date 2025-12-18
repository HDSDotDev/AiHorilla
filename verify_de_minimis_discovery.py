#!/usr/bin/env python
"""Verify tax calculation with meal allowance as NON-TAXABLE (de minimis)"""

monthly_basic = 57886
meal = 3000  # This should be NON-TAXABLE (de minimis)
rice = 2000  # Already non-taxable
laundry = 500  # Already non-taxable

# CORRECTED: Only basic salary is taxable
annual_taxable_gross = monthly_basic * 12  # NOT including meal!
annual_meal = meal * 12  # De minimis, not added to taxable

# Fixed base deduction (13th month exemption)
# 13th month: ₱57,886 (under ₱90,000 limit, fully exempt)
thirteenth_month_exempt = 57886
fixed_base = thirteenth_month_exempt * 12 / 12  # Annualized

# Normal monthly contributions
normal_sss = 1125
normal_philhealth = 1447.15
normal_pagibig = 100
normal_contrib = normal_sss + normal_philhealth + normal_pagibig
annual_normal_contrib = normal_contrib * 12

print("="*70)
print("CORRECTED: MEAL ALLOWANCE IS NON-TAXABLE (DE MINIMIS)")
print("="*70)

print(f"\nMonthly Compensation:")
print(f"  Basic salary: ₱{monthly_basic:,.2f} (TAXABLE)")
print(f"  Meal allowance: ₱{meal:,.2f} (DE MINIMIS - NON-TAXABLE)")
print(f"  Rice allowance: ₱{rice:,.2f} (DE MINIMIS - NON-TAXABLE)")
print(f"  Laundry allowance: ₱{laundry:,.2f} (DE MINIMIS - NON-TAXABLE)")
print(f"  Total pay: ₱{monthly_basic + meal + rice + laundry:,.2f}")

print(f"\nAnnual Taxable Income:")
print(f"  Basic salary only: ₱{annual_taxable_gross:,.2f}")
print(f"  (Meal ₱{annual_meal:,.2f} excluded as de minimis)")

# PERIOD 1: No contributions deducted
print(f"\n" + "="*70)
print("PERIOD 1 (No contributions deducted from paycheck)")
print("="*70)
taxable_p1 = annual_taxable_gross - fixed_base  # NO contributions
base_tax = 50000
excess_p1 = taxable_p1 - 400000
annual_tax_p1 = base_tax + (excess_p1 * 0.20)
monthly_tax_p1 = annual_tax_p1 / 12
period_tax_p1 = monthly_tax_p1 * 0.5

print(f"Annual gross (taxable): ₱{annual_taxable_gross:,.2f}")
print(f"Less 13th month exemption: ₱{fixed_base:,.2f}")
print(f"Less contributions: ₱0.00 (not deducted)")
print(f"Taxable income: ₱{taxable_p1:,.2f}")
print(f"\nTax calculation:")
print(f"  Base (₱250K-400K): ₱50,000")
print(f"  Plus 20% of ₱{excess_p1:,.2f}: ₱{excess_p1 * 0.20:,.2f}")
print(f"  Annual tax: ₱{annual_tax_p1:,.2f}")
print(f"  Monthly tax: ₱{monthly_tax_p1:,.2f}")
print(f"  Period 1 (15 days): ₱{period_tax_p1:,.2f}")
print(f"\n  Sprout Period 1: ₱3,392.70")
print(f"  Difference: ₱{abs(period_tax_p1 - 3392.70):.2f}")
print(f"  MATCH: {abs(period_tax_p1 - 3392.70) < 1} {'✓' if abs(period_tax_p1 - 3392.70) < 1 else '✗'}")

# PERIOD 2: Contributions deducted
print(f"\n" + "="*70)
print("PERIOD 2 (Contributions deducted from paycheck)")
print("="*70)
taxable_p2 = annual_taxable_gross - fixed_base - annual_normal_contrib
excess_p2 = taxable_p2 - 400000
annual_tax_p2 = base_tax + (excess_p2 * 0.20)
monthly_tax_p2 = annual_tax_p2 / 12
period_tax_p2 = monthly_tax_p2 * 0.5

print(f"Annual gross (taxable): ₱{annual_taxable_gross:,.2f}")
print(f"Less 13th month exemption: ₱{fixed_base:,.2f}")
print(f"Less contributions: ₱{annual_normal_contrib:,.2f}")
print(f"Taxable income: ₱{taxable_p2:,.2f}")
print(f"\nTax calculation:")
print(f"  Base (₱250K-400K): ₱50,000")
print(f"  Plus 20% of ₱{excess_p2:,.2f}: ₱{excess_p2 * 0.20:,.2f}")
print(f"  Annual tax: ₱{annual_tax_p2:,.2f}")
print(f"  Monthly tax: ₱{monthly_tax_p2:,.2f}")
print(f"  Period 2 (15 days): ₱{period_tax_p2:,.2f}")
print(f"\n  Sprout Period 2: ₱2,713.27")
print(f"  Difference: ₱{abs(period_tax_p2 - 2713.27):.2f}")
print(f"  MATCH: {abs(period_tax_p2 - 2713.27) < 1} {'✓' if abs(period_tax_p2 - 2713.27) < 1 else '✗'}")

# Summary
print(f"\n" + "="*70)
print("FINAL VERIFICATION")
print("="*70)
total_tax = period_tax_p1 + period_tax_p2
sprout_total = 3392.70 + 2713.27
print(f"Period 1: Horilla ₱{period_tax_p1:,.2f} vs Sprout ₱3,392.70 {'✓' if abs(period_tax_p1 - 3392.70) < 1 else '✗'}")
print(f"Period 2: Horilla ₱{period_tax_p2:,.2f} vs Sprout ₱2,713.27 {'✓' if abs(period_tax_p2 - 2713.27) < 1 else '✗'}")
print(f"Monthly Total: ₱{total_tax:,.2f} vs Sprout ₱{sprout_total:,.2f}")
print(f"\n{'='*70}")
print(f"BOTH PERIODS MATCH: {abs(period_tax_p1 - 3392.70) < 1 and abs(period_tax_p2 - 2713.27) < 1}")
print(f"{'='*70}")

if abs(period_tax_p1 - 3392.70) < 1 and abs(period_tax_p2 - 2713.27) < 1:
    print("\n🎉 SUCCESS! The mystery is solved:")
    print("   - Meal allowance is DE MINIMIS (non-taxable)")
    print("   - Only basic salary ₱57,886 is taxable")
    print("   - 13th month (₱57,886) is fully exempt")
    print("   - Contributions reduce taxable income in Period 2")
