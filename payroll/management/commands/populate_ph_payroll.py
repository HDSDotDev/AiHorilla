"""
Management command to populate Philippines payroll data with 2024-2025 rates
"""

from datetime import date
from decimal import Decimal

from django.core.management.base import BaseCommand

from payroll.models.country_models import (
    PayrollCountryConfig,
    PhilippinesCOLA,
    PhilippinesHolidayPay,
    PhilippinesOvertimeRule,
    PhilippinesPagIbigContribution,
    PhilippinesPhilHealthContribution,
    PhilippinesRegion,
    PhilippinesSSSContribution,
    PhilippinesTaxBracket,
    PhilippinesThirteenthMonthPay,
)


class Command(BaseCommand):
    help = 'Populate Philippines payroll data with current 2024-2025 rates'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting Philippines payroll data population...'))

        # Create country config
        self.create_country_config()
        
        # Create regions
        self.create_regions()
        
        # Create SSS contribution table
        self.create_sss_contributions()
        
        # Create PhilHealth contribution table
        self.create_philhealth_contributions()
        
        # Create Pag-IBIG contribution table
        self.create_pagibig_contributions()
        
        # Create tax brackets (TRAIN Law)
        self.create_tax_brackets()
        
        # Create 13th month pay config
        self.create_thirteenth_month_config()
        
        # Create overtime rules
        self.create_overtime_rules()
        
        # Create holiday pay configs
        self.create_holiday_pay()
        
        self.stdout.write(self.style.SUCCESS('Successfully populated Philippines payroll data!'))

    def create_country_config(self):
        """Create Philippines country configuration"""
        config, created = PayrollCountryConfig.objects.get_or_create(
            country='PH',
            defaults={'is_active': False}
        )
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Created Philippines country configuration'))
        else:
            self.stdout.write('• Philippines country configuration already exists')

    def create_regions(self):
        """Create Philippines regions with minimum wage (2024 rates)"""
        regions_data = [
            ('NCR', 'National Capital Region', Decimal('610.00'), Decimal('15860.00')),
            ('Region I', 'Ilocos Region', Decimal('470.00'), Decimal('12220.00')),
            ('Region II', 'Cagayan Valley', Decimal('460.00'), Decimal('11960.00')),
            ('Region III', 'Central Luzon', Decimal('500.00'), Decimal('13000.00')),
            ('Region IV-A', 'CALABARZON', Decimal('570.00'), Decimal('14820.00')),
            ('Region IV-B', 'MIMAROPA', Decimal('435.00'), Decimal('11310.00')),
            ('Region V', 'Bicol Region', Decimal('420.00'), Decimal('10920.00')),
            ('Region VI', 'Western Visayas', Decimal('450.00'), Decimal('11700.00')),
            ('Region VII', 'Central Visayas', Decimal('470.00'), Decimal('12220.00')),
            ('Region VIII', 'Eastern Visayas', Decimal('430.00'), Decimal('11180.00')),
            ('Region IX', 'Zamboanga Peninsula', Decimal('433.00'), Decimal('11258.00')),
            ('Region X', 'Northern Mindanao', Decimal('465.00'), Decimal('12090.00')),
            ('Region XI', 'Davao Region', Decimal('500.00'), Decimal('13000.00')),
            ('Region XII', 'SOCCSKSARGEN', Decimal('450.00'), Decimal('11700.00')),
            ('Region XIII', 'Caraga', Decimal('430.00'), Decimal('11180.00')),
            ('CAR', 'Cordillera Administrative Region', Decimal('460.00'), Decimal('11960.00')),
            ('BARMM', 'Bangsamoro Autonomous Region', Decimal('430.00'), Decimal('11180.00')),
        ]
        
        for code, name, daily, monthly in regions_data:
            region, created = PhilippinesRegion.objects.get_or_create(
                region_code=code,
                defaults={
                    'region_name': name,
                    'daily_minimum_wage': daily,
                    'monthly_minimum_wage': monthly,
                    'effective_date': date(2024, 7, 1)
                }
            )
            if created:
                self.stdout.write(f'  ✓ Created region: {code}')

    def create_sss_contributions(self):
        """Create SSS contribution table (2024 rates)"""
        sss_data = [
            # (min_salary, max_salary, msc, employee, employer, total, ec)
            (Decimal('4250.00'), Decimal('4749.99'), Decimal('4500.00'), Decimal('202.50'), Decimal('427.50'), Decimal('630.00'), Decimal('10.00')),
            (Decimal('4750.00'), Decimal('5249.99'), Decimal('5000.00'), Decimal('225.00'), Decimal('475.00'), Decimal('700.00'), Decimal('10.00')),
            (Decimal('5250.00'), Decimal('5749.99'), Decimal('5500.00'), Decimal('247.50'), Decimal('522.50'), Decimal('770.00'), Decimal('10.00')),
            (Decimal('5750.00'), Decimal('6249.99'), Decimal('6000.00'), Decimal('270.00'), Decimal('570.00'), Decimal('840.00'), Decimal('10.00')),
            (Decimal('6250.00'), Decimal('6749.99'), Decimal('6500.00'), Decimal('292.50'), Decimal('617.50'), Decimal('910.00'), Decimal('10.00')),
            (Decimal('6750.00'), Decimal('7249.99'), Decimal('7000.00'), Decimal('315.00'), Decimal('665.00'), Decimal('980.00'), Decimal('10.00')),
            (Decimal('7250.00'), Decimal('7749.99'), Decimal('7500.00'), Decimal('337.50'), Decimal('712.50'), Decimal('1050.00'), Decimal('10.00')),
            (Decimal('7750.00'), Decimal('8249.99'), Decimal('8000.00'), Decimal('360.00'), Decimal('760.00'), Decimal('1120.00'), Decimal('10.00')),
            (Decimal('8250.00'), Decimal('8749.99'), Decimal('8500.00'), Decimal('382.50'), Decimal('807.50'), Decimal('1190.00'), Decimal('10.00')),
            (Decimal('8750.00'), Decimal('9249.99'), Decimal('9000.00'), Decimal('405.00'), Decimal('855.00'), Decimal('1260.00'), Decimal('10.00')),
            (Decimal('9250.00'), Decimal('9749.99'), Decimal('9500.00'), Decimal('427.50'), Decimal('902.50'), Decimal('1330.00'), Decimal('10.00')),
            (Decimal('9750.00'), Decimal('10249.99'), Decimal('10000.00'), Decimal('450.00'), Decimal('950.00'), Decimal('1400.00'), Decimal('10.00')),
            (Decimal('10250.00'), Decimal('10749.99'), Decimal('10500.00'), Decimal('472.50'), Decimal('997.50'), Decimal('1470.00'), Decimal('10.00')),
            (Decimal('10750.00'), Decimal('11249.99'), Decimal('11000.00'), Decimal('495.00'), Decimal('1045.00'), Decimal('1540.00'), Decimal('10.00')),
            (Decimal('11250.00'), Decimal('11749.99'), Decimal('11500.00'), Decimal('517.50'), Decimal('1092.50'), Decimal('1610.00'), Decimal('10.00')),
            (Decimal('11750.00'), Decimal('12249.99'), Decimal('12000.00'), Decimal('540.00'), Decimal('1140.00'), Decimal('1680.00'), Decimal('10.00')),
            (Decimal('12250.00'), Decimal('12749.99'), Decimal('12500.00'), Decimal('562.50'), Decimal('1187.50'), Decimal('1750.00'), Decimal('10.00')),
            (Decimal('12750.00'), Decimal('13249.99'), Decimal('13000.00'), Decimal('585.00'), Decimal('1235.00'), Decimal('1820.00'), Decimal('10.00')),
            (Decimal('13250.00'), Decimal('13749.99'), Decimal('13500.00'), Decimal('607.50'), Decimal('1282.50'), Decimal('1890.00'), Decimal('10.00')),
            (Decimal('13750.00'), Decimal('14249.99'), Decimal('14000.00'), Decimal('630.00'), Decimal('1330.00'), Decimal('1960.00'), Decimal('10.00')),
            (Decimal('14250.00'), Decimal('14749.99'), Decimal('14500.00'), Decimal('652.50'), Decimal('1377.50'), Decimal('2030.00'), Decimal('10.00')),
            (Decimal('14750.00'), Decimal('15249.99'), Decimal('15000.00'), Decimal('675.00'), Decimal('1425.00'), Decimal('2100.00'), Decimal('10.00')),
            (Decimal('15250.00'), Decimal('15749.99'), Decimal('15500.00'), Decimal('697.50'), Decimal('1472.50'), Decimal('2170.00'), Decimal('10.00')),
            (Decimal('15750.00'), Decimal('16249.99'), Decimal('16000.00'), Decimal('720.00'), Decimal('1520.00'), Decimal('2240.00'), Decimal('10.00')),
            (Decimal('16250.00'), Decimal('16749.99'), Decimal('16500.00'), Decimal('742.50'), Decimal('1567.50'), Decimal('2310.00'), Decimal('10.00')),
            (Decimal('16750.00'), Decimal('17249.99'), Decimal('17000.00'), Decimal('765.00'), Decimal('1615.00'), Decimal('2380.00'), Decimal('10.00')),
            (Decimal('17250.00'), Decimal('17749.99'), Decimal('17500.00'), Decimal('787.50'), Decimal('1662.50'), Decimal('2450.00'), Decimal('10.00')),
            (Decimal('17750.00'), Decimal('18249.99'), Decimal('18000.00'), Decimal('810.00'), Decimal('1710.00'), Decimal('2520.00'), Decimal('10.00')),
            (Decimal('18250.00'), Decimal('18749.99'), Decimal('18500.00'), Decimal('832.50'), Decimal('1757.50'), Decimal('2590.00'), Decimal('10.00')),
            (Decimal('18750.00'), Decimal('19249.99'), Decimal('19000.00'), Decimal('855.00'), Decimal('1805.00'), Decimal('2660.00'), Decimal('10.00')),
            (Decimal('19250.00'), Decimal('19749.99'), Decimal('19500.00'), Decimal('877.50'), Decimal('1852.50'), Decimal('2730.00'), Decimal('10.00')),
            (Decimal('19750.00'), Decimal('20249.99'), Decimal('20000.00'), Decimal('900.00'), Decimal('1900.00'), Decimal('2800.00'), Decimal('10.00')),
            (Decimal('20250.00'), Decimal('20749.99'), Decimal('20500.00'), Decimal('922.50'), Decimal('1947.50'), Decimal('2870.00'), Decimal('10.00')),
            (Decimal('20750.00'), Decimal('21249.99'), Decimal('21000.00'), Decimal('945.00'), Decimal('1995.00'), Decimal('2940.00'), Decimal('10.00')),
            (Decimal('21250.00'), Decimal('21749.99'), Decimal('21500.00'), Decimal('967.50'), Decimal('2042.50'), Decimal('3010.00'), Decimal('10.00')),
            (Decimal('21750.00'), Decimal('22249.99'), Decimal('22000.00'), Decimal('990.00'), Decimal('2090.00'), Decimal('3080.00'), Decimal('10.00')),
            (Decimal('22250.00'), Decimal('22749.99'), Decimal('22500.00'), Decimal('1012.50'), Decimal('2137.50'), Decimal('3150.00'), Decimal('10.00')),
            (Decimal('22750.00'), Decimal('23249.99'), Decimal('23000.00'), Decimal('1035.00'), Decimal('2185.00'), Decimal('3220.00'), Decimal('10.00')),
            (Decimal('23250.00'), Decimal('23749.99'), Decimal('23500.00'), Decimal('1057.50'), Decimal('2232.50'), Decimal('3290.00'), Decimal('10.00')),
            (Decimal('23750.00'), Decimal('24249.99'), Decimal('24000.00'), Decimal('1080.00'), Decimal('2280.00'), Decimal('3360.00'), Decimal('10.00')),
            (Decimal('24250.00'), Decimal('24749.99'), Decimal('24500.00'), Decimal('1102.50'), Decimal('2327.50'), Decimal('3430.00'), Decimal('10.00')),
            (Decimal('24750.00'), Decimal('25249.99'), Decimal('25000.00'), Decimal('1125.00'), Decimal('2375.00'), Decimal('3500.00'), Decimal('10.00')),
            (Decimal('25250.00'), Decimal('25749.99'), Decimal('25500.00'), Decimal('1147.50'), Decimal('2422.50'), Decimal('3570.00'), Decimal('10.00')),
            (Decimal('25750.00'), Decimal('26249.99'), Decimal('26000.00'), Decimal('1170.00'), Decimal('2470.00'), Decimal('3640.00'), Decimal('10.00')),
            (Decimal('26250.00'), Decimal('26749.99'), Decimal('26500.00'), Decimal('1192.50'), Decimal('2517.50'), Decimal('3710.00'), Decimal('10.00')),
            (Decimal('26750.00'), Decimal('27249.99'), Decimal('27000.00'), Decimal('1215.00'), Decimal('2565.00'), Decimal('3780.00'), Decimal('10.00')),
            (Decimal('27250.00'), Decimal('27749.99'), Decimal('27500.00'), Decimal('1237.50'), Decimal('2612.50'), Decimal('3850.00'), Decimal('10.00')),
            (Decimal('27750.00'), Decimal('28249.99'), Decimal('28000.00'), Decimal('1260.00'), Decimal('2660.00'), Decimal('3920.00'), Decimal('10.00')),
            (Decimal('28250.00'), Decimal('28749.99'), Decimal('28500.00'), Decimal('1282.50'), Decimal('2707.50'), Decimal('3990.00'), Decimal('10.00')),
            (Decimal('28750.00'), Decimal('29249.99'), Decimal('29000.00'), Decimal('1305.00'), Decimal('2755.00'), Decimal('4060.00'), Decimal('10.00')),
            (Decimal('29250.00'), Decimal('29749.99'), Decimal('29500.00'), Decimal('1327.50'), Decimal('2802.50'), Decimal('4130.00'), Decimal('10.00')),
            (Decimal('29750.00'), None, Decimal('30000.00'), Decimal('1350.00'), Decimal('2850.00'), Decimal('4200.00'), Decimal('10.00')),
        ]
        
        effective_date = date(2024, 1, 1)
        count = 0
        for data in sss_data:
            _, created = PhilippinesSSSContribution.objects.get_or_create(
                min_salary=data[0],
                max_salary=data[1],
                effective_date=effective_date,
                defaults={
                    'monthly_salary_credit': data[2],
                    'employee_contribution': data[3],
                    'employer_contribution': data[4],
                    'total_contribution': data[5],
                    'ec_contribution': data[6],
                }
            )
            if created:
                count += 1
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {count} SSS contribution brackets'))

    def create_philhealth_contributions(self):
        """Create PhilHealth contribution table (2024 rates - 5%)"""
        philhealth_data = [
            # (min_salary, max_salary, rate%, premium, employee_share, employer_share)
            (Decimal('10000.00'), Decimal('89999.99'), Decimal('5.00'), Decimal('500.00'), Decimal('250.00'), Decimal('250.00')),
            (Decimal('90000.00'), None, Decimal('5.00'), Decimal('4500.00'), Decimal('2250.00'), Decimal('2250.00')),
        ]
        
        effective_date = date(2024, 1, 1)
        count = 0
        for data in philhealth_data:
            _, created = PhilippinesPhilHealthContribution.objects.get_or_create(
                min_salary=data[0],
                max_salary=data[1],
                effective_date=effective_date,
                defaults={
                    'premium_rate': data[2],
                    'monthly_premium': data[3],
                    'employee_share': data[4],
                    'employer_share': data[5],
                }
            )
            if created:
                count += 1
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {count} PhilHealth contribution brackets'))

    def create_pagibig_contributions(self):
        """Create Pag-IBIG contribution table (2024 rates)"""
        pagibig_data = [
            # (min_salary, max_salary, employee_rate%, employer_rate%, employee, employer, total)
            (Decimal('1000.00'), Decimal('1500.00'), Decimal('1.00'), Decimal('2.00'), Decimal('15.00'), Decimal('30.00'), Decimal('45.00')),
            (Decimal('1500.01'), Decimal('5000.00'), Decimal('2.00'), Decimal('2.00'), Decimal('100.00'), Decimal('100.00'), Decimal('200.00')),
            (Decimal('5000.01'), None, Decimal('2.00'), Decimal('2.00'), Decimal('200.00'), Decimal('200.00'), Decimal('400.00')),
        ]
        
        effective_date = date(2024, 1, 1)
        count = 0
        for data in pagibig_data:
            _, created = PhilippinesPagIbigContribution.objects.get_or_create(
                min_salary=data[0],
                max_salary=data[1],
                effective_date=effective_date,
                defaults={
                    'employee_rate': data[2],
                    'employer_rate': data[3],
                    'employee_contribution': data[4],
                    'employer_contribution': data[5],
                    'total_contribution': data[6],
                }
            )
            if created:
                count += 1
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {count} Pag-IBIG contribution brackets'))

    def create_tax_brackets(self):
        """Create Philippines BIR tax brackets based on TRAIN Law"""
        tax_data = [
            # (min_annual, max_annual, base_tax, rate%)
            (Decimal('0.00'), Decimal('250000.00'), Decimal('0.00'), Decimal('0.00')),
            (Decimal('250000.01'), Decimal('400000.00'), Decimal('0.00'), Decimal('15.00')),
            (Decimal('400000.01'), Decimal('800000.00'), Decimal('22500.00'), Decimal('20.00')),
            (Decimal('800000.01'), Decimal('2000000.00'), Decimal('102500.00'), Decimal('25.00')),
            (Decimal('2000000.01'), Decimal('8000000.00'), Decimal('402500.00'), Decimal('30.00')),
            (Decimal('8000000.01'), None, Decimal('2202500.00'), Decimal('35.00')),
        ]
        
        effective_date = date(2024, 1, 1)
        count = 0
        for data in tax_data:
            _, created = PhilippinesTaxBracket.objects.get_or_create(
                min_annual_income=data[0],
                max_annual_income=data[1],
                effective_date=effective_date,
                defaults={
                    'base_tax': data[2],
                    'tax_rate': data[3],
                }
            )
            if created:
                count += 1
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {count} tax brackets (TRAIN Law)'))

    def create_thirteenth_month_config(self):
        """Create 13th month pay configuration"""
        config, created = PhilippinesThirteenthMonthPay.objects.get_or_create(
            year=2024,
            defaults={
                'tax_exempt_amount': Decimal('90000.00'),
                'computation_method': 'total_basic'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Created 13th month pay configuration for 2024'))
        
        config, created = PhilippinesThirteenthMonthPay.objects.get_or_create(
            year=2025,
            defaults={
                'tax_exempt_amount': Decimal('90000.00'),
                'computation_method': 'total_basic'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Created 13th month pay configuration for 2025'))

    def create_overtime_rules(self):
        """Create overtime pay rules"""
        ot_rules = [
            ('regular_day_ot', Decimal('1.25'), 'Regular day overtime - 125% of hourly rate'),
            ('rest_day_ot', Decimal('1.30'), 'Rest day overtime - 130% of hourly rate'),
            ('special_holiday_ot', Decimal('1.30'), 'Special holiday overtime - 130% of hourly rate'),
            ('special_holiday_rest_day_ot', Decimal('1.50'), 'Special holiday + rest day overtime - 150% of hourly rate'),
            ('regular_holiday_ot', Decimal('1.60'), 'Regular holiday overtime - 160% of hourly rate'),
            ('regular_holiday_rest_day_ot', Decimal('2.60'), 'Regular holiday + rest day overtime - 260% of hourly rate'),
            ('night_differential', Decimal('0.10'), 'Night differential (10 PM - 6 AM) - Additional 10% of hourly rate'),
        ]
        
        count = 0
        for ot_type, multiplier, description in ot_rules:
            _, created = PhilippinesOvertimeRule.objects.get_or_create(
                overtime_type=ot_type,
                defaults={
                    'multiplier': multiplier,
                    'description': description
                }
            )
            if created:
                count += 1
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {count} overtime rules'))

    def create_holiday_pay(self):
        """Create 2025 Philippines holidays"""
        holidays_2025 = [
            (date(2025, 1, 1), 'New Year\'s Day', 'regular', Decimal('2.00')),
            (date(2025, 2, 25), 'EDSA People Power Revolution Anniversary', 'special', Decimal('1.30')),
            (date(2025, 4, 9), 'Araw ng Kagitingan (Day of Valor)', 'regular', Decimal('2.00')),
            (date(2025, 4, 17), 'Maundy Thursday', 'regular', Decimal('2.00')),
            (date(2025, 4, 18), 'Good Friday', 'regular', Decimal('2.00')),
            (date(2025, 4, 19), 'Black Saturday', 'special', Decimal('1.30')),
            (date(2025, 5, 1), 'Labor Day', 'regular', Decimal('2.00')),
            (date(2025, 6, 12), 'Independence Day', 'regular', Decimal('2.00')),
            (date(2025, 8, 21), 'Ninoy Aquino Day', 'special', Decimal('1.30')),
            (date(2025, 8, 25), 'National Heroes Day', 'regular', Decimal('2.00')),
            (date(2025, 11, 1), 'All Saints\' Day', 'special', Decimal('1.30')),
            (date(2025, 11, 30), 'Bonifacio Day', 'regular', Decimal('2.00')),
            (date(2025, 12, 8), 'Feast of the Immaculate Conception of Mary', 'special', Decimal('1.30')),
            (date(2025, 12, 25), 'Christmas Day', 'regular', Decimal('2.00')),
            (date(2025, 12, 30), 'Rizal Day', 'regular', Decimal('2.00')),
            (date(2025, 12, 31), 'Last Day of the Year', 'special', Decimal('1.30')),
        ]
        
        count = 0
        for holiday_date, name, hol_type, multiplier in holidays_2025:
            _, created = PhilippinesHolidayPay.objects.get_or_create(
                holiday_date=holiday_date,
                defaults={
                    'holiday_name': name,
                    'holiday_type': hol_type,
                    'pay_multiplier': multiplier
                }
            )
            if created:
                count += 1
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {count} holiday pay configurations for 2025'))
