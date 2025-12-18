"""
Debug script to trace payroll calculation issue
"""
import os
import django
from datetime import date

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horilla.settings')
django.setup()

from employee.models import Employee
from payroll.methods.methods import months_between_range, compute_salary_on_period

def debug_payroll():
    """Debug payroll generation for a single employee"""
    
    # Get first employee
    employee = Employee.objects.filter(is_active=True).first()
    if not employee:
        print("[ERROR] No active employees found!")
        return
    
    print(f"\n=== Debugging Payroll for Employee: {employee.get_full_name()} ===\n")
    
    # Check contract
    contract = employee.contract_set.filter(contract_status="active").first()
    if not contract:
        print("[ERROR] Employee has no active contract!")
        return
    
    print(f"Contract found:")
    print(f"  - Wage: PHP {contract.wage}")
    print(f"  - Wage Type: {contract.wage_type}")
    print(f"  - Pay Frequency: {contract.pay_frequency}")
    print(f"  - Contract Status: {contract.contract_status}")
    
    # Check work info
    work_info = employee.employee_work_info
    if not work_info:
        print("[ERROR] Employee has no work information!")
        return
    
    print(f"\nWork Info:")
    print(f"  - Job Position: {work_info.job_position_id}")
    print(f"  - Department: {work_info.department_id}")
    print(f"  - Shift: {work_info.shift_id}")
    print(f"  - Work Type: {work_info.work_type_id}")
    
    # Test dates
    start_date = date(2025, 9, 1)
    end_date = date(2025, 9, 30)
    
    print(f"\nTest Period: {start_date} to {end_date}")
    
    # Test months_between_range
    print(f"\nCalling months_between_range...")
    try:
        month_data = months_between_range(contract.wage, start_date, end_date)
        print(f"✓ months_between_range returned {len(month_data)} months")
        
        if month_data:
            print(f"\nMonth Data:")
            for data in month_data:
                print(f"  - Month {data['month']}/{data['year']}")
                print(f"    Working days in period: {data['working_days_on_period']}")
                print(f"    Working days in month: {data['working_days_on_month']}")
                print(f"    Per day amount: PHP {data['per_day_amount']:.2f}")
        else:
            print(f"✗ months_between_range returned EMPTY LIST!")
            print(f"  This is why the IndexError occurs at month_data[0]")
    except Exception as e:
        print(f"✗ months_between_range FAILED: {e}")
        import traceback
        traceback.print_exc()
    
    # Test compute_salary_on_period
    print(f"\n\nCalling compute_salary_on_period...")
    try:
        result = compute_salary_on_period(employee, start_date, end_date)
        if result:
            print(f"✓ compute_salary_on_period succeeded!")
            print(f"  - Basic Pay: PHP {result.get('basic_pay', 0):.2f}")
            print(f"  - Loss of Pay: PHP {result.get('loss_of_pay', 0):.2f}")
            print(f"  - Paid Days: {result.get('paid_days', 0)}")
            print(f"  - Unpaid Days: {result.get('unpaid_days', 0)}")
        else:
            print(f"✗ compute_salary_on_period returned None (no contract found)")
    except IndexError as e:
        print(f"✗ compute_salary_on_period FAILED with IndexError!")
        print(f"  This confirms the month_data[0] issue")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"✗ compute_salary_on_period FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    debug_payroll()
