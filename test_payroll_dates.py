"""
Debug script to test payroll generation with different date formats
"""
import os
import django
from datetime import date, datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horilla.settings')
django.setup()

from employee.models import Employee
from payroll.views.component_views import payroll_calculation

def test_payroll_generation():
    """Test payroll generation like the web interface does"""
    
    employees = Employee.objects.filter(is_active=True)[:3]  # Test first 3 employees
    
    # Test different date formats
    test_cases = [
        ("String dates (ISO)", "2025-09-01", "2025-09-30"),
        ("Date objects", date(2025, 9, 1), date(2025, 9, 30)),
        ("December 2024", date(2024, 12, 1), date(2024, 12, 31)),
        ("November 2024", date(2024, 11, 1), date(2024, 11, 30)),
        ("Single day", date(2025, 9, 1), date(2025, 9, 1)),
    ]
    
    for test_name, start, end in test_cases:
        print(f"\n{'='*60}")
        print(f"TEST: {test_name}")
        print(f"{'='*60}")
        print(f"Start: {start} (type: {type(start).__name__})")
        print(f"End: {end} (type: {type(end).__name__})")
        
        # Convert string dates to date objects if needed
        if isinstance(start, str):
            start = datetime.strptime(start, "%Y-%m-%d").date()
        if isinstance(end, str):
            end = datetime.strptime(end, "%Y-%m-%d").date()
        
        print(f"\nTesting with {len(employees)} employees...")
        
        for employee in employees:
            print(f"\n  Employee: {employee.get_full_name()} (ID: {employee.id})")
            
            try:
                # This mimics what component_views.py does
                from payroll.methods.philippines_payroll import philippines_payroll_calculation
                
                result = philippines_payroll_calculation(employee, start, end)
                
                if result:
                    print(f"    ✓ SUCCESS")
                    print(f"      Basic Pay: PHP {result.get('basic_pay', 0):,.2f}")
                    print(f"      Gross Pay: PHP {result.get('gross_pay', 0):,.2f}")
                    print(f"      Net Pay: PHP {result.get('net_pay', 0):,.2f}")
                else:
                    print(f"    ✗ FAILED: returned None")
                    
            except Exception as e:
                print(f"    ✗ FAILED: {type(e).__name__}: {e}")
                
                # Show first few lines of traceback
                import traceback
                tb_lines = traceback.format_exc().split('\n')
                for line in tb_lines[-5:]:
                    if line.strip():
                        print(f"      {line}")

if __name__ == '__main__':
    test_payroll_generation()
