import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horilla.settings')
django.setup()

from employee.models import Employee, EmployeeWorkInformation
from payroll.models import Contract
from base.models import JobPosition

# Check first employee
emp = Employee.objects.filter(badge_id='BZQ-0001').first()
print(f'\nEmployee: {emp.employee_first_name} {emp.employee_last_name}')
print(f'Badge: {emp.badge_id}')

# Check work info
work_info = EmployeeWorkInformation.objects.filter(employee_id=emp).first()
print(f'\nWork Info exists: {work_info is not None}')
if work_info:
    print(f'Job Position: {work_info.job_position_id}')
    print(f'Department: {work_info.department_id}')
    print(f'Company: {work_info.company_id}')

# Check contract
contract = Contract.objects.filter(employee_id=emp).first()
print(f'\nContract exists: {contract is not None}')
if contract:
    print(f'Contract ID: {contract.id}')
    print(f'Wage: {contract.wage}')
    print(f'Job Position: {contract.job_position}')
    print(f'Department: {contract.department}')
    print(f'Status: {contract.contract_status}')

# Check total job positions
positions = JobPosition.objects.all()
print(f'\nTotal Job Positions in DB: {positions.count()}')
if positions.count() > 0:
    print(f'Sample positions: {[p.job_position for p in positions[:5]]}')
