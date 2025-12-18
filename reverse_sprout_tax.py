"""
Reverse engineer Sprout's tax calculation
Work backwards from ₱3,392.70 to find their taxable income
"""

from decimal import Decimal

sprout_tax = Decimal('3392.70')

print("=" * 80)
print("REVERSE ENGINEERING SPROUT'S TAX CALCULATION")
print("=" * 80)
print(f"\nSprout's Tax: ₱{sprout_tax:,.2f}")
print()

# The tax is in the ₱16,667 - ₱33,332 bracket (20% rate)
# Formula: ₱937.50 + (Taxable Income − ₱16,667) × 20%

# Solving for Taxable Income:
# 3,392.70 = 937.50 + (TI - 16,667) × 0.20
# 3,392.70 - 937.50 = (TI - 16,667) × 0.20
# 2,455.20 = (TI - 16,667) × 0.20
# 2,455.20 / 0.20 = TI - 16,667
# 12,276 = TI - 16,667
# TI = 12,276 + 16,667 = 28,943

base_tax = Decimal('937.50')
tax_above_base = sprout_tax - base_tax
rate = Decimal('0.20')

excess_over_bracket = tax_above_base / rate
bracket_min = Decimal('16667')
calculated_taxable_income = bracket_min + excess_over_bracket

print(f"Working backwards:")
print(f"  Tax above base: ₱{sprout_tax:,.2f} - ₱{base_tax:,.2f} = ₱{tax_above_base:,.2f}")
print(f"  Excess taxed at 20%: ₱{tax_above_base:,.2f} ÷ 0.20 = ₱{excess_over_bracket:,.2f}")
print(f"  Taxable Income: ₱{bracket_min:,.2f} + ₱{excess_over_bracket:,.2f} = ₱{calculated_taxable_income:,.2f}")
print()

# Now work backwards to find the Total Basic (before deductions)
print("=" * 80)
print("WHAT TOTAL BASIC WOULD GIVE THIS TAXABLE INCOME?")
print("=" * 80)
print()

# Standard contributions
sss = Decimal('1125.00')
philhealth = Decimal('1447.15')
pagibig = Decimal('100.00')
total_contribs = sss + philhealth + pagibig

print(f"Standard Contributions:")
print(f"  SSS: ₱{sss:,.2f}")
print(f"  PhilHealth: ₱{philhealth:,.2f}")
print(f"  Pag-IBIG: ₱{pagibig:,.2f}")
print(f"  Total: ₱{total_contribs:,.2f}")
print()

total_basic = calculated_taxable_income + total_contribs
print(f"Total Basic = Taxable Income + Contributions")
print(f"Total Basic = ₱{calculated_taxable_income:,.2f} + ₱{total_contribs:,.2f}")
print(f"Total Basic = ₱{total_basic:,.2f}")
print()

# Compare with what we calculated
halfmonth_basic = Decimal('28943.00')
meal_allowance = Decimal('1500.00')
our_total = halfmonth_basic + meal_allowance

print("=" * 80)
print("COMPARISON:")
print("=" * 80)
print(f"Total Basic needed for Sprout's tax: ₱{total_basic:,.2f}")
print(f"Our calculation:")
print(f"  Half-month basic: ₱{halfmonth_basic:,.2f}")
print(f"  Meal allowance: ₱{meal_allowance:,.2f}")
print(f"  Our total: ₱{our_total:,.2f}")
print()
print(f"Difference: ₱{total_basic - our_total:,.2f}")
print()

if total_basic > our_total:
    extra_needed = total_basic - our_total
    print(f"Sprout has ₱{extra_needed:,.2f} MORE in taxable income")
    print(f"This could be:")
    print(f"  - Additional allowances")
    print(f"  - Different contribution amounts")
    print(f"  - Different basic pay calculation")
elif total_basic < our_total:
    less_needed = our_total - total_basic
    print(f"Sprout has ₱{less_needed:,.2f} LESS in taxable income")
    print(f"This could be:")
    print(f"  - Higher contribution deductions")
    print(f"  - Some allowances not included")
else:
    print("✅ PERFECT MATCH!")

print()
print("=" * 80)

# Try different scenarios
print()
print("POSSIBLE SCENARIOS:")
print("=" * 80)
print()

# Scenario 1: Maybe different contributions
print("Scenario 1: What if PhilHealth is different?")
# If total basic is ₱31,115.15, and we have ₱30,443
# Difference is ₱672.15
# Current PhilHealth: ₱1,447.15
# New PhilHealth: ₱1,447.15 - ₱672.15 = ₱775.00
alt_philhealth = philhealth - (total_basic - our_total)
print(f"  PhilHealth would need to be: ₱{alt_philhealth:,.2f}")
print(f"  (vs current ₱{philhealth:,.2f})")
print()

# Scenario 2: Maybe additional allowances
print("Scenario 2: Additional taxable allowances?")
extra_allowance = total_basic - our_total
print(f"  Would need ₱{extra_allowance:,.2f} more in taxable allowances")
print(f"  Semi-monthly: ₱{extra_allowance:,.2f}")
print(f"  Monthly: ₱{extra_allowance * 2:,.2f}")
print()

# Verify the tax with the calculated taxable income
print("=" * 80)
print("VERIFICATION:")
print("=" * 80)
verify_tax = base_tax + ((calculated_taxable_income - bracket_min) * rate)
print(f"Tax with taxable income of ₱{calculated_taxable_income:,.2f}:")
print(f"  ₱937.50 + ((₱{calculated_taxable_income:,.2f} - ₱16,667) × 20%)")
print(f"  = ₱{verify_tax:,.2f}")
print(f"\nMatches Sprout? {verify_tax == sprout_tax}")
