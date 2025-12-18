#!/usr/bin/env python
"""Reverse engineer Sprout's ₱3,392.70 tax calculation"""

period_basic = 28943.00
sprout_tax = 3392.70
monthly_basic = 57886.00

print("=" * 60)
print("REVERSE ENGINEERING SPROUT TAX: ₱3,392.70")
print("=" * 60)

# What monthly tax does this imply?
monthly_tax_implied = sprout_tax * 2  # 15 days → 30 days
annual_tax_implied = monthly_tax_implied * 12

print(f"\n15-day tax: ₱{sprout_tax:,.2f}")
print(f"Implied monthly tax: ₱{monthly_tax_implied:,.2f}")
print(f"Implied annual tax: ₱{annual_tax_implied:,.2f}")

# Work backwards from annual tax to find taxable income
# Using 20% bracket: Tax = 50,000 + (Taxable - 400,000) × 0.20
base_tax = 50000
tax_rate = 0.20
min_bracket = 400000

tax_on_excess = annual_tax_implied - base_tax
excess_income = tax_on_excess / tax_rate
taxable_annual = min_bracket + excess_income

print(f"\nWorking backwards:")
print(f"  Tax on excess: ₱{tax_on_excess:,.2f}")
print(f"  Excess over ₱400K: ₱{excess_income:,.2f}")
print(f"  Taxable annual income: ₱{taxable_annual:,.2f}")

# What contributions does this imply?
annual_basic = monthly_basic * 12
annual_contributions_implied = annual_basic - taxable_annual
monthly_contributions_implied = annual_contributions_implied / 12

print(f"\n  Annual basic: ₱{annual_basic:,.2f}")
print(f"  Implied annual contributions: ₱{annual_contributions_implied:,.2f}")
print(f"  Implied monthly contributions: ₱{monthly_contributions_implied:,.2f}")

# Compare with actual contributions
actual_monthly = 1125 + 1447.15 + 100
print(f"\n  Actual monthly contributions: ₱{actual_monthly:,.2f}")
print(f"  Difference: ₱{abs(monthly_contributions_implied - actual_monthly):,.2f}")

# Try with allowances
print(f"\n\n" + "=" * 60)
print("TESTING: What if ₱3,000 meal allowance is PARTIALLY taxed?")
print("=" * 60)

meal_allowance = 3000
de_minimis_monthly = 25000 / 12  # ₱2,083.33

print(f"\nMeal allowance: ₱{meal_allowance:,.2f}")
print(f"De minimis limit: ₱{de_minimis_monthly:,.2f}")

# Test different taxable portions
for taxable_portion in [0, 500, 916.67, 1000, 1500, 2000, 2500, 3000]:
    monthly_comp = monthly_basic + taxable_portion
    annual_comp = monthly_comp * 12
    annual_contributions = actual_monthly * 12
    taxable_annual_test = annual_comp - annual_contributions
    
    excess = taxable_annual_test - 400000
    annual_tax_test = 50000 + (excess * 0.20)
    monthly_tax_test = annual_tax_test / 12
    period_tax_test = monthly_tax_test * 0.5
    
    diff = abs(period_tax_test - sprout_tax)
    
    if diff < 100:  # Close match
        print(f"\n✓ Taxable meal portion: ₱{taxable_portion:,.2f}")
        print(f"  Monthly comp: ₱{monthly_comp:,.2f}")
        print(f"  Period tax: ₱{period_tax_test:,.2f}")
        print(f"  Difference from Sprout: ₱{diff:,.2f}")

print(f"\n\n" + "=" * 60)
print("CONCLUSION")
print("=" * 60)
print(f"None of the standard calculations match Sprout's ₱3,392.70")
print(f"This suggests Sprout may be using:")
print(f"  1. A different BIR interpretation")
print(f"  2. Year-to-date cumulative method")
print(f"  3. Custom tax table/formula")
print(f"  4. Different basis for annualization")
