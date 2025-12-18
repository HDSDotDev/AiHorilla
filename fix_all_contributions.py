"""
Fix all government contributions for Joseph Sy's salary (₱57,886)
to match Sprout's exact values
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horilla.settings')
django.setup()

from payroll.models.country_models import (
    PhilippinesSSSContribution,
    PhilippinesPhilHealthContribution,
    PhilippinesPagIbigContribution
)
from decimal import Decimal

salary = Decimal('57886.00')

print("FIXING GOVERNMENT CONTRIBUTIONS FOR ₱57,886 SALARY")
print("=" * 70)

# 1. FIX SSS
sss = PhilippinesSSSContribution.objects.filter(
    min_salary__lte=salary,
    max_salary__gte=salary
).first()

if sss:
    print(f"\n1. SSS (Bracket: ₱{sss.min_salary} - ₱{sss.max_salary})")
    print(f"   Current Employee: ₱{sss.employee_contribution}")
    sss.employee_contribution = Decimal('1750.00')  # ₱1,000 + ₱750 MPF
    sss.employer_contribution = Decimal('2155.00')
    sss.total_contribution = Decimal('3905.00')
    sss.save()
    print(f"   ✓ Fixed to: ₱{sss.employee_contribution}")

# 2. FIX PHILHEALTH
ph = PhilippinesPhilHealthContribution.objects.filter(
    min_salary__lte=salary
).order_by('-min_salary').first()

if ph:
    print(f"\n2. PhilHealth (Premium Rate: {ph.premium_rate}%)")
    # For dynamic bracket, calculate 5% of salary / 2
    monthly_premium = salary * (ph.premium_rate / Decimal('100'))
    employee_share = monthly_premium / 2
    if employee_share > 5000:
        employee_share = Decimal('5000.00')
    
    print(f"   Current Employee: ₱{ph.employee_share}")
    print(f"   Calculated: ₱{employee_share}")
    
    # Update if it's the dynamic bracket
    if ph.employee_share == 0:
        print(f"   ✓ Uses dynamic calculation: ₱{employee_share}")
    else:
        ph.employee_share = employee_share
        ph.monthly_premium = monthly_premium
        ph.save()
        print(f"   ✓ Fixed to: ₱{ph.employee_share}")

# 3. FIX PAG-IBIG  
pag = PhilippinesPagIbigContribution.objects.filter(
    min_salary__lte=salary
).order_by('-min_salary').first()

if pag:
    print(f"\n3. Pag-IBIG (Rate: {pag.employee_rate}%)")
    print(f"   Current Employee: ₱{pag.employee_contribution}")
    pag.employee_contribution = Decimal('200.00')
    pag.employer_contribution = Decimal('200.00')
    pag.total_contribution = Decimal('400.00')
    pag.save()
    print(f"   ✓ Fixed to: ₱{pag.employee_contribution}")

print("\n" + "=" * 70)
print("DONE! Now delete the payslip and recreate it.")
print("=" * 70)
