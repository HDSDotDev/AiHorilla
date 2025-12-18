import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horilla.settings')
django.setup()

from employee.models import Employee
from payroll.models.models import Allowance

joseph = Employee.objects.get(id=3)
all_allowances = Allowance.objects.filter(specific_employees=joseph) | \
                 Allowance.objects.filter(include_active_employees=True).exclude(exclude_employees=joseph)

print('ALL Allowances for Joseph Sy:')
print('=' * 60)

total_taxable_monthly = 0
taxable_allowances = []

for a in all_allowances.distinct():
    taxable_str = "TAXABLE" if a.is_taxable else "non-taxable"
    print(f'{a.title:30s} P{a.amount:>8,.2f}  [{taxable_str}]')
    
    if a.is_taxable and a.is_fixed:
        total_taxable_monthly += float(a.amount)
        taxable_allowances.append((a.title, float(a.amount)))

print('=' * 60)
print(f'\nTaxable Allowances (Monthly):')
for title, amount in taxable_allowances:
    print(f'  {title}: P{amount:,.2f}')

print(f'\nTotal Taxable (Monthly): P{total_taxable_monthly:,.2f}')
print(f'Total Taxable (Semi-Monthly): P{total_taxable_monthly/2:,.2f}')

print()
print('Expected from Sprout reverse-engineering:')
print('  Meal Allowance: P1,500.00')
print('  Unknown Allowance: P512.72')
print('  Total Semi-Monthly Allowances: P2,012.72')
print()
print(f'Our Semi-Monthly Allowances: P{total_taxable_monthly/2:,.2f}')
difference = 2012.72 - (total_taxable_monthly/2)
print(f'Missing Amount: P{difference:,.2f}')
print(f'Missing Monthly: P{difference * 2:,.2f}')
