"""
Test Payroll for Joseph Sy
Period: September 29 - October 13, 2024
Compare with Sprout tax: ₱3,392.70
"""

import os
import django
from datetime import date
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horilla.settings')
django.setup()

from employee.models import Employee
from payroll.methods.philippines_payroll import philippines_payroll_calculation

def test_joseph_sy_payroll():
    print("=" * 80)
    print("JOSEPH SY PAYROLL TEST")
    print("Period: September 29 - October 13, 2024")
    print("Sprout Expected Tax: ₱3,392.70")
    print("=" * 80)
    print()
    
    # Find Joseph Sy
    try:
        joseph = Employee.objects.get(
            employee_first_name__icontains='Joseph',
            employee_last_name__icontains='Sy'
        )
        print(f"✓ Found Employee: {joseph.get_full_name()}")
        print(f"  Employee ID: {joseph.employee_user_id}")
        print(f"  Badge ID: {joseph.badge_id}")
        
        # Get contract/salary info
        from payroll.models.models import Contract
        contract = Contract.objects.filter(employee_id=joseph).first()
        if contract:
            print(f"  Basic Salary: ₱{contract.wage:,.2f} per month")
        else:
            print("  ⚠️  No contract found")
        print()
        
    except Employee.DoesNotExist:
        print("❌ Joseph Sy not found in database")
        print("\nSearching for similar names...")
        similar = Employee.objects.filter(
            employee_last_name__icontains='Sy'
        ) | Employee.objects.filter(
            employee_first_name__icontains='Joseph'
        )
        for emp in similar:
            print(f"  - {emp.get_full_name()} (ID: {emp.employee_user_id})")
        return
    except Employee.MultipleObjectsReturned:
        print("⚠️  Multiple employees found with name Joseph Sy")
        employees = Employee.objects.filter(
            employee_first_name__icontains='Joseph',
            employee_last_name__icontains='Sy'
        )
        for emp in employees:
            print(f"  - {emp.get_full_name()} (ID: {emp.employee_user_id})")
        joseph = employees.first()
        print(f"\nUsing first match: {joseph.get_full_name()}")
        print()
    
    # Run payroll calculation
    start_date = date(2024, 9, 29)
    end_date = date(2024, 10, 13)
    
    print(f"Running payroll calculation...")
    print(f"Start Date: {start_date}")
    print(f"End Date: {end_date}")
    print(f"Period Days: {(end_date - start_date).days + 1} days")
    print()
    
    try:
        result = philippines_payroll_calculation(
            employee=joseph,
            start_date=start_date,
            end_date=end_date,
            apply_sss=True,
            apply_philhealth=True,
            apply_pagibig=True,
            apply_tax=True,
            apply_allowances=True
        )
        
        print("=" * 80)
        print("PAYROLL RESULTS")
        print("=" * 80)
        print()
        
        # Debug: Print full result structure
        print("DEBUG - Full Result Keys:", list(result.keys()))
        print()
        
        # Basic Pay
        print(f"BASIC PAY: ₱{result['basic_pay']:,.2f}")
        print()
        
        # Allowances
        if result.get('total_allowance', 0) > 0:
            print(f"ALLOWANCES:")
            for allowance in result.get('allowances', []):
                print(f"  {allowance['title']}: ₱{allowance['amount']:,.2f}")
            print(f"  Total Allowances: ₱{result['total_allowance']:,.2f}")
            print()
        
        # Gross Pay
        print(f"GROSS PAY: ₱{result['gross_pay']:,.2f}")
        print()
        
        # Deductions
        print("DEDUCTIONS:")
        total_deductions = 0
        
        for deduction in result.get('deductions', []):
            amount = deduction['amount']
            total_deductions += amount
            print(f"  {deduction['title']}: ₱{amount:,.2f}")
            if deduction.get('description'):
                print(f"    → {deduction['description']}")
        
        print(f"\n  Total Deductions: ₱{total_deductions:,.2f}")
        print()
        
        # Net Pay
        print("=" * 80)
        print(f"NET PAY: ₱{result['net_pay']:,.2f}")
        print("=" * 80)
        print()
        
        # Find the tax deduction
        tax_deduction = None
        for deduction in result.get('deductions', []):
            if 'tax' in deduction['title'].lower() or 'bir' in deduction['title'].lower():
                tax_deduction = deduction
                break
        
        if tax_deduction:
            our_tax = tax_deduction['amount']
            sprout_tax = 3392.70
            
            print("=" * 80)
            print("TAX COMPARISON")
            print("=" * 80)
            print(f"Sprout Tax (BIR):     ₱{sprout_tax:,.2f}")
            print(f"Our Tax (Calculated): ₱{our_tax:,.2f}")
            print(f"Difference:           ₱{(our_tax - sprout_tax):,.2f}")
            print()
            
            if abs(our_tax - sprout_tax) < 1:
                print("✅ MATCH! Tax calculation is CORRECT!")
            elif abs(our_tax - sprout_tax) < 100:
                print("⚠️  Close match - minor difference (likely rounding)")
            else:
                print("❌ MISMATCH - significant difference")
                print()
                print("Possible reasons:")
                print("1. Different basic salary amount")
                print("2. Different allowances included")
                print("3. Different contribution amounts (SSS, PhilHealth, Pag-IBIG)")
                print("4. Different period proration")
            print("=" * 80)
        else:
            print("⚠️  No tax deduction found in results")
        
        return result
        
    except Exception as e:
        print(f"❌ Error running payroll: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    test_joseph_sy_payroll()
