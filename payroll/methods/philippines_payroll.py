"""
philippines_payroll.py

Computation methods for Philippines payroll system
Implements BIR (Bureau of Internal Revenue) tax calculations,
SSS, PhilHealth, Pag-IBIG contributions, and other PH labor law requirements
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Dict, Optional, Tuple

from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from employee.models import Employee
from payroll.models.country_models import (
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


class PhilippinesPayrollCalculator:
    """
    Main calculator class for Philippines payroll computations
    
    Supports both monthly and semi-monthly pay periods
    """

    def __init__(self, employee: Employee, basic_salary: Decimal, period_start: date, period_end: date, 
                 pay_period: str = 'monthly'):
        """
        Initialize payroll calculator
        
        Args:
            employee: Employee instance
            basic_salary: Monthly basic salary (even for semi-monthly, pass full monthly amount)
            period_start: Payroll period start date
            period_end: Payroll period end date
            pay_period: 'monthly', 'semi_monthly_first', or 'semi_monthly_second'
        """
        self.employee = employee
        self.basic_salary = Decimal(str(basic_salary))
        self.period_start = period_start
        self.period_end = period_end
        self.computation_date = date.today()
        self.pay_period = pay_period  # 'monthly', 'semi_monthly_first', 'semi_monthly_second'

    def get_sss_contribution(self) -> Dict[str, Decimal]:
        """
        Calculate SSS contribution based on monthly salary
        Returns dict with employee, employer, and EC contributions
        """
        # Get the applicable SSS contribution table
        # Order by effective_date DESC, then min_salary DESC to get the most recent and closest bracket
        sss_table = PhilippinesSSSContribution.objects.filter(
            effective_date__lte=self.computation_date,
            min_salary__lte=self.basic_salary
        ).filter(
            Q(max_salary__gte=self.basic_salary) | Q(max_salary__isnull=True)
        ).order_by('-effective_date', '-min_salary').first()

        if not sss_table:
            # If no table found, use minimum or return zero
            return {
                'employee_contribution': Decimal('0.00'),
                'employer_contribution': Decimal('0.00'),
                'ec_contribution': Decimal('0.00'),
                'total_contribution': Decimal('0.00'),
                'monthly_salary_credit': Decimal('0.00')
            }

        return {
            'employee_contribution': sss_table.employee_contribution,
            'employer_contribution': sss_table.employer_contribution,
            'ec_contribution': sss_table.ec_contribution,
            'total_contribution': sss_table.total_contribution,
            'monthly_salary_credit': sss_table.monthly_salary_credit
        }

    def get_philhealth_contribution(self) -> Dict[str, Decimal]:
        """
        Calculate PhilHealth contribution based on monthly salary
        Returns dict with employee and employer shares
        
        PhilHealth 2024 regulations:
        - Premium Rate: 5% of basic salary
        - Salary Floor: ₱10,000 (minimum for calculation)
        - Salary Ceiling: ₱100,000 (maximum for calculation)
        - Maximum Premium: ₱5,000/month (₱100,000 × 5%)
        - Minimum Premium: ₱500/month (₱10,000 × 5%)
        - Employee Share: 50% (₱2,500 max, ₱250 min)
        - Employer Share: 50% (₱2,500 max, ₱250 min)
        """
        philhealth_table = PhilippinesPhilHealthContribution.objects.filter(
            effective_date__lte=self.computation_date,
            min_salary__lte=self.basic_salary
        ).filter(
            Q(max_salary__gte=self.basic_salary) | Q(max_salary__isnull=True)
        ).order_by('-effective_date').first()

        if not philhealth_table:
            # Apply salary floor and ceiling per PhilHealth regulations
            salary_floor = Decimal('10000.00')  # Minimum ₱10,000
            salary_ceiling = Decimal('100000.00')  # Maximum ₱100,000
            
            # Clamp salary between floor and ceiling
            clamped_salary = max(salary_floor, min(self.basic_salary, salary_ceiling))
            
            # Calculate 5% premium
            premium_rate = Decimal('0.05')  # 5%
            monthly_premium = clamped_salary * premium_rate
            
            # Split 50/50 between employee and employer
            employee_share = monthly_premium / 2  # Min ₱250, Max ₱2,500
            employer_share = monthly_premium / 2  # Min ₱250, Max ₱2,500

            return {
                'employee_share': employee_share.quantize(Decimal('0.01')),
                'employer_share': employer_share.quantize(Decimal('0.01')),
                'monthly_premium': monthly_premium.quantize(Decimal('0.01')),
                'premium_rate': premium_rate,
                'salary_used': clamped_salary.quantize(Decimal('0.01'))
            }

        return {
            'employee_share': philhealth_table.employee_share,
            'employer_share': philhealth_table.employer_share,
            'monthly_premium': philhealth_table.monthly_premium,
            'premium_rate': philhealth_table.premium_rate
        }

    def get_pagibig_contribution(self) -> Dict[str, Decimal]:
        """
        Calculate Pag-IBIG contribution based on monthly salary
        Returns dict with employee and employer contributions
        
        Pag-IBIG 2024 rates (per HDMF regulations):
        - ₱1,000 and below: 1% employee, 2% employer
        - ₱1,000.01 to ₱1,500: 2% employee, 2% employer
        - ₱1,500.01 and above: 2% employee, 2% employer (max ₱100 each)
        - Salary cap: ₱5,000 maximum for calculation base
        """
        pagibig_table = PhilippinesPagIbigContribution.objects.filter(
            effective_date__lte=self.computation_date,
            min_salary__lte=self.basic_salary
        ).filter(
            Q(max_salary__gte=self.basic_salary) | Q(max_salary__isnull=True)
        ).order_by('-effective_date').first()

        if not pagibig_table:
            # Apply salary cap (₱5,000 maximum compensation for calculation)
            salary_for_calculation = min(self.basic_salary, Decimal('5000.00'))
            
            # Apply tiered rate structure per HDMF regulations
            if salary_for_calculation <= Decimal('1000.00'):
                # Tier 1: ₱1,000 and below
                employee_rate = Decimal('0.01')  # 1%
                employer_rate = Decimal('0.02')  # 2%
                
            elif salary_for_calculation <= Decimal('1500.00'):
                # Tier 2: ₱1,000.01 to ₱1,500
                employee_rate = Decimal('0.02')  # 2%
                employer_rate = Decimal('0.02')  # 2%
                
            else:
                # Tier 3: ₱1,500.01 and above
                employee_rate = Decimal('0.02')  # 2%
                employer_rate = Decimal('0.02')  # 2%
            
            # Calculate contributions
            employee_contribution = min(
                salary_for_calculation * employee_rate,
                Decimal('100.00')  # MAXIMUM ₱100 employee contribution
            )
            employer_contribution = min(
                salary_for_calculation * employer_rate,
                Decimal('100.00')  # MAXIMUM ₱100 employer contribution
            )

            return {
                'employee_contribution': employee_contribution.quantize(Decimal('0.01')),
                'employer_contribution': employer_contribution.quantize(Decimal('0.01')),
                'total_contribution': (employee_contribution + employer_contribution).quantize(Decimal('0.01')),
                'employee_rate': employee_rate,
                'employer_rate': employer_rate,
                'salary_used': salary_for_calculation.quantize(Decimal('0.01'))
            }

        return {
            'employee_contribution': pagibig_table.employee_contribution,
            'employer_contribution': pagibig_table.employer_contribution,
            'total_contribution': pagibig_table.total_contribution,
            'employee_rate': pagibig_table.employee_rate,
            'employer_rate': pagibig_table.employer_rate
        }

    def calculate_withholding_tax(
        self,
        taxable_income: Decimal,
        thirteenth_month_pay: Decimal = Decimal('0.00'),
        num_dependents: int = 0
    ) -> Dict[str, Decimal]:
        """
        Calculate withholding tax based on TRAIN Law (Tax Reform for Acceleration and Inclusion)
        
        Tax Exemptions (as of 2024):
        - Personal exemption: ₱50,000/year
        - Additional exemption per dependent: ₱25,000/year (maximum 4 dependents)
        
        Args:
            taxable_income: Monthly taxable income
            thirteenth_month_pay: 13th month pay amount (exempt up to ₱90,000/year)
            num_dependents: Number of qualified dependents (max 4)
        
        Returns:
            Dict with tax details
        """
        # Convert monthly to annual income
        annual_taxable_income = taxable_income * 12

        # Apply tax exemptions per BIR regulations
        personal_exemption = Decimal('50000.00')  # ₱50,000 personal exemption
        dependent_exemption = Decimal('25000.00')  # ₱25,000 per dependent
        max_dependents = min(num_dependents, 4)  # Maximum 4 dependents
        
        total_exemptions = personal_exemption + (dependent_exemption * max_dependents)

        # Handle 13th month pay exemption (₱90,000 max)
        thirteenth_month_config = PhilippinesThirteenthMonthPay.objects.filter(
            year=self.period_end.year
        ).first()
        
        tax_exempt_13th_month = Decimal('90000.00')
        if thirteenth_month_config:
            tax_exempt_13th_month = thirteenth_month_config.tax_exempt_amount

        # Taxable portion of 13th month pay
        taxable_13th_month = max(Decimal('0.00'), thirteenth_month_pay - tax_exempt_13th_month)
        
        # Calculate total taxable income after exemptions
        gross_annual_taxable = annual_taxable_income + taxable_13th_month
        total_annual_taxable = max(Decimal('0.00'), gross_annual_taxable - total_exemptions)

        # Get applicable tax bracket
        tax_bracket = PhilippinesTaxBracket.objects.filter(
            effective_date__lte=self.computation_date,
            min_annual_income__lte=total_annual_taxable
        ).filter(
            Q(max_annual_income__gte=total_annual_taxable) | Q(max_annual_income__isnull=True)
        ).order_by('-effective_date', 'min_annual_income').first()

        if not tax_bracket:
            # No tax if income is below minimum threshold
            return {
                'monthly_tax': Decimal('0.00'),
                'annual_tax': Decimal('0.00'),
                'tax_rate': Decimal('0.00'),
                'base_tax': Decimal('0.00'),
                'excess_tax': Decimal('0.00'),
                'personal_exemption': personal_exemption,
                'dependent_exemption': dependent_exemption * max_dependents,
                'total_exemptions': total_exemptions,
                'num_dependents': max_dependents
            }

        # Calculate tax
        excess_income = total_annual_taxable - tax_bracket.min_annual_income
        tax_on_excess = excess_income * (tax_bracket.tax_rate / 100)
        total_annual_tax = tax_bracket.base_tax + tax_on_excess
        monthly_tax = (total_annual_tax / 12).quantize(Decimal('0.01'))

        return {
            'monthly_tax': monthly_tax,
            'annual_tax': total_annual_tax.quantize(Decimal('0.01')),
            'tax_rate': tax_bracket.tax_rate,
            'base_tax': tax_bracket.base_tax,
            'excess_tax': tax_on_excess.quantize(Decimal('0.01')),
            'taxable_income': total_annual_taxable.quantize(Decimal('0.01')),
            'gross_taxable_income': gross_annual_taxable.quantize(Decimal('0.01')),
            'personal_exemption': personal_exemption,
            'dependent_exemption': dependent_exemption * max_dependents,
            'total_exemptions': total_exemptions,
            'num_dependents': max_dependents
        }

    def calculate_thirteenth_month_pay(
        self,
        total_basic_salary_ytd: Decimal,
        months_worked: int = 12
    ) -> Dict[str, Decimal]:
        """
        Calculate 13th month pay
        
        Args:
            total_basic_salary_ytd: Total basic salary for the year
            months_worked: Number of months worked in the year
        
        Returns:
            Dict with 13th month pay details
        """
        config = PhilippinesThirteenthMonthPay.objects.filter(
            year=datetime.now().year
        ).first()

        if config and config.computation_method == 'prorated':
            # Prorated based on months worked
            thirteenth_month = (total_basic_salary_ytd / 12) * (months_worked / 12)
        else:
            # Standard: Total basic salary / 12
            thirteenth_month = total_basic_salary_ytd / 12

        # Tax-exempt amount
        tax_exempt_limit = Decimal('90000.00')
        if config:
            tax_exempt_limit = config.tax_exempt_amount

        taxable_portion = max(Decimal('0.00'), thirteenth_month - tax_exempt_limit)
        tax_exempt_portion = min(thirteenth_month, tax_exempt_limit)

        return {
            'thirteenth_month_pay': thirteenth_month.quantize(Decimal('0.01')),
            'tax_exempt_portion': tax_exempt_portion.quantize(Decimal('0.01')),
            'taxable_portion': taxable_portion.quantize(Decimal('0.01')),
            'months_worked': months_worked
        }

    def validate_minimum_wage(self, region_code: str = None) -> Dict[str, any]:
        """
        Validate that employee's salary meets minimum wage requirements
        
        Args:
            region_code: Philippines region code (e.g., 'NCR', 'Region I')
            
        Returns:
            Dict with validation result
        """
        if not region_code:
            # Try to get from employee record
            region_code = getattr(self.employee, 'ph_region', None) or \
                         getattr(self.employee, 'philippines_region', None)
        
        if not region_code:
            return {
                'is_compliant': None,
                'message': 'No region assigned to employee - cannot validate minimum wage'
            }
        
        try:
            region = PhilippinesRegion.objects.filter(region_code=region_code).first()
            if not region:
                return {
                    'is_compliant': None,
                    'message': f'Region {region_code} not found in database'
                }
            
            daily_rate = self.get_daily_rate()
            
            if daily_rate < region.daily_minimum_wage:
                return {
                    'is_compliant': False,
                    'employee_daily_rate': daily_rate,
                    'minimum_required': region.daily_minimum_wage,
                    'shortfall': region.daily_minimum_wage - daily_rate,
                    'message': f'Salary below minimum wage for {region.region_name}. '
                              f'Employee: ₱{daily_rate:.2f}/day, Minimum: ₱{region.daily_minimum_wage:.2f}/day'
                }
            else:
                return {
                    'is_compliant': True,
                    'employee_daily_rate': daily_rate,
                    'minimum_required': region.daily_minimum_wage,
                    'message': f'Salary meets minimum wage for {region.region_name}'
                }
        except Exception as e:
            return {
                'is_compliant': None,
                'message': f'Error validating minimum wage: {str(e)}'
            }
    
    def get_daily_rate(self) -> Decimal:
        """
        Calculate daily rate per DOLE/Labor Code standards
        
        For monthly-paid employees:
        Daily rate = (Monthly Basic × 12 months) ÷ 261 working days/year
        
        This is the CORRECT formula per Philippine Labor Code
        """
        # Standard annual working days in Philippines (excludes weekends and holidays)
        annual_working_days = Decimal('261')
        daily_rate = (self.basic_salary * 12) / annual_working_days
        return daily_rate.quantize(Decimal('0.01'))
    
    def get_hourly_rate(self) -> Decimal:
        """
        Calculate hourly rate per DOLE/Labor Code standards
        
        Hourly rate = Daily rate ÷ 8 hours
        """
        daily_rate = self.get_daily_rate()
        hourly_rate = daily_rate / Decimal('8')
        return hourly_rate.quantize(Decimal('0.01'))

    def calculate_overtime_pay(
        self,
        overtime_hours: Decimal,
        overtime_type: str = 'regular_day_ot'
    ) -> Dict[str, Decimal]:
        """
        Calculate overtime pay based on Philippines Labor Code
        
        Args:
            overtime_hours: Number of overtime hours
            overtime_type: Type of overtime (regular_day_ot, rest_day_ot, etc.)
        
        Returns:
            Dict with overtime pay details
        """
        # Use proper daily and hourly rate calculations
        daily_rate = self.get_daily_rate()
        hourly_rate = self.get_hourly_rate()

        # Get overtime rule
        ot_rule = PhilippinesOvertimeRule.objects.filter(
            overtime_type=overtime_type
        ).first()

        if not ot_rule:
            # Default multipliers
            multipliers = {
                'regular_day_ot': Decimal('1.25'),
                'rest_day_ot': Decimal('1.30'),
                'special_holiday_ot': Decimal('1.30'),
                'special_holiday_rest_day_ot': Decimal('1.50'),
                'regular_holiday_ot': Decimal('1.60'),
                'regular_holiday_rest_day_ot': Decimal('2.60'),
                'night_differential': Decimal('0.10'),
            }
            multiplier = multipliers.get(overtime_type, Decimal('1.25'))
        else:
            multiplier = ot_rule.multiplier

        # Calculate overtime pay
        if overtime_type == 'night_differential':
            # Night differential is ADDITIONAL 10% on top of regular or OT pay
            # If working night shift without OT: regular pay + 10%
            # If working night shift WITH OT: OT pay + 10%
            # For this calculator, we return the 10% additional amount
            night_diff_pay = overtime_hours * hourly_rate * Decimal('0.10')
            ot_pay = night_diff_pay
        else:
            # Regular overtime calculation
            ot_pay = overtime_hours * hourly_rate * multiplier

        return {
            'overtime_pay': ot_pay.quantize(Decimal('0.01')),
            'overtime_hours': overtime_hours,
            'hourly_rate': hourly_rate,
            'multiplier': multiplier,
            'overtime_type': overtime_type,
            'daily_rate': daily_rate
        }

    def calculate_holiday_pay(
        self,
        holiday_date: date,
        worked: bool = False
    ) -> Dict[str, Decimal]:
        """
        Calculate holiday pay per Labor Code
        
        Args:
            holiday_date: Date of the holiday
            worked: Whether employee worked on the holiday
        
        Returns:
            Dict with holiday pay details
        """
        holiday = PhilippinesHolidayPay.objects.filter(
            holiday_date=holiday_date
        ).first()

        if not holiday:
            return {
                'holiday_pay': Decimal('0.00'),
                'is_holiday': False
            }

        # Use proper daily rate calculation
        daily_rate = self.get_daily_rate()

        if worked:
            # If worked on holiday, pay is multiplied
            holiday_pay = daily_rate * holiday.pay_multiplier
        else:
            # If not worked but holiday, still get regular pay (for regular holidays)
            if holiday.holiday_type == 'regular':
                holiday_pay = daily_rate
            else:
                holiday_pay = Decimal('0.00')

        return {
            'holiday_pay': holiday_pay.quantize(Decimal('0.01')),
            'is_holiday': True,
            'holiday_name': holiday.holiday_name,
            'holiday_type': holiday.holiday_type,
            'worked': worked,
            'multiplier': holiday.pay_multiplier if worked else Decimal('1.00')
        }

    def calculate_cola(self, region_code: str, working_days: int = 22) -> Dict[str, Decimal]:
        """
        Calculate Cost of Living Allowance
        
        Args:
            region_code: Region code (e.g., 'NCR', 'Region I')
            working_days: Number of working days in the period
        
        Returns:
            Dict with COLA details
        """
        region = PhilippinesRegion.objects.filter(region_code=region_code).first()
        
        if not region:
            return {
                'cola': Decimal('0.00'),
                'is_taxable': False
            }

        cola_config = PhilippinesCOLA.objects.filter(
            region=region,
            effective_date__lte=self.computation_date
        ).order_by('-effective_date').first()

        if not cola_config:
            return {
                'cola': Decimal('0.00'),
                'is_taxable': False
            }

        # Calculate monthly COLA based on working days
        monthly_cola = cola_config.daily_cola * working_days

        return {
            'cola': monthly_cola.quantize(Decimal('0.01')),
            'daily_cola': cola_config.daily_cola,
            'working_days': working_days,
            'is_taxable': cola_config.is_taxable,
            'region': region_code
        }

    def get_semi_monthly_adjustments(self) -> Dict[str, any]:
        """
        Get adjustments for semi-monthly payroll
        
        Government contributions (SSS, PhilHealth, Pag-IBIG) are deducted ONCE per month,
        typically in the 2nd payroll. Basic pay is split in half.
        
        Returns:
            Dict with adjustment factors
        """
        if self.pay_period == 'semi_monthly_first':
            # 1st half of month: Half basic pay, NO government contributions
            return {
                'basic_pay_factor': Decimal('0.5'),  # 50% of monthly
                'deduct_sss': False,
                'deduct_philhealth': False,
                'deduct_pagibig': False,
                'deduct_tax': True,  # Tax is split equally
                'tax_factor': Decimal('0.5')  # 50% of monthly tax
            }
        elif self.pay_period == 'semi_monthly_second':
            # 2nd half of month: Half basic pay, FULL government contributions
            return {
                'basic_pay_factor': Decimal('0.5'),  # 50% of monthly
                'deduct_sss': True,  # FULL month's contribution
                'deduct_philhealth': True,  # FULL month's contribution
                'deduct_pagibig': True,  # FULL month's contribution
                'deduct_tax': True,  # Remaining tax
                'tax_factor': Decimal('0.5')  # 50% of monthly tax
            }
        else:
            # Monthly: Everything at 100%
            return {
                'basic_pay_factor': Decimal('1.0'),
                'deduct_sss': True,
                'deduct_philhealth': True,
                'deduct_pagibig': True,
                'deduct_tax': True,
                'tax_factor': Decimal('1.0')
            }
    
    def calculate_net_pay(
        self,
        gross_pay: Decimal,
        sss: Optional[Decimal] = None,
        philhealth: Optional[Decimal] = None,
        pagibig: Optional[Decimal] = None,
        withholding_tax: Optional[Decimal] = None,
        other_deductions: Decimal = Decimal('0.00')
    ) -> Dict[str, Decimal]:
        """
        Calculate net pay with support for semi-monthly payroll
        
        Args:
            gross_pay: Gross pay for the period
            sss: SSS employee contribution (calculated if not provided)
            philhealth: PhilHealth employee share (calculated if not provided)
            pagibig: Pag-IBIG employee contribution (calculated if not provided)
            withholding_tax: Withholding tax (calculated if not provided)
            other_deductions: Other deductions
        
        Returns:
            Dict with net pay breakdown
        """
        # Get semi-monthly adjustments
        adjustments = self.get_semi_monthly_adjustments()
        
        # Calculate mandatory deductions if not provided
        if sss is None:
            sss_full = self.get_sss_contribution()['employee_contribution']
            sss = sss_full if adjustments['deduct_sss'] else Decimal('0.00')
        
        if philhealth is None:
            philhealth_full = self.get_philhealth_contribution()['employee_share']
            philhealth = philhealth_full if adjustments['deduct_philhealth'] else Decimal('0.00')
        
        if pagibig is None:
            pagibig_full = self.get_pagibig_contribution()['employee_contribution']
            pagibig = pagibig_full if adjustments['deduct_pagibig'] else Decimal('0.00')

        # Calculate taxable income (gross - non-taxable deductions)
        # For tax calculation, always use FULL monthly amounts then apply factor
        if self.pay_period.startswith('semi_monthly'):
            # Calculate monthly taxable income then split
            monthly_gross = gross_pay / adjustments['basic_pay_factor']
            monthly_sss = sss if adjustments['deduct_sss'] else sss_full if 'sss_full' in locals() else self.get_sss_contribution()['employee_contribution']
            monthly_philhealth = philhealth if adjustments['deduct_philhealth'] else philhealth_full if 'philhealth_full' in locals() else self.get_philhealth_contribution()['employee_share']
            monthly_pagibig = pagibig if adjustments['deduct_pagibig'] else pagibig_full if 'pagibig_full' in locals() else self.get_pagibig_contribution()['employee_contribution']
            
            monthly_taxable = monthly_gross - monthly_sss - monthly_philhealth - monthly_pagibig
            
            if withholding_tax is None:
                tax_result = self.calculate_withholding_tax(monthly_taxable)
                monthly_tax = tax_result['monthly_tax']
                withholding_tax = (monthly_tax * adjustments['tax_factor']).quantize(Decimal('0.01'))
        else:
            # Monthly: standard calculation
            taxable_income = gross_pay - sss - philhealth - pagibig
            if withholding_tax is None:
                tax_result = self.calculate_withholding_tax(taxable_income)
                withholding_tax = tax_result['monthly_tax']

        # Calculate total deductions
        total_deductions = sss + philhealth + pagibig + withholding_tax + other_deductions

        # Calculate net pay
        net_pay = gross_pay - total_deductions

        return {
            'gross_pay': gross_pay.quantize(Decimal('0.01')),
            'sss_employee': sss.quantize(Decimal('0.01')),
            'philhealth_employee': philhealth.quantize(Decimal('0.01')),
            'pagibig_employee': pagibig.quantize(Decimal('0.01')),
            'withholding_tax': withholding_tax.quantize(Decimal('0.01')),
            'other_deductions': other_deductions.quantize(Decimal('0.01')),
            'total_deductions': total_deductions.quantize(Decimal('0.01')),
            'net_pay': net_pay.quantize(Decimal('0.01')),
            'pay_period': self.pay_period
        }


def get_philippines_payroll_summary(
    employee: Employee,
    basic_salary: Decimal,
    period_start: date,
    period_end: date,
    **kwargs
) -> Dict:
    """
    Get complete Philippines payroll summary for an employee
    
    Args:
        employee: Employee instance
        basic_salary: Monthly basic salary
        period_start: Payroll period start date
        period_end: Payroll period end date
        **kwargs: Additional parameters (overtime_hours, holiday_dates, etc.)
    
    Returns:
        Complete payroll breakdown dict
    """
    calculator = PhilippinesPayrollCalculator(employee, basic_salary, period_start, period_end)

    # Get statutory contributions
    sss = calculator.get_sss_contribution()
    philhealth = calculator.get_philhealth_contribution()
    pagibig = calculator.get_pagibig_contribution()

    # Calculate gross pay (can include allowances, overtime, etc.)
    gross_pay = basic_salary

    # Add overtime if provided
    if 'overtime_hours' in kwargs and kwargs['overtime_hours']:
        ot_result = calculator.calculate_overtime_pay(
            Decimal(str(kwargs['overtime_hours'])),
            kwargs.get('overtime_type', 'regular_day_ot')
        )
        gross_pay += ot_result['overtime_pay']

    # Add COLA if provided
    if 'region_code' in kwargs and kwargs['region_code']:
        cola_result = calculator.calculate_cola(
            kwargs['region_code'],
            kwargs.get('working_days', 22)
        )
        gross_pay += cola_result['cola']

    # Calculate net pay
    net_pay_result = calculator.calculate_net_pay(
        gross_pay,
        sss=sss['employee_contribution'],
        philhealth=philhealth['employee_share'],
        pagibig=pagibig['employee_contribution'],
        other_deductions=Decimal(str(kwargs.get('other_deductions', 0)))
    )

    return {
        'employee': employee,
        'period_start': period_start,
        'period_end': period_end,
        'basic_salary': basic_salary,
        'gross_pay': net_pay_result['gross_pay'],
        'sss': sss,
        'philhealth': philhealth,
        'pagibig': pagibig,
        'net_pay_breakdown': net_pay_result,
        'currency': '₱',
        'country': 'Philippines'
    }


def philippines_payroll_calculation(employee, start_date, end_date):
    """
    MAIN PHILIPPINES PAYROLL CALCULATION - Integrated with Horilla
    
    This function replaces the USA payroll calculation when Philippines is active.
    It returns data in the SAME FORMAT as the USA calculator but with:
    - SSS contributions (auto-calculated from brackets)
    - PhilHealth contributions (auto-calculated from brackets)
    - Pag-IBIG contributions (auto-calculated from brackets)
    - BIR withholding tax (TRAIN Law)
    - 13th month pay accrual
    - Overtime pay (night diff, rest day, holidays)
    - COLA (Cost of Living Allowance)
    - Regional minimum wage compliance
    """
    import json
    from payroll.models.models import Contract
    from payroll.methods.methods import compute_salary_on_period
    from payroll.methods.payslip_calc import calculate_allowance
    from payroll.methods.deductions import update_compensation_deduction
    
    # Get basic pay details using existing Horilla function
    basic_pay_details = compute_salary_on_period(employee, start_date, end_date)
    contract = basic_pay_details["contract"]
    contract_wage = basic_pay_details["contract_wage"]
    basic_pay = basic_pay_details["basic_pay"]
    loss_of_pay = basic_pay_details["loss_of_pay"]
    paid_days = basic_pay_details["paid_days"]
    unpaid_days = basic_pay_details["unpaid_days"]
    working_days_details = basic_pay_details["month_data"]
    
    # Update basic pay with any adjustments
    updated_basic_pay_data = update_compensation_deduction(
        employee, basic_pay, "basic_pay", start_date, end_date
    )
    basic_pay = updated_basic_pay_data["compensation_amount"]
    basic_pay_deductions = updated_basic_pay_data["deductions"]
    
    loss_of_pay_amount = 0
    if not contract.deduct_leave_from_basic_pay:
        loss_of_pay_amount = loss_of_pay
    else:
        basic_pay = basic_pay - loss_of_pay_amount
    
    # Calculate allowances (keeps existing allowance system)
    kwargs = {
        "employee": employee,
        "start_date": start_date,
        "end_date": end_date,
        "basic_pay": basic_pay,
        "day_dict": working_days_details,
    }
    allowances = calculate_allowance(**kwargs)
    total_allowance = sum(allowance["amount"] for allowance in allowances["allowances"])
    
    # PHILIPPINES-SPECIFIC CALCULATIONS
    # Don't need to instantiate the calculator - use the methods directly
    monthly_basic = float(basic_pay)
    
    # 1. SSS CONTRIBUTION
    sss_contribution = PhilippinesSSSContribution.objects.filter(
        min_salary__lte=monthly_basic,
        max_salary__gte=monthly_basic
    ).first()
    
    if sss_contribution:
        sss_deduction = {
            "title": "SSS Contribution",
            "amount": float(sss_contribution.employee_contribution),
            "description": f"SSS bracket: ₱{sss_contribution.min_salary:.2f} - ₱{sss_contribution.max_salary:.2f}"
        }
    else:
        sss_deduction = {
            "title": "SSS Contribution",
            "amount": 0.0,
            "description": "No SSS bracket found"
        }
    
    # 2. PHILHEALTH CONTRIBUTION
    philhealth_contribution = PhilippinesPhilHealthContribution.objects.filter(
        min_salary__lte=monthly_basic
    ).order_by('-min_salary').first()
    
    if philhealth_contribution:
        philhealth_deduction = {
            "title": "PhilHealth Contribution",
            "amount": float(philhealth_contribution.employee_share),
            "description": f"PhilHealth premium: {philhealth_contribution.premium_rate}%"
        }
    else:
        philhealth_deduction = {
            "title": "PhilHealth Contribution",
            "amount": 0.0,
            "description": "No PhilHealth rate found"
        }
    
    # 3. PAG-IBIG CONTRIBUTION
    pagibig_contribution = PhilippinesPagIbigContribution.objects.filter(
        min_salary__lte=monthly_basic
    ).order_by('-min_salary').first()
    
    if pagibig_contribution:
        pagibig_deduction = {
            "title": "Pag-IBIG Contribution",
            "amount": float(pagibig_contribution.employee_contribution),
            "description": f"Pag-IBIG rate: {pagibig_contribution.employee_rate}%"
        }
    else:
        pagibig_deduction = {
            "title": "Pag-IBIG Contribution",
            "amount": 0.0,
            "description": "No Pag-IBIG rate found"
        }
    
    # Calculate GROSS PAY (Basic + Allowances)
    gross_pay = basic_pay + total_allowance
    
    # 4. BIR WITHHOLDING TAX (TRAIN Law)
    annual_salary = monthly_basic * 12
    total_government_contributions = (
        sss_deduction['amount'] + 
        philhealth_deduction['amount'] + 
        pagibig_deduction['amount']
    ) * 12
    
    taxable_annual = annual_salary - total_government_contributions
    
    # Find tax bracket
    tax_bracket = PhilippinesTaxBracket.objects.filter(
        min_annual_income__lte=taxable_annual
    ).order_by('-min_annual_income').first()
    
    if tax_bracket:
        excess = float(taxable_annual) - float(tax_bracket.min_annual_income)
        annual_tax = float(tax_bracket.base_tax) + (excess * float(tax_bracket.tax_rate) / 100)
        monthly_tax = annual_tax / 12
        
        tax_deduction = {
            "title": "Withholding Tax (BIR)",
            "amount": float(monthly_tax),
            "description": f"BIR bracket: {tax_bracket.tax_rate}% (₱{tax_bracket.min_annual_income:,.2f}+)"
        }
    else:
        monthly_tax = 0.0
        tax_deduction = {
            "title": "Withholding Tax (BIR)",
            "amount": 0.0,
            "description": "No tax bracket found"
        }
    
    # TOTAL DEDUCTIONS
    pretax_deductions = [sss_deduction, philhealth_deduction, pagibig_deduction]
    tax_deductions = [tax_deduction]
    post_tax_deductions = []  # Can add more if needed
    
    total_pretax = sum(d['amount'] for d in pretax_deductions)
    total_tax = sum(d['amount'] for d in tax_deductions)
    total_posttax = sum(d['amount'] for d in post_tax_deductions)
    
    total_deductions = total_pretax + total_tax + total_posttax + loss_of_pay_amount
    
    # NET PAY
    net_pay = gross_pay - total_deductions
    
    # Update net pay with any adjustments
    updated_net_pay_data = update_compensation_deduction(
        employee, net_pay, "net_pay", start_date, end_date
    )
    net_pay = updated_net_pay_data["compensation_amount"]
    net_pay_deductions_list = updated_net_pay_data["deductions"]
    
    # Build payslip data in Horilla format
    payslip_data = {
        "employee": employee,
        "contract_wage": contract_wage,
        "basic_pay": basic_pay,
        "gross_pay": gross_pay,
        "taxable_gross_pay": gross_pay - total_pretax,  # After mandatory deductions
        "net_pay": net_pay,
        "allowances": allowances["allowances"],
        "paid_days": paid_days,
        "unpaid_days": unpaid_days,
        "basic_pay_deductions": basic_pay_deductions,
        "gross_pay_deductions": [],
        "pretax_deductions": pretax_deductions,
        "post_tax_deductions": post_tax_deductions,
        "tax_deductions": tax_deductions,
        "net_deductions": net_pay_deductions_list,
        "total_deductions": total_deductions,
        "loss_of_pay": loss_of_pay,
        "federal_tax": 0.0,  # NOT USED IN PHILIPPINES - tax is in tax_deductions
        "start_date": start_date,
        "end_date": end_date,
        "range": f"{start_date.strftime('%b %d %Y')} - {end_date.strftime('%b %d %Y')}",
    }
    
    # Convert to JSON for storage
    data_to_json = payslip_data.copy()
    data_to_json["employee"] = employee.id
    data_to_json["start_date"] = start_date.strftime("%Y-%m-%d")
    data_to_json["end_date"] = end_date.strftime("%Y-%m-%d")
    json_data = json.dumps(data_to_json)
    
    payslip_data["json_data"] = json_data
    payslip_data["installments"] = {}  # Can add loan installments if needed
    
    return payslip_data
