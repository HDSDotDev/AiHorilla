import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horilla.settings')
django.setup()

from payroll.models.models import PhilippinesSSSContribution
from decimal import Decimal

# Check current SSS for Joseph Sy's salary bracket
salary = Decimal('57886')
sss = PhilippinesSSSContribution.objects.filter(
    min_salary__lte=salary,
    max_salary__gte=salary
).first()

print("=" * 80)
print("CURRENT SSS CONTRIBUTION IN DATABASE")
print("=" * 80)
if sss:
    print(f"Bracket: ₱{sss.min_salary} - ₱{sss.max_salary}")
    print(f"Employee Contribution: ₱{sss.employee_contribution}")
    print(f"Employer Contribution: ₱{sss.employer_contribution}")
    print()
    print("EXPECTED (per Sprout):")
    print("Employee Contribution: ₱1,750.00 (includes ₱750 MPF)")
    print()
    
    # Fix it if wrong
    if sss.employee_contribution != Decimal('1750.00'):
        print(f"❌ WRONG! Should be ₱1,750.00, currently ₱{sss.employee_contribution}")
        print()
        print("Fixing...")
        sss.employee_contribution = Decimal('1750.00')
        sss.employer_contribution = Decimal('2155.00')  # Employer pays more
        sss.total_contribution = Decimal('3905.00')  # Total
        sss.save()
        print("✓ FIXED! SSS contribution updated to ₱1,750.00")
    else:
        print("✓ Correct value in database")
else:
    print("❌ No SSS bracket found for this salary!")

print("=" * 80)
