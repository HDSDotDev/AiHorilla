#!/usr/bin/env python
"""Test if all allowances treated as de minimis"""

# Annual calculations
annual_basic = 57886 * 12
meal_annual = 3000 * 12
rice_annual = 2000 * 12
laundry_annual = 500 * 12
total_allowances_annual = meal_annual + rice_annual + laundry_annual
annual_gross = annual_basic + meal_annual  # Only meal is in Sprout gross

print("="*70)
print("HYPOTHESIS: ALL ALLOWANCES ARE DE MINIMIS")
print("="*70)

print(f"\nAnnual Values:")
print(f"  Basic salary: ₱{annual_basic:,.2f}")
print(f"  Meal allowance: ₱{meal_annual:,.2f}")
print(f"  Rice allowance: ₱{rice_annual:,.2f}")
print(f"  Laundry allowance: ₱{laundry_annual:,.2f}")
print(f"  Total allowances: ₱{total_allowances_annual:,.2f}")
print(f"  Annual gross (basic + meal): ₱{annual_gross:,.2f}")

print(f"\nBIR de minimis limit: ₱90,000/year (₱7,500/month)")
print(f"Joseph's allowances: ₱{total_allowances_annual:,.2f}/year (₱{total_allowances_annual/12:,.2f}/month)")
print(f"Under limit: {total_allowances_annual < 90000} ✓")

# If all allowances are de minimis
de_minimis_deduction = total_allowances_annual
thirteenth = 57886
total_fixed = thirteenth + de_minimis_deduction

print(f"\n" + "="*70)
print("TAX CALCULATION - PERIOD 1")
print("="*70)
print(f"Annual gross: ₱{annual_gross:,.2f}")
print(f"Deductions:")
print(f"  13th month exemption: ₱{thirteenth:,.2f}")
print(f"  De minimis (all allowances): ₱{de_minimis_deduction:,.2f}")
print(f"  Total deductions: ₱{total_fixed:,.2f}")

taxable = annual_gross - total_fixed
tax = 50000 + (taxable - 400000) * 0.20
monthly_tax = tax / 12
period_tax = monthly_tax / 2

print(f"\nTaxable income: ₱{taxable:,.2f}")
print(f"Annual tax: ₱{tax:,.2f}")
print(f"Monthly tax: ₱{monthly_tax:,.2f}")
print(f"Period 1 tax (15 days): ₱{period_tax:,.2f}")
print(f"\nSprout Period 1: ₱3,392.70")
print(f"Difference: ₱{abs(period_tax - 3392.70):.2f}")
print(f"MATCH: {abs(period_tax - 3392.70) < 1} {'✓' if abs(period_tax - 3392.70) < 1 else '✗'}")

# Period 2 with contributions
print(f"\n" + "="*70)
print("TAX CALCULATION - PERIOD 2")
print("="*70)
normal_contrib = (1125 + 1447.15 + 100) * 12
taxable_p2 = annual_gross - total_fixed - normal_contrib
tax_p2 = 50000 + (taxable_p2 - 400000) * 0.20
monthly_tax_p2 = tax_p2 / 12
period_tax_p2 = monthly_tax_p2 / 2

print(f"Annual gross: ₱{annual_gross:,.2f}")
print(f"Deductions:")
print(f"  13th month + de minimis: ₱{total_fixed:,.2f}")
print(f"  Government contributions: ₱{normal_contrib:,.2f}")
print(f"  Total deductions: ₱{total_fixed + normal_contrib:,.2f}")

print(f"\nTaxable income: ₱{taxable_p2:,.2f}")
print(f"Annual tax: ₱{tax_p2:,.2f}")
print(f"Monthly tax: ₱{monthly_tax_p2:,.2f}")
print(f"Period 2 tax (15 days): ₱{period_tax_p2:,.2f}")
print(f"\nSprout Period 2: ₱2,713.27")
print(f"Difference: ₱{abs(period_tax_p2 - 2713.27):.2f}")
print(f"MATCH: {abs(period_tax_p2 - 2713.27) < 1} {'✓' if abs(period_tax_p2 - 2713.27) < 1 else '✗'}")

print(f"\n" + "="*70)
print("FINAL RESULT")
print("="*70)
both_match = abs(period_tax - 3392.70) < 1 and abs(period_tax_p2 - 2713.27) < 1
print(f"Period 1: ₱{period_tax:,.2f} vs ₱3,392.70 {'✓' if abs(period_tax - 3392.70) < 1 else '✗'}")
print(f"Period 2: ₱{period_tax_p2:,.2f} vs ₱2,713.27 {'✓' if abs(period_tax_p2 - 2713.27) < 1 else '✗'}")
print(f"Monthly Total: ₱{period_tax + period_tax_p2:,.2f} vs ₱6,105.97")
print(f"\nBOTH PERIODS MATCH: {both_match}")

if both_match:
    print("\n" + "="*70)
    print("🎉 SOLUTION FOUND!")
    print("="*70)
    print("Sprout configuration:")
    print("  • Meal allowance (₱3,000): TAXABLE (included in gross)")
    print("  • ALL allowances marked as DE MINIMIS:")
    print(f"    - Meal: ₱{meal_annual:,.2f}/year")
    print(f"    - Rice: ₱{rice_annual:,.2f}/year")
    print(f"    - Laundry: ₱{laundry_annual:,.2f}/year")
    print(f"    - Total: ₱{de_minimis_deduction:,.2f}/year")
    print("  • 13th month: Fully exempt (under ₱90K limit)")
    print("  • Government contributions: Deducted in Period 2 only")
