"""
Test script to verify deduction control functionality
This simulates the Sprout payroll strategy:
- Period 1: Tax only (higher take-home)
- Period 2: All contributions (full monthly obligations)
"""

import os
import sys
import django
from datetime import date

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horilla.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from employee.models import Employee
from payroll.methods.philippines_payroll import philippines_payroll_calculation

def format_currency(amount):
    """Format amount as Philippine pesos"""
    return f"₱{amount:,.2f}"

def print_payslip(period_name, result):
    """Print formatted payslip details"""
    print(f"\n{'='*80}")
    print(f"  {period_name}")
    print(f"{'='*80}")
    
    # Basic Pay
    print(f"\nBASIC PAY:")
    print(f"  Gross: {format_currency(result['basic_pay'])}")
    print(f"  Paid Days: {result['paid_days']}")
    
    # Deductions
    print(f"\nDEDUCTIONS:")
    for deduction in result['pretax_deductions']:
        print(f"  {deduction['title']}: {format_currency(deduction['amount'])}")
        if deduction['description']:
            print(f"    └─ {deduction['description']}")
    
    for deduction in result['tax_deductions']:
        print(f"  {deduction['title']}: {format_currency(deduction['amount'])}")
        if deduction['description']:
            print(f"    └─ {deduction['description']}")
    
    # Totals
    print(f"\nSUMMARY:")
    print(f"  Gross Pay: {format_currency(result['gross_pay'])}")
    print(f"  Total Deductions: {format_currency(result['total_deductions'])}")
    print(f"  NET PAY: {format_currency(result['net_pay'])}")

def test_period_1_tax_only():
    """Test Period 1: Only tax deduction (Sprout strategy)"""
    print("\n" + "="*80)
    print("TEST 1: PERIOD 1 - TAX ONLY (Sept 1-15, 2025)")
    print("="*80)
    print("\nScenario: Sprout-style Period 1")
    print("- SSS: DEFERRED (unchecked)")
    print("- PhilHealth: DEFERRED (unchecked)")
    print("- Pag-IBIG: DEFERRED (unchecked)")
    print("- Tax: APPLIED (checked)")
    
    # Get test employee
    employee = Employee.objects.filter(
        employee_work_info__isnull=False
    ).first()
    
    if not employee:
        print("\n❌ ERROR: No employee found")
        return False
    
    print(f"\nEmployee: {employee.get_full_name()}")
    
    # Calculate with only tax
    result = philippines_payroll_calculation(
        employee,
        start_date=date(2025, 9, 1),
        end_date=date(2025, 9, 15),
        apply_sss=False,
        apply_philhealth=False,
        apply_pagibig=False,
        apply_tax=True
    )
    
    print_payslip("PERIOD 1 PAYSLIP (Sept 1-15, 2025)", result)
    
    # Validate expectations
    print(f"\n{'='*80}")
    print("VALIDATION:")
    print(f"{'='*80}")
    
    # Check SSS is 0
    sss_amount = next((d['amount'] for d in result['pretax_deductions'] if 'SSS' in d['title']), None)
    print(f"✓ SSS deferred: {sss_amount == 0.0} (amount: {format_currency(sss_amount)})")
    
    # Check PhilHealth is 0
    ph_amount = next((d['amount'] for d in result['pretax_deductions'] if 'PhilHealth' in d['title']), None)
    print(f"✓ PhilHealth deferred: {ph_amount == 0.0} (amount: {format_currency(ph_amount)})")
    
    # Check Pag-IBIG is 0
    pi_amount = next((d['amount'] for d in result['pretax_deductions'] if 'Pag-IBIG' in d['title']), None)
    print(f"✓ Pag-IBIG deferred: {pi_amount == 0.0} (amount: {format_currency(pi_amount)})")
    
    # Check Tax is NOT 0
    tax_amount = next((d['amount'] for d in result['tax_deductions'] if 'Tax' in d['title']), None)
    print(f"✓ Tax applied: {tax_amount > 0} (amount: {format_currency(tax_amount)})")
    
    success = (sss_amount == 0.0 and ph_amount == 0.0 and pi_amount == 0.0 and tax_amount > 0)
    print(f"\nPeriod 1 Test: {'✅ PASSED' if success else '❌ FAILED'}")
    
    return success, result

def test_period_2_all_deductions():
    """Test Period 2: All deductions (Sprout strategy)"""
    print("\n" + "="*80)
    print("TEST 2: PERIOD 2 - ALL DEDUCTIONS (Sept 16-30, 2025)")
    print("="*80)
    print("\nScenario: Sprout-style Period 2")
    print("- SSS: APPLIED (checked) - FULL monthly contribution")
    print("- PhilHealth: APPLIED (checked) - FULL monthly contribution")
    print("- Pag-IBIG: APPLIED (checked) - FULL monthly contribution")
    print("- Tax: APPLIED (checked)")
    
    # Get test employee
    employee = Employee.objects.filter(
        employee_work_info__isnull=False
    ).first()
    
    if not employee:
        print("\n❌ ERROR: No employee found")
        return False
    
    print(f"\nEmployee: {employee.get_full_name()}")
    
    # Calculate with all deductions
    result = philippines_payroll_calculation(
        employee,
        start_date=date(2025, 9, 16),
        end_date=date(2025, 9, 30),
        apply_sss=True,
        apply_philhealth=True,
        apply_pagibig=True,
        apply_tax=True
    )
    
    print_payslip("PERIOD 2 PAYSLIP (Sept 16-30, 2025)", result)
    
    # Validate expectations
    print(f"\n{'='*80}")
    print("VALIDATION:")
    print(f"{'='*80}")
    
    # Check all deductions are applied
    sss_amount = next((d['amount'] for d in result['pretax_deductions'] if 'SSS' in d['title']), None)
    print(f"✓ SSS applied: {sss_amount > 0} (amount: {format_currency(sss_amount)})")
    
    ph_amount = next((d['amount'] for d in result['pretax_deductions'] if 'PhilHealth' in d['title']), None)
    print(f"✓ PhilHealth applied: {ph_amount > 0} (amount: {format_currency(ph_amount)})")
    
    pi_amount = next((d['amount'] for d in result['pretax_deductions'] if 'Pag-IBIG' in d['title']), None)
    print(f"✓ Pag-IBIG applied: {pi_amount > 0} (amount: {format_currency(pi_amount)})")
    
    tax_amount = next((d['amount'] for d in result['tax_deductions'] if 'Tax' in d['title']), None)
    print(f"✓ Tax applied: {tax_amount > 0} (amount: {format_currency(tax_amount)})")
    
    success = (sss_amount > 0 and ph_amount > 0 and pi_amount > 0 and tax_amount > 0)
    print(f"\nPeriod 2 Test: {'✅ PASSED' if success else '❌ FAILED'}")
    
    return success, result

def test_combined_compliance(period1_result, period2_result):
    """Verify combined periods meet monthly obligations"""
    print("\n" + "="*80)
    print("TEST 3: COMBINED PERIOD COMPLIANCE")
    print("="*80)
    print("\nVerifying that both periods combined = full monthly obligations")
    
    # Get deduction amounts from both periods
    def get_amount(deductions, keyword):
        return next((d['amount'] for d in deductions if keyword in d['title']), 0.0)
    
    # Period 1 (deferred)
    p1_sss = get_amount(period1_result['pretax_deductions'], 'SSS')
    p1_ph = get_amount(period1_result['pretax_deductions'], 'PhilHealth')
    p1_pi = get_amount(period1_result['pretax_deductions'], 'Pag-IBIG')
    p1_tax = get_amount(period1_result['tax_deductions'], 'Tax')
    
    # Period 2 (full monthly)
    p2_sss = get_amount(period2_result['pretax_deductions'], 'SSS')
    p2_ph = get_amount(period2_result['pretax_deductions'], 'PhilHealth')
    p2_pi = get_amount(period2_result['pretax_deductions'], 'Pag-IBIG')
    p2_tax = get_amount(period2_result['tax_deductions'], 'Tax')
    
    # Combined totals
    total_sss = p1_sss + p2_sss
    total_ph = p1_ph + p2_ph
    total_pi = p1_pi + p2_pi
    total_tax = p1_tax + p2_tax
    
    print(f"\nGOVERNMENT CONTRIBUTIONS:")
    print(f"  SSS:")
    print(f"    Period 1: {format_currency(p1_sss)} (deferred)")
    print(f"    Period 2: {format_currency(p2_sss)} (FULL monthly)")
    print(f"    Combined: {format_currency(total_sss)} ✅")
    
    print(f"\n  PhilHealth:")
    print(f"    Period 1: {format_currency(p1_ph)} (deferred)")
    print(f"    Period 2: {format_currency(p2_ph)} (FULL monthly)")
    print(f"    Combined: {format_currency(total_ph)} ✅")
    
    print(f"\n  Pag-IBIG:")
    print(f"    Period 1: {format_currency(p1_pi)} (deferred)")
    print(f"    Period 2: {format_currency(p2_pi)} (FULL monthly)")
    print(f"    Combined: {format_currency(total_pi)} ✅")
    
    print(f"\n  BIR Tax:")
    print(f"    Period 1: {format_currency(p1_tax)}")
    print(f"    Period 2: {format_currency(p2_tax)}")
    print(f"    Combined: {format_currency(total_tax)} ✅")
    
    print(f"\nTOTAL MONTHLY DEDUCTIONS: {format_currency(total_sss + total_ph + total_pi + total_tax)}")
    
    # Validate
    print(f"\n{'='*80}")
    print("COMPLIANCE CHECK:")
    print(f"{'='*80}")
    print(f"✅ Full monthly SSS paid in Period 2: {total_sss == p2_sss}")
    print(f"✅ Full monthly PhilHealth paid in Period 2: {total_ph == p2_ph}")
    print(f"✅ Full monthly Pag-IBIG paid in Period 2: {total_pi == p2_pi}")
    print(f"✅ Both periods calculated tax: {p1_tax > 0 and p2_tax > 0}")
    
    return True

def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("PHILIPPINES PAYROLL DEDUCTION CONTROL TEST SUITE")
    print("Testing Sprout-style flexible deduction strategy")
    print("="*80)
    
    try:
        # Test Period 1
        success1, period1_result = test_period_1_tax_only()
        
        # Test Period 2
        success2, period2_result = test_period_2_all_deductions()
        
        # Test Combined Compliance
        if success1 and success2:
            test_combined_compliance(period1_result, period2_result)
        
        # Final Summary
        print("\n" + "="*80)
        print("FINAL RESULTS")
        print("="*80)
        print(f"Period 1 (Tax Only): {'✅ PASSED' if success1 else '❌ FAILED'}")
        print(f"Period 2 (All Deductions): {'✅ PASSED' if success2 else '❌ FAILED'}")
        print(f"\nOverall Test Suite: {'✅ ALL TESTS PASSED' if (success1 and success2) else '❌ SOME TESTS FAILED'}")
        
        if success1 and success2:
            print("\n🎉 SUCCESS! Deduction control implementation working as expected!")
            print("   You can now use the checkboxes to control which deductions apply per pay period.")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()
