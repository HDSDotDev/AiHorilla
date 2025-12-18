"""
Populate Philippines Government Deduction Tables (2025 Rates)
SSS, PhilHealth, Pag-IBIG, and BIR Tax Brackets
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horilla.settings')
django.setup()

from payroll.models import (
    PhilippinesSSSContribution,
    PhilippinesPhilHealthContribution,
    PhilippinesPagIbigContribution,
    PhilippinesTaxBracket
)
from decimal import Decimal
from datetime import date

def populate_sss_contributions():
    """SSS Contribution Table (2025) - Employee share only"""
    print("Populating SSS Contributions...")
    
    sss_brackets = [
        # (min_salary, max_salary, msc, employee_contribution, employer_contribution, total, ec)
        (0, 4249.99, 4000, 180.00, 380.00, 560.00, 10.00),
        (4250, 4749.99, 4500, 202.50, 427.50, 630.00, 10.00),
        (4750, 5249.99, 5000, 225.00, 475.00, 700.00, 10.00),
        (5250, 5749.99, 5500, 247.50, 522.50, 770.00, 10.00),
        (5750, 6249.99, 6000, 270.00, 570.00, 840.00, 10.00),
        (6250, 6749.99, 6500, 292.50, 617.50, 910.00, 10.00),
        (6750, 7249.99, 7000, 315.00, 665.00, 980.00, 10.00),
        (7250, 7749.99, 7500, 337.50, 712.50, 1050.00, 10.00),
        (7750, 8249.99, 8000, 360.00, 760.00, 1120.00, 10.00),
        (8250, 8749.99, 8500, 382.50, 807.50, 1190.00, 10.00),
        (8750, 9249.99, 9000, 405.00, 855.00, 1260.00, 10.00),
        (9250, 9749.99, 9500, 427.50, 902.50, 1330.00, 10.00),
        (9750, 10249.99, 10000, 450.00, 950.00, 1400.00, 10.00),
        (10250, 10749.99, 10500, 472.50, 997.50, 1470.00, 10.00),
        (10750, 11249.99, 11000, 495.00, 1045.00, 1540.00, 10.00),
        (11250, 11749.99, 11500, 517.50, 1092.50, 1610.00, 10.00),
        (11750, 12249.99, 12000, 540.00, 1140.00, 1680.00, 10.00),
        (12250, 12749.99, 12500, 562.50, 1187.50, 1750.00, 10.00),
        (12750, 13249.99, 13000, 585.00, 1235.00, 1820.00, 10.00),
        (13250, 13749.99, 13500, 607.50, 1282.50, 1890.00, 10.00),
        (13750, 14249.99, 14000, 630.00, 1330.00, 1960.00, 10.00),
        (14250, 14749.99, 14500, 652.50, 1377.50, 2030.00, 10.00),
        (14750, 15249.99, 15000, 675.00, 1425.00, 2100.00, 10.00),
        (15250, 15749.99, 15500, 697.50, 1472.50, 2170.00, 10.00),
        (15750, 16249.99, 16000, 720.00, 1520.00, 2240.00, 10.00),
        (16250, 16749.99, 16500, 742.50, 1567.50, 2310.00, 10.00),
        (16750, 17249.99, 17000, 765.00, 1615.00, 2380.00, 10.00),
        (17250, 17749.99, 17500, 787.50, 1662.50, 2450.00, 10.00),
        (17750, 18249.99, 18000, 810.00, 1710.00, 2520.00, 10.00),
        (18250, 18749.99, 18500, 832.50, 1757.50, 2590.00, 10.00),
        (18750, 19249.99, 19000, 855.00, 1805.00, 2660.00, 10.00),
        (19250, 19749.99, 19500, 877.50, 1852.50, 2730.00, 10.00),
        (19750, 20249.99, 20000, 900.00, 1900.00, 2800.00, 10.00),
        (20250, 20749.99, 20500, 922.50, 1947.50, 2870.00, 10.00),
        (20750, 21249.99, 21000, 945.00, 1995.00, 2940.00, 10.00),
        (21250, 21749.99, 21500, 967.50, 2042.50, 3010.00, 10.00),
        (21750, 22249.99, 22000, 990.00, 2090.00, 3080.00, 10.00),
        (22250, 22749.99, 22500, 1012.50, 2137.50, 3150.00, 10.00),
        (22750, 23249.99, 23000, 1035.00, 2185.00, 3220.00, 10.00),
        (23250, 23749.99, 23500, 1057.50, 2232.50, 3290.00, 10.00),
        (23750, 24249.99, 24000, 1080.00, 2280.00, 3360.00, 10.00),
        (24250, 24749.99, 24500, 1102.50, 2327.50, 3430.00, 10.00),
        (24750, 29999.99, 25000, 1125.00, 2375.00, 3500.00, 10.00),
        (30000, 999999.99, 30000, 1125.00, 2375.00, 3500.00, 10.00),  # Maximum ceiling
    ]
    
    effective = date(2025, 1, 1)
    
    for min_sal, max_sal, msc, emp_cont, empr_cont, total, ec in sss_brackets:
        PhilippinesSSSContribution.objects.get_or_create(
            min_salary=Decimal(str(min_sal)),
            max_salary=Decimal(str(max_sal)),
            defaults={
                'monthly_salary_credit': Decimal(str(msc)),
                'employee_contribution': Decimal(str(emp_cont)),
                'employer_contribution': Decimal(str(empr_cont)),
                'total_contribution': Decimal(str(total)),
                'ec_contribution': Decimal(str(ec)),
                'effective_date': effective
            }
        )
    
    count = PhilippinesSSSContribution.objects.count()
    print(f"✓ Created {count} SSS contribution brackets")


def populate_philhealth_contributions():
    """PhilHealth Contribution Table (2025) - 5% premium rate"""
    print("Populating PhilHealth Contributions...")
    
    philhealth_brackets = [
        # (min_salary, max_salary, premium_rate %, monthly_premium, employee_share, employer_share)
        (0, 10000, 5.0, 1000.00, 500.00, 500.00),  # Minimum
        (10001, 100000, 5.0, 0, 0, 0),  # 5% of basic salary (calculated dynamically)
        (100001, 999999, 5.0, 10000.00, 5000.00, 5000.00),  # Maximum ceiling
    ]
    
    effective = date(2025, 1, 1)
    
    for min_sal, max_sal, rate, monthly_prem, emp_share, empr_share in philhealth_brackets:
        PhilippinesPhilHealthContribution.objects.get_or_create(
            min_salary=Decimal(str(min_sal)),
            max_salary=Decimal(str(max_sal)),
            defaults={
                'premium_rate': Decimal(str(rate)),
                'monthly_premium': Decimal(str(monthly_prem)),
                'employee_share': Decimal(str(emp_share)),
                'employer_share': Decimal(str(empr_share)),
                'effective_date': effective
            }
        )
    
    count = PhilippinesPhilHealthContribution.objects.count()
    print(f"✓ Created {count} PhilHealth contribution brackets")


def populate_pagibig_contributions():
    """Pag-IBIG Contribution Table (2025) - 2% employee, 2% employer"""
    print("Populating Pag-IBIG Contributions...")
    
    pagibig_brackets = [
        # (min_salary, max_salary, employee_rate %, employee_cont, employer_rate %, employer_cont, total)
        (0, 1500, 1.0, 0, 2.0, 0, 0),  # 1% employee, 2% employer (calculated)
        (1500.01, 5000, 2.0, 0, 2.0, 0, 0),  # 2% both (calculated)
        (5000.01, 999999, 2.0, 100.00, 2.0, 100.00, 200.00),  # Maximum ₱100 each
    ]
    
    effective = date(2025, 1, 1)
    
    for min_sal, max_sal, emp_rate, emp_cont, empr_rate, empr_cont, total in pagibig_brackets:
        PhilippinesPagIbigContribution.objects.get_or_create(
            min_salary=Decimal(str(min_sal)),
            max_salary=Decimal(str(max_sal)),
            defaults={
                'employee_rate': Decimal(str(emp_rate)),
                'employee_contribution': Decimal(str(emp_cont)),
                'employer_rate': Decimal(str(empr_rate)),
                'employer_contribution': Decimal(str(empr_cont)),
                'total_contribution': Decimal(str(total)),
                'effective_date': effective
            }
        )
    
    count = PhilippinesPagIbigContribution.objects.count()
    print(f"✓ Created {count} Pag-IBIG contribution brackets")


def populate_tax_brackets():
    """BIR Withholding Tax Table (2025) - TRAIN Law - SEMI-MONTHLY"""
    print("Populating BIR Tax Brackets (Semi-Monthly)...")
    
    # SEMI-MONTHLY tax brackets as used by Sprout
    # This is the DIRECT bracket approach - NOT annualized
    tax_brackets = [
        # (min_semimonthly, max_semimonthly, base_tax, tax_rate %)
        (0, 10417, 0, 0),  # ≤ 10,417: 0
        (10417, 16666, 0, 15),  # (TI − 10,417) × 15%
        (16667, 33332, 937.50, 20),  # 937.50 + (TI − 16,667) × 20%
        (33333, 83332, 4270.70, 25),  # 4,270.70 + (TI − 33,333) × 25%
        (83333, 333332, 16770.70, 30),  # 16,770.70 + (TI − 83,333) × 30%
        (333333, 999999999, 91770.70, 35),  # 91,770.70 + (TI − 333,333) × 35%
    ]
    
    effective = date(2025, 1, 1)
    
    # Clear old annual brackets first
    PhilippinesTaxBracket.objects.all().delete()
    print("  Cleared old annual tax brackets")
    
    for min_income, max_income, base_tax, rate in tax_brackets:
        PhilippinesTaxBracket.objects.create(
            min_annual_income=Decimal(str(min_income)),
            max_annual_income=Decimal(str(max_income)),
            base_tax=Decimal(str(base_tax)),
            tax_rate=Decimal(str(rate)),
            effective_date=effective
        )
    
    count = PhilippinesTaxBracket.objects.count()
    print(f"✓ Created {count} BIR semi-monthly tax brackets")


if __name__ == '__main__':
    print("=" * 60)
    print("POPULATING PHILIPPINES GOVERNMENT DEDUCTION TABLES")
    print("=" * 60)
    
    populate_sss_contributions()
    populate_philhealth_contributions()
    populate_pagibig_contributions()
    populate_tax_brackets()
    
    print("=" * 60)
    print("✓ ALL TABLES POPULATED SUCCESSFULLY!")
    print("=" * 60)
    
    # Summary
    print("\nSummary:")
    print(f"  SSS Brackets: {PhilippinesSSSContribution.objects.count()}")
    print(f"  PhilHealth Brackets: {PhilippinesPhilHealthContribution.objects.count()}")
    print(f"  Pag-IBIG Brackets: {PhilippinesPagIbigContribution.objects.count()}")
    print(f"  BIR Tax Brackets: {PhilippinesTaxBracket.objects.count()}")
    print("\nYou can now generate payslips with proper deductions!")
