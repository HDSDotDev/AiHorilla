"""
Simple test for deduction controls - no special characters
"""
import os
import sys
import django
from datetime import date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horilla.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from employee.models import Employee
from payroll.methods.philippines_payroll import philippines_payroll_calculation

def test_deductions():
    """Test deduction control functionality"""
    
    # Get first employee
    employee = Employee.objects.first()
    if not employee:
        print("ERROR: No employee found")
        return
    
    print("=" * 70)
    print("TESTING DEDUCTION CONTROLS")
    print("=" * 70)
    print(f"Employee: {employee.get_full_name()}")
    print()
    
    # TEST 1: Tax only (Period 1 - Sprout style)
    print("TEST 1: Period 1 - Tax Only (SSS/PhilHealth/Pag-IBIG deferred)")
    print("-" * 70)
    
    result1 = philippines_payroll_calculation(
        employee,
        start_date=date(2025, 9, 1),
        end_date=date(2025, 9, 15),
        apply_sss=False,
        apply_philhealth=False,
        apply_pagibig=False,
        apply_tax=True
    )
    
    print(f"Basic Pay: P{result1['basic_pay']:,.2f}")
    print(f"Gross Pay: P{result1['gross_pay']:,.2f}")
    print()
    print("Deductions:")
    for d in result1['pretax_deductions']:
        status = "DEFERRED" if d['amount'] == 0 else "APPLIED"
        print(f"  {d['title']}: P{d['amount']:,.2f} [{status}]")
        print(f"    -> {d['description']}")
    
    for d in result1['tax_deductions']:
        status = "DEFERRED" if d['amount'] == 0 else "APPLIED"
        print(f"  {d['title']}: P{d['amount']:,.2f} [{status}]")
        print(f"    -> {d['description']}")
    
    print()
    print(f"Total Deductions: P{result1['total_deductions']:,.2f}")
    print(f"NET PAY: P{result1['net_pay']:,.2f}")
    print()
    
    # Validate
    sss_ok = any(d['amount'] == 0 and 'SSS' in d['title'] for d in result1['pretax_deductions'])
    ph_ok = any(d['amount'] == 0 and 'PhilHealth' in d['title'] for d in result1['pretax_deductions'])
    pi_ok = any(d['amount'] == 0 and 'Pag-IBIG' in d['title'] for d in result1['pretax_deductions'])
    tax_ok = any(d['amount'] > 0 and 'Tax' in d['title'] for d in result1['tax_deductions'])
    
    test1_pass = sss_ok and ph_ok and pi_ok and tax_ok
    print(f"Period 1 Test: {'PASS' if test1_pass else 'FAIL'}")
    print()
    print()
    
    # TEST 2: All deductions (Period 2 - Sprout style)
    print("TEST 2: Period 2 - All Deductions (Full monthly contributions)")
    print("-" * 70)
    
    result2 = philippines_payroll_calculation(
        employee,
        start_date=date(2025, 9, 16),
        end_date=date(2025, 9, 30),
        apply_sss=True,
        apply_philhealth=True,
        apply_pagibig=True,
        apply_tax=True
    )
    
    print(f"Basic Pay: P{result2['basic_pay']:,.2f}")
    print(f"Gross Pay: P{result2['gross_pay']:,.2f}")
    print()
    print("Deductions:")
    for d in result2['pretax_deductions']:
        status = "DEFERRED" if d['amount'] == 0 else "APPLIED"
        print(f"  {d['title']}: P{d['amount']:,.2f} [{status}]")
        print(f"    -> {d['description']}")
    
    for d in result2['tax_deductions']:
        status = "DEFERRED" if d['amount'] == 0 else "APPLIED"
        print(f"  {d['title']}: P{d['amount']:,.2f} [{status}]")
        print(f"    -> {d['description']}")
    
    print()
    print(f"Total Deductions: P{result2['total_deductions']:,.2f}")
    print(f"NET PAY: P{result2['net_pay']:,.2f}")
    print()
    
    # Validate
    sss_ok2 = any(d['amount'] > 0 and 'SSS' in d['title'] for d in result2['pretax_deductions'])
    ph_ok2 = any(d['amount'] > 0 and 'PhilHealth' in d['title'] for d in result2['pretax_deductions'])
    pi_ok2 = any(d['amount'] > 0 and 'Pag-IBIG' in d['title'] for d in result2['pretax_deductions'])
    tax_ok2 = any(d['amount'] > 0 and 'Tax' in d['title'] for d in result2['tax_deductions'])
    
    test2_pass = sss_ok2 and ph_ok2 and pi_ok2 and tax_ok2
    print(f"Period 2 Test: {'PASS' if test2_pass else 'FAIL'}")
    print()
    print()
    
    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Test 1 (Tax Only): {'PASS' if test1_pass else 'FAIL'}")
    print(f"Test 2 (All Deductions): {'PASS' if test2_pass else 'FAIL'}")
    print()
    if test1_pass and test2_pass:
        print("SUCCESS! Deduction controls working correctly!")
        print("You can now control which deductions apply per pay period.")
    else:
        print("FAILED! Some deduction controls not working.")

if __name__ == "__main__":
    try:
        test_deductions()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
