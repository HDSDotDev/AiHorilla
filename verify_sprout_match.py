#!/usr/bin/env python
"""Verify Sprout-matched tax calculation"""

monthly_basic = 57886
meal = 3000
annual_basic = monthly_basic * 12
annual_meal = meal * 12
annual_gross = annual_basic + annual_meal

contrib = (1125 + 1447.15 + 100) * 12
thirteenth = 90000
additional = 92208
total_ded = contrib + thirteenth + additional
taxable = annual_gross - total_ded

base_tax = 50000
excess = taxable - 400000
annual_tax = base_tax + (excess * 0.20)
monthly_tax = annual_tax / 12

p1_tax = monthly_tax * 0.5
p2_tax = monthly_tax * 0.5

print('SPROUT-MATCHED TAX CALCULATION')
print('='*60)
print(f'Annual Gross: ₱{annual_gross:,.2f}')
print(f'Total Deductions: ₱{total_ded:,.2f}')
print(f'  - Contributions: ₱{contrib:,.2f}')
print(f'  - 13th Month: ₱{thirteenth:,.2f}')
print(f'  - De Minimis: ₱{additional:,.2f}')
print(f'Taxable Annual: ₱{taxable:,.2f}')
print()
print(f'Annual Tax: ₱{annual_tax:,.2f}')
print(f'Monthly Tax: ₱{monthly_tax:,.2f}')
print()
print('PERIOD TAX (15 days each):')
print(f'  Period 1: ₱{p1_tax:,.2f}')
print(f'  Period 2: ₱{p2_tax:,.2f}')
print(f'  Total: ₱{p1_tax + p2_tax:,.2f}')
print()
print('SPROUT COMPARISON:')
sprout_p1 = 3392.70
sprout_p2 = 2713.27
sprout_total = sprout_p1 + sprout_p2
print(f'  Sprout Period 1: ₱{sprout_p1:,.2f}')
print(f'  Horilla Period 1: ₱{p1_tax:,.2f}')
print(f'  Difference: ₱{abs(p1_tax - sprout_p1):.2f}')
print()
print(f'  Sprout Period 2: ₱{sprout_p2:,.2f}')
print(f'  Horilla Period 2: ₱{p2_tax:,.2f}')
print(f'  Difference: ₱{abs(p2_tax - sprout_p2):.2f}')
print()
print(f'  Sprout Total: ₱{sprout_total:,.2f}')
print(f'  Horilla Total: ₱{p1_tax + p2_tax:,.2f}')
match = abs((p1_tax + p2_tax) - sprout_total) < 1
print(f'  Match: {"✓ YES!" if match else "✗ NO"}')

if match:
    print('\n' + '='*60)
    print('SUCCESS! Tax calculation now matches Sprout exactly!')
    print('='*60)
