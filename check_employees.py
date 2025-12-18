"""
Check all employee contracts and work info
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horilla.settings')
django.setup()

from employee.models import Employee, EmployeeWorkInformation
from payroll.models.models import Contract

def check_all_employees():
    """Check all employees for contract and work info completeness"""
    
    employees = Employee.objects.filter(is_active=True).order_by('id')
    print(f"\n=== Checking {employees.count()} Active Employees ===\n")
    
    issues_found = []
    
    for emp in employees:
        emp_issues = []
        
        # Check contract
        contracts = emp.contract_set.filter(contract_status="active")
        if not contracts.exists():
            emp_issues.append("No active contract")
        elif contracts.count() > 1:
            emp_issues.append(f"Multiple active contracts ({contracts.count()})")
        else:
            contract = contracts.first()
            if contract.wage == 0:
                emp_issues.append("Wage is 0")
            if not contract.wage_type:
                emp_issues.append("No wage_type")
        
        # Check work info
        try:
            work_info = emp.employee_work_info
            if not work_info:
                emp_issues.append("No work info")
            else:
                if not work_info.shift_id:
                    emp_issues.append("No shift assigned")
                if not work_info.job_position_id:
                    emp_issues.append("No job position")
                if not work_info.department_id:
                    emp_issues.append("No department")
        except EmployeeWorkInformation.DoesNotExist:
            emp_issues.append("No work info (DoesNotExist)")
        
        # Report results
        if emp_issues:
            issues_found.append({
                'employee': emp,
                'issues': emp_issues
            })
            print(f"✗ Employee #{emp.id} - {emp.get_full_name()}")
            for issue in emp_issues:
                print(f"    - {issue}")
        else:
            print(f"✓ Employee #{emp.id} - {emp.get_full_name()}")
    
    print(f"\n=== Summary ===")
    print(f"Total Employees: {employees.count()}")
    print(f"Employees with Issues: {len(issues_found)}")
    print(f"Employees OK: {employees.count() - len(issues_found)}")
    
    if issues_found:
        print(f"\n✗ FOUND {len(issues_found)} EMPLOYEES WITH ISSUES!")
        print(f"These employees will likely fail payroll generation.")
    else:
        print(f"\n✓ ALL EMPLOYEES ARE READY FOR PAYROLL!")

if __name__ == '__main__':
    check_all_employees()
