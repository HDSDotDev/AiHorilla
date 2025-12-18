"""
Test Sprout-Style Cutoff Allocation
Validates the exact behavior: SSS/Pag-IBIG split, PhilHealth stateful
"""

from decimal import Decimal

print("=" * 80)
print("SPROUT CUTOFF ALLOCATION TEST")
print("=" * 80)
print()

# Joseph Sy's monthly contributions
monthly_sss = Decimal('1750.00')
monthly_philhealth = Decimal('1447.15')
monthly_pagibig = Decimal('100.00')

print("MONTHLY CONTRIBUTIONS:")
print(f"  SSS:        ₱{monthly_sss:,.2f}")
print(f"  PhilHealth: ₱{monthly_philhealth:,.2f}")
print(f"  Pag-IBIG:   ₱{monthly_pagibig:,.2f}")
print()

# Scenario: This is the 2nd cutoff, ₱359.43 PhilHealth already deducted
print("=" * 80)
print("CUTOFF 2 (Sept 29 - Oct 13) - Sprout Actual")
print("=" * 80)
print()

philhealth_already_deducted = Decimal('359.43')
print(f"PhilHealth already deducted in Cutoff 1: ₱{philhealth_already_deducted:,.2f}")
print()

# SSS: Split evenly
cutoff_sss = monthly_sss / 2
print(f"SSS (÷2):        ₱{cutoff_sss:,.2f}")

# Pag-IBIG: Split evenly
cutoff_pagibig = monthly_pagibig / 2
print(f"Pag-IBIG (÷2):   ₱{cutoff_pagibig:,.2f}")

# PhilHealth: Remainder allocation
philhealth_remaining = monthly_philhealth - philhealth_already_deducted
cutoff_philhealth = philhealth_remaining
print(f"PhilHealth (remainder): ₱{monthly_philhealth:,.2f} - ₱{philhealth_already_deducted:,.2f} = ₱{cutoff_philhealth:,.2f}")

total_cutoff_deductions = cutoff_sss + cutoff_pagibig + cutoff_philhealth
print()
print(f"TOTAL CUTOFF DEDUCTIONS: ₱{total_cutoff_deductions:,.2f}")
print()

# Now calculate tax
halfmonth_basic = Decimal('28943.00')
meal_allowance = Decimal('1500.00')
total_basic = halfmonth_basic + meal_allowance

print("=" * 80)
print("TAX CALCULATION")
print("=" * 80)
print()

print(f"Total Basic Pay: ₱{total_basic:,.2f}")
print(f"  Half-month salary: ₱{halfmonth_basic:,.2f}")
print(f"  Meal allowance:    ₱{meal_allowance:,.2f}")
print()

taxable_income = total_basic - total_cutoff_deductions
print(f"Taxable Income: ₱{total_basic:,.2f} - ₱{total_cutoff_deductions:,.2f} = ₱{taxable_income:,.2f}")
print()

# Apply tax bracket
bracket_min = Decimal('16667')
base_tax = Decimal('937.50')
rate = Decimal('0.20')

if taxable_income <= Decimal('10417'):
    tax = Decimal('0.00')
    bracket = "≤ ₱10,417 (0%)"
elif taxable_income <= Decimal('16666'):
    tax = (taxable_income - Decimal('10417')) * Decimal('0.15')
    bracket = "₱10,417 - ₱16,666 (15%)"
elif taxable_income <= Decimal('33332'):
    excess = taxable_income - bracket_min
    tax = base_tax + (excess * rate)
    bracket = "₱16,667 - ₱33,332 (20%)"
    print(f"Bracket: {bracket}")
    print(f"Excess over ₱16,667: ₱{excess:,.2f}")
    print(f"Tax = ₱937.50 + (₱{excess:,.2f} × 20%)")
    print(f"Tax = ₱937.50 + ₱{excess * rate:,.2f}")
elif taxable_income <= Decimal('83332'):
    excess = taxable_income - Decimal('33333')
    tax = Decimal('4270.70') + (excess * Decimal('0.25'))
    bracket = "₱33,333 - ₱83,332 (25%)"
else:
    excess = taxable_income - Decimal('83333')
    tax = Decimal('16770.70') + (excess * Decimal('0.30'))
    bracket = "₱83,333 - ₱333,332 (30%)"

print()
print("=" * 80)
print(f"WITHHOLDING TAX: ₱{tax:,.2f}")
print("=" * 80)
print()

# Compare with Sprout
sprout_tax = Decimal('3392.70')
difference = tax - sprout_tax

print("COMPARISON WITH SPROUT:")
print(f"  Sprout:         ₱{sprout_tax:,.2f}")
print(f"  Our Calculated: ₱{tax:,.2f}")
print(f"  Difference:     ₱{difference:,.2f}")
print()

if abs(difference) < Decimal('0.01'):
    print("✅ PERFECT MATCH! Tax calculation is CORRECT!")
elif abs(difference) < Decimal('1.00'):
    print("✅ MATCH (within rounding)")
else:
    print(f"⚠️  Difference: ₱{abs(difference):,.2f}")
    
print()
print("=" * 80)
print("NET PAY CALCULATION")
print("=" * 80)
print(f"  Half-month basic:  ₱{halfmonth_basic:,.2f}")
print(f"  Meal allowance:    ₱{meal_allowance:,.2f}")
print(f"  Gross Pay:         ₱{total_basic:,.2f}")
print(f"  Less: SSS         (₱{cutoff_sss:,.2f})")
print(f"  Less: PhilHealth  (₱{cutoff_philhealth:,.2f})")
print(f"  Less: Pag-IBIG    (₱{cutoff_pagibig:,.2f})")
print(f"  Less: Tax         (₱{tax:,.2f})")
print(f"  {'-' * 40}")
net_pay = total_basic - total_cutoff_deductions - tax
print(f"  NET PAY:           ₱{net_pay:,.2f}")
print()

# Verify month-to-date PhilHealth totals
print("=" * 80)
print("PHILHEALTH MONTH-TO-DATE VERIFICATION")
print("=" * 80)
cutoff1_philhealth = philhealth_already_deducted
cutoff2_philhealth = cutoff_philhealth
total_month_philhealth = cutoff1_philhealth + cutoff2_philhealth
print(f"  Cutoff 1:     ₱{cutoff1_philhealth:,.2f}")
print(f"  Cutoff 2:     ₱{cutoff2_philhealth:,.2f}")
print(f"  Month Total:  ₱{total_month_philhealth:,.2f}")
print(f"  Expected:     ₱{monthly_philhealth:,.2f}")
print()
if abs(total_month_philhealth - monthly_philhealth) < Decimal('0.01'):
    print("✅ PhilHealth month total matches!")
else:
    print(f"⚠️  PhilHealth total off by: ₱{abs(total_month_philhealth - monthly_philhealth):,.2f}")
