"""
Manual Tax Calculation for Joseph Sy
Period: September 29 - October 13, 2024 (15 days)
Monthly Salary: ₱57,886.00
Sprout Expected Tax: ₱3,392.70
"""

from decimal import Decimal

print("=" * 80)
print("JOSEPH SY - MANUAL TAX CALCULATION")
print("=" * 80)
print()

# Employee Data
monthly_salary = Decimal('57886.00')
meal_allowance = Decimal('3000.00')  # Taxable allowance
period_days = 15
standard_semimonthly_days = 15

print(f"Monthly Salary: ₱{monthly_salary:,.2f}")
print(f"Meal Allowance (Taxable): ₱{meal_allowance:,.2f}")
print(f"Period: September 29 - October 13, 2024 ({period_days} days)")
print()

# Step 1: Calculate half-month basic + allowances
halfmonth_basic = monthly_salary / 2
halfmonth_allowance = meal_allowance / 2
halfmonth_total = halfmonth_basic + halfmonth_allowance

print(f"Step 1: Half-Month Total (Basic + Allowances)")
print(f"  Basic: ₱{monthly_salary:,.2f} ÷ 2 = ₱{halfmonth_basic:,.2f}")
print(f"  Meal Allowance: ₱{meal_allowance:,.2f} ÷ 2 = ₱{halfmonth_allowance:,.2f}")
print(f"  Total: ₱{halfmonth_total:,.2f}")
print()

# Step 2: Get government contributions
# SSS for Joseph Sy's salary level
sss_contribution = Decimal('1750.00')  # Actual SSS employee share from Sprout
# PhilHealth: 5% premium rate, employee pays half, max ₱5,000
philhealth_premium = monthly_salary * Decimal('0.05')
philhealth_employee = philhealth_premium / 2
if philhealth_employee > Decimal('5000'):
    philhealth_employee = Decimal('5000')
# Actual calculation: ₱57,886 × 5% = ₱2,894.30, ÷ 2 = ₱1,447.15
philhealth_contribution = Decimal('1447.15')

# Pag-IBIG: 2% of basic, employee share
pagibig_contribution = Decimal('100.00')  # Standard for most salaries

print(f"Step 2: Government Contributions (BEFORE Tax)")
print(f"  SSS:        ₱{sss_contribution:,.2f}")
print(f"  PhilHealth: ₱{philhealth_contribution:,.2f}")
print(f"  Pag-IBIG:   ₱{pagibig_contribution:,.2f}")
total_contributions = sss_contribution + philhealth_contribution + pagibig_contribution
print(f"  Total:      ₱{total_contributions:,.2f}")
print()

# Step 3: Calculate taxable income
taxable_income = halfmonth_total - total_contributions
print(f"Step 3: Taxable Income")
print(f"  ₱{halfmonth_total:,.2f} − ₱{total_contributions:,.2f} = ₱{taxable_income:,.2f}")
print()

# Step 4: Apply semi-monthly tax brackets
print(f"Step 4: Apply Semi-Monthly Tax Bracket")
tax = Decimal('0')
bracket_name = ""

if taxable_income <= Decimal('10417'):
    tax = Decimal('0.00')
    bracket_name = "≤ ₱10,417 (0%)"
    formula = "₱0"
elif taxable_income <= Decimal('16666'):
    tax = (taxable_income - Decimal('10417')) * Decimal('0.15')
    bracket_name = "₱10,417 - ₱16,666 (15%)"
    formula = f"(₱{taxable_income:,.2f} - ₱10,417) × 15%"
elif taxable_income <= Decimal('33332'):
    tax = Decimal('937.50') + ((taxable_income - Decimal('16667')) * Decimal('0.20'))
    bracket_name = "₱16,667 - ₱33,332 (20%)"
    excess = taxable_income - Decimal('16667')
    formula = f"₱937.50 + (₱{excess:,.2f} × 20%)"
    print(f"  Bracket: {bracket_name}")
    print(f"  Excess over ₱16,667: ₱{excess:,.2f}")
    print(f"  Tax on excess: ₱{excess:,.2f} × 20% = ₱{excess * Decimal('0.20'):,.2f}")
    print(f"  Base tax: ₱937.50")
elif taxable_income <= Decimal('83332'):
    tax = Decimal('4270.70') + ((taxable_income - Decimal('33333')) * Decimal('0.25'))
    bracket_name = "₱33,333 - ₱83,332 (25%)"
    excess = taxable_income - Decimal('33333')
    formula = f"₱4,270.70 + (₱{excess:,.2f} × 25%)"
elif taxable_income <= Decimal('333332'):
    tax = Decimal('16770.70') + ((taxable_income - Decimal('83333')) * Decimal('0.30'))
    bracket_name = "₱83,333 - ₱333,332 (30%)"
    excess = taxable_income - Decimal('83333')
    formula = f"₱16,770.70 + (₱{excess:,.2f} × 30%)"
else:
    tax = Decimal('91770.70') + ((taxable_income - Decimal('333333')) * Decimal('0.35'))
    bracket_name = "Above ₱333,333 (35%)"
    excess = taxable_income - Decimal('333333')
    formula = f"₱91,770.70 + (₱{excess:,.2f} × 35%)"

if 'Bracket' not in locals() or bracket_name not in ["₱16,667 - ₱33,332 (20%)"]:
    print(f"  Bracket: {bracket_name}")

print(f"  Formula: {formula}")
print()

print("=" * 80)
print(f"WITHHOLDING TAX (Semi-Monthly): ₱{tax:,.2f}")
print("=" * 80)
print()

# Compare with Sprout
sprout_tax = Decimal('3392.70')
difference = tax - sprout_tax

print("=" * 80)
print("COMPARISON WITH SPROUT")
print("=" * 80)
print(f"Sprout Tax:       ₱{sprout_tax:,.2f}")
print(f"Our Calculated:   ₱{tax:,.2f}")
print(f"Difference:       ₱{difference:,.2f}")
print()

if abs(difference) < Decimal('1'):
    print("✅ PERFECT MATCH!")
elif abs(difference) < Decimal('10'):
    print("✅ VERY CLOSE - likely rounding difference")
elif abs(difference) < Decimal('100'):
    print("⚠️  CLOSE - minor difference")
    percentage_diff = (abs(difference) / sprout_tax) * 100
    print(f"   ({percentage_diff:.2f}% difference)")
else:
    print("❌ SIGNIFICANT DIFFERENCE")
    percentage_diff = (abs(difference) / sprout_tax) * 100
    print(f"   ({percentage_diff:.2f}% difference)")
    
print()
print("Possible reasons for difference:")
print("1. Different contribution amounts (SSS, PhilHealth, Pag-IBIG)")
print("2. Allowances included in Sprout but not here")
print("3. Different basic salary calculation for the period")
print("=" * 80)

# Show net pay calculation
print()
print("NET PAY CALCULATION:")
print(f"  Half-Month Basic:   ₱{halfmonth_basic:,.2f}")
print(f"  Meal Allowance:     ₱{halfmonth_allowance:,.2f}")
print(f"  Gross Pay:          ₱{halfmonth_total:,.2f}")
print(f"  Less: SSS          (₱{sss_contribution:,.2f})")
print(f"  Less: PhilHealth   (₱{philhealth_contribution:,.2f})")
print(f"  Less: Pag-IBIG     (₱{pagibig_contribution:,.2f})")
print(f"  Less: Tax          (₱{tax:,.2f})")
print(f"  {'-' * 40}")
net_pay = halfmonth_total - total_contributions - tax
print(f"  NET PAY:            ₱{net_pay:,.2f}")
