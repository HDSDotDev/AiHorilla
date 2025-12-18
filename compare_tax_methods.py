"""
Comparison: Old Annual Method vs New Semi-Monthly Method
Shows the difference between the two tax calculation approaches
"""

from decimal import Decimal

def old_annual_method(monthly_basic, sss, philhealth, pagibig):
    """
    OLD METHOD: Annualize, apply exemptions, use annual brackets, divide by 12
    """
    print("=" * 80)
    print("OLD METHOD (Annual Approach)")
    print("=" * 80)
    
    # Annualize
    annual_basic = monthly_basic * 12
    print(f"1. Annual Basic: ₱{monthly_basic:,.2f} × 12 = ₱{annual_basic:,.2f}")
    
    # Apply exemptions
    personal_exemption = Decimal('50000')
    dependent_exemption = Decimal('0')  # Assume 0 dependents for comparison
    total_exemptions = personal_exemption + dependent_exemption
    print(f"2. Personal Exemption: ₱{personal_exemption:,.2f}")
    print(f"3. Dependent Exemption: ₱{dependent_exemption:,.2f}")
    
    # Annual deductions
    annual_sss = sss * 12
    annual_philhealth = philhealth * 12
    annual_pagibig = pagibig * 12
    total_annual_deductions = annual_sss + annual_philhealth + annual_pagibig
    print(f"4. Annual Contributions: ₱{total_annual_deductions:,.2f}")
    
    # Taxable income
    taxable_annual = annual_basic - total_exemptions - total_annual_deductions
    print(f"5. Taxable Annual Income: ₱{annual_basic:,.2f} - ₱{total_exemptions:,.2f} - ₱{total_annual_deductions:,.2f}")
    print(f"   = ₱{taxable_annual:,.2f}")
    
    # Apply annual brackets
    annual_tax = Decimal('0')
    if taxable_annual <= Decimal('250000'):
        annual_tax = Decimal('0')
        bracket = "₱0 - ₱250,000 (0%)"
    elif taxable_annual <= Decimal('400000'):
        annual_tax = (taxable_annual - Decimal('250000')) * Decimal('0.15')
        bracket = "₱250,001 - ₱400,000 (15%)"
    elif taxable_annual <= Decimal('800000'):
        annual_tax = Decimal('22500') + ((taxable_annual - Decimal('400000')) * Decimal('0.20'))
        bracket = "₱400,001 - ₱800,000 (20%)"
    elif taxable_annual <= Decimal('2000000'):
        annual_tax = Decimal('102500') + ((taxable_annual - Decimal('800000')) * Decimal('0.25'))
        bracket = "₱800,001 - ₱2,000,000 (25%)"
    else:
        annual_tax = Decimal('402500') + ((taxable_annual - Decimal('2000000')) * Decimal('0.30'))
        bracket = "Above ₱2,000,000 (30%)"
    
    print(f"6. Annual Tax Bracket: {bracket}")
    print(f"7. Annual Tax: ₱{annual_tax:,.2f}")
    
    # Monthly tax
    monthly_tax = annual_tax / 12
    print(f"8. Monthly Tax: ₱{annual_tax:,.2f} ÷ 12 = ₱{monthly_tax:,.2f}")
    
    # Semi-monthly tax
    semimonthly_tax = monthly_tax / 2
    print(f"9. Semi-Monthly Tax: ₱{monthly_tax:,.2f} ÷ 2 = ₱{semimonthly_tax:,.2f}")
    print()
    
    return semimonthly_tax

def new_semimonthly_method(monthly_basic, sss, philhealth, pagibig):
    """
    NEW METHOD: Semi-monthly direct, no exemptions, contributions deducted first
    """
    print("=" * 80)
    print("NEW METHOD (Semi-Monthly Direct - Accountant Approved)")
    print("=" * 80)
    
    # Half-month basic
    halfmonth_basic = monthly_basic / 2
    print(f"1. Half-Month Basic: ₱{monthly_basic:,.2f} ÷ 2 = ₱{halfmonth_basic:,.2f}")
    
    # Deduct contributions
    total_contributions = sss + philhealth + pagibig
    taxable_income = halfmonth_basic - total_contributions
    print(f"2. Deduct Contributions:")
    print(f"   SSS: ₱{sss:,.2f}")
    print(f"   PhilHealth: ₱{philhealth:,.2f}")
    print(f"   Pag-IBIG: ₱{pagibig:,.2f}")
    print(f"   Total: ₱{total_contributions:,.2f}")
    print(f"3. Taxable Income: ₱{halfmonth_basic:,.2f} - ₱{total_contributions:,.2f} = ₱{taxable_income:,.2f}")
    
    # Apply semi-monthly brackets
    tax = Decimal('0')
    if taxable_income <= Decimal('10417'):
        tax = Decimal('0')
        bracket = "≤ ₱10,417 (0%)"
        formula = "₱0"
    elif taxable_income <= Decimal('16666'):
        tax = (taxable_income - Decimal('10417')) * Decimal('0.15')
        bracket = "₱10,417 - ₱16,666 (15%)"
        formula = f"(₱{taxable_income:,.2f} - ₱10,417) × 15% = ₱{tax:,.2f}"
    elif taxable_income <= Decimal('33332'):
        tax = Decimal('937.50') + ((taxable_income - Decimal('16667')) * Decimal('0.20'))
        bracket = "₱16,667 - ₱33,332 (20%)"
        excess = taxable_income - Decimal('16667')
        formula = f"₱937.50 + (₱{excess:,.2f} × 20%) = ₱{tax:,.2f}"
    elif taxable_income <= Decimal('83332'):
        tax = Decimal('4270.70') + ((taxable_income - Decimal('33333')) * Decimal('0.25'))
        bracket = "₱33,333 - ₱83,332 (25%)"
        excess = taxable_income - Decimal('33333')
        formula = f"₱4,270.70 + (₱{excess:,.2f} × 25%) = ₱{tax:,.2f}"
    elif taxable_income <= Decimal('333332'):
        tax = Decimal('16770.70') + ((taxable_income - Decimal('83333')) * Decimal('0.30'))
        bracket = "₱83,333 - ₱333,332 (30%)"
        excess = taxable_income - Decimal('83333')
        formula = f"₱16,770.70 + (₱{excess:,.2f} × 30%) = ₱{tax:,.2f}"
    else:
        tax = Decimal('91770.70') + ((taxable_income - Decimal('333333')) * Decimal('0.35'))
        bracket = "Above ₱333,333 (35%)"
        excess = taxable_income - Decimal('333333')
        formula = f"₱91,770.70 + (₱{excess:,.2f} × 35%) = ₱{tax:,.2f}"
    
    print(f"4. Semi-Monthly Tax Bracket: {bracket}")
    print(f"5. Formula: {formula}")
    print(f"6. Semi-Monthly Tax: ₱{tax:,.2f}")
    print()
    
    return tax

def compare_methods():
    """
    Compare both methods side by side
    """
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "TAX CALCULATION COMPARISON" + " " * 32 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    
    # Sample data
    monthly_basic = Decimal('57486.00')
    sss = Decimal('1125.00')
    philhealth = Decimal('1437.15')
    pagibig = Decimal('100.00')
    
    print(f"Sample Employee:")
    print(f"  Monthly Basic Salary: ₱{monthly_basic:,.2f}")
    print(f"  SSS: ₱{sss:,.2f}")
    print(f"  PhilHealth: ₱{philhealth:,.2f}")
    print(f"  Pag-IBIG: ₱{pagibig:,.2f}")
    print()
    
    old_tax = old_annual_method(monthly_basic, sss, philhealth, pagibig)
    new_tax = new_semimonthly_method(monthly_basic, sss, philhealth, pagibig)
    
    # Comparison
    print("=" * 80)
    print("RESULTS COMPARISON")
    print("=" * 80)
    print(f"Old Method (Annual): ₱{old_tax:,.2f}")
    print(f"New Method (Semi-Monthly): ₱{new_tax:,.2f}")
    difference = new_tax - old_tax
    print(f"Difference: ₱{difference:,.2f}")
    
    if difference > 0:
        print(f"New method results in ₱{difference:,.2f} MORE tax per semi-monthly period")
    elif difference < 0:
        print(f"New method results in ₱{abs(difference):,.2f} LESS tax per semi-monthly period")
    else:
        print("Both methods produce the same result")
    
    print()
    print("=" * 80)
    print("WHY THE DIFFERENCE?")
    print("=" * 80)
    print("1. Old method applied ₱50,000 personal exemption annually")
    print("2. Old method annualized contributions which diluted their tax benefit")
    print("3. New method deducts contributions DIRECTLY from semi-monthly basic")
    print("4. Semi-monthly brackets have different thresholds than annual÷24")
    print()
    print("The NEW METHOD is what Sprout uses and what the accountant confirmed.")
    print("=" * 80)

if __name__ == '__main__':
    compare_methods()
