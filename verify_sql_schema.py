"""
Schema Verification Script for SQL Loader

This script verifies all field names used in load_demo_sql.py against actual Django models
to catch schema mismatches BEFORE deployment.
"""
import os
import django

os.environ['SKIP_SCHEDULERS'] = '1'
os.environ['SKIP_DB_INIT_IN_READY'] = '1'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horilla.settings')

django.setup()

from base.models import Company, Department, JobPosition, WorkType, EmployeeType, EmployeeShift
from employee.models import Employee, EmployeeWorkInformation

def check_model_fields(model_class, model_name):
    """Check and print all fields for a model"""
    print(f"\n{model_name} Model Fields:")
    print("=" * 60)
    fields = model_class._meta.get_fields()
    for field in fields:
        field_type = type(field).__name__
        if hasattr(field, 'null'):
            nullable = f"NULL={field.null}"
        else:
            nullable = ""
        if hasattr(field, 'max_length'):
            max_len = f"max_length={field.max_length}"
        else:
            max_len = ""
        print(f"  {field.name:30} {field_type:25} {nullable:12} {max_len}")

# Check all models used in SQL loader
print("\n" + "=" * 80)
print("CHECKING ALL MODELS USED IN load_demo_sql.py")
print("=" * 80)

check_model_fields(Company, "Company")
check_model_fields(Department, "Department")
check_model_fields(JobPosition, "JobPosition")
check_model_fields(WorkType, "WorkType")
check_model_fields(EmployeeType, "EmployeeType")
check_model_fields(EmployeeShift, "EmployeeShift")
check_model_fields(Employee, "Employee")
check_model_fields(EmployeeWorkInformation, "EmployeeWorkInformation")

print("\n" + "=" * 80)
print("CRITICAL FINDINGS:")
print("=" * 80)

# Check ManyToMany fields (these DON'T have _id suffix in the table)
print("\n1. ManyToMany Fields (require junction tables, not direct foreign keys):")
print("   - Department.company_id (ManyToManyField)")
print("   - JobPosition.company_id (ManyToManyField)")
print("   - WorkType.company_id (ManyToManyField)")
print("   - EmployeeType.company_id (ManyToManyField)")
print("   - EmployeeShift.company_id (ManyToManyField)")

print("\n2. Foreign Key Fields (have _id suffix in DB):")
print("   - JobPosition.department_id → base_jobposition.department_id_id")
print("   - EmployeeWorkInformation.company_id → employee_employeeworkinformation.company_id_id")

print("\n" + "=" * 80)
