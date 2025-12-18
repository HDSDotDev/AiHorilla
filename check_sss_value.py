import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horilla.settings')
django.setup()

from payroll.models.models import PhilippinesSSSContribution

monthly_basic = 57886

sss = PhilippinesSSSContribution.objects.filter(
    min_salary__lte=monthly_basic, 
    max_salary__gte=monthly_basic
).first()

if sss:
    print(f"SSS Contribution for salary ₱{monthly_basic}:")
    print(f"  Bracket: ₱{sss.min_salary} - ₱{sss.max_salary}")
    print(f"  Employee: ₱{sss.employee_contribution}")
    print(f"  Employer: ₱{sss.employer_contribution}")
    print(f"  Total: ₱{sss.total_contribution}")
    print()
    print(f"EXPECTED: Employee = ₱1,750.00 (includes ₱750 MPF)")
else:
    print("No SSS bracket found!")
