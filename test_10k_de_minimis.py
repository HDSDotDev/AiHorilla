#!/usr/bin/env python
"""Test with meal as TAXABLE but with ₱10,000/year de minimis deduction"""

monthly_basic = 57886
meal = 3000  # TAXABLE (part of gross)
annual_gross = (monthly_basic + meal) * 12

# De minimis benefits deduction: ₱10,000/year (BIR limit)
de_minimis_deduction = 10000

# 13th month exemption
thirteenth_month = 57886  # Under ₱90,000 limit
total_fixed_deductions = thirteenth_month + de_minimis_deduction

# Normal monthly contributions
normal_contrib = 1125 + 1447.15 + 100
annual_normal_contrib = normal_contrib * 12

print("="*70)
print("TEST: MEAL TAXABLE + ₱10,000 DE MINIMIS DEDUCTION")
print("="*70)

print(f"\nAnnual Gross (Basic + Meal): ₱{annual_gross:,.2f}")
print(f"\nFixed Deductions:")
print(f"  13th month exemption: ₱{thirteenth_month:,.2f}")
print(f"  De minimis benefits: ₱{de_minimis_deduction:,.2f}")
print(f"  Total: ₱{total_fixed_deductions:,.2f}")

# PERIOD 1
print(f"\n" + "="*70)
print("PERIOD 1")
print("="*70)
taxable_p1 = annual_gross - total_fixed_deductions
tax_p1 = 50000 + (taxable_p1 - 400000) * 0.20
monthly_tax_p1 = tax_p1 / 12
period_tax_p1 = monthly_tax_p1 * 0.5

print(f"Taxable: ₱{taxable_p1:,.2f}")
print(f"Annual tax: ₱{tax_p1:,.2f}")
print(f"Period tax: ₱{period_tax_p1:,.2f}")
print(f"Expected: ₱3,392.70")
print(f"Match: {abs(period_tax_p1 - 3392.70) < 1} {'✓' if abs(period_tax_p1 - 3392.70) < 1 else '✗'}")

# PERIOD 2
print(f"\n" + "="*70)
print("PERIOD 2")
print("="*70)
taxable_p2 = annual_gross - total_fixed_deductions - annual_normal_contrib
tax_p2 = 50000 + (taxable_p2 - 400000) * 0.20
monthly_tax_p2 = tax_p2 / 12
period_tax_p2 = monthly_tax_p2 * 0.5

print(f"Taxable: ₱{taxable_p2:,.2f}")
print(f"Annual tax: ₱{tax_p2:,.2f}")
print(f"Period tax: ₱{period_tax_p2:,.2f}")
print(f"Expected: ₱2,713.27")
print(f"Match: {abs(period_tax_p2 - 2713.27) < 1} {'✓' if abs(period_tax_p2 - 2713.27) < 1 else '✗'}")

print(f"\n" + "="*70)
print(f"RESULT: {abs(period_tax_p1 - 3392.70) < 1 and abs(period_tax_p2 - 2713.27) < 1}")
print("="*70)

# What deduction amount would work?
print(f"\n" + "="*70)
print("REVERSE ENGINEERING THE CORRECT DEDUCTION")
print("="*70)

# We know Period 1 should give ₱3,392.70
target_period_1 = 3392.70
target_monthly = target_period_1 * 2
target_annual = target_monthly * 12
# tax = 50000 + (taxable - 400000) * 0.20
# target_annual = 50000 + (taxable - 400000) * 0.20
# taxable = ((target_annual - 50000) / 0.20) + 400000
target_taxable = ((target_annual - 50000) / 0.20) + 400000
required_deduction = annual_gross - target_taxable

print(f"Target Period 1 tax: ₱{target_period_1:,.2f}")
print(f"Target annual tax: ₱{target_annual:,.2f}")
print(f"Required taxable: ₱{target_taxable:,.2f}")
print(f"Annual gross: ₱{annual_gross:,.2f}")
print(f"Required total deduction: ₱{required_deduction:,.2f}")
print(f"\nBreakdown guess:")
print(f"  13th month: ₱{thirteenth_month:,.2f}")
print(f"  Remaining (de minimis?): ₱{required_deduction - thirteenth_month:,.2f}")
print(f"  Per month: ₱{(required_deduction - thirteenth_month) / 12:,.2f}")
