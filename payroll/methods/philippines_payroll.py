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
    """

    def __init__(self, employee: Employee, basic_salary: Decimal, period_start: date, period_end: date):
        self.employee = employee
        self.basic_salary = Decimal(str(basic_salary))
        self.period_start = period_start
        self.period_end = period_end
        self.computation_date = date.today()

    def get_sss_contribution(self) -> Dict[str, Decimal]:
        """
        Calculate SSS contribution based on monthly salary
        Returns dict with employee, employer, and EC contributions
        """
        # Get the applicable SSS contribution table
        sss_table = PhilippinesSSSContribution.objects.filter(
            effective_date__lte=self.computation_date,
            min_salary__lte=self.basic_salary
        ).filter(
            Q(max_salary__gte=self.basic_salary) | Q(max_salary__isnull=True)
        ).order_by('-effective_date').first()

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
        """
        philhealth_table = PhilippinesPhilHealthContribution.objects.filter(
            effective_date__lte=self.computation_date,
            min_salary__lte=self.basic_salary
        ).filter(
            Q(max_salary__gte=self.basic_salary) | Q(max_salary__isnull=True)
        ).order_by('-effective_date').first()

        if not philhealth_table:
            # Calculate using 5% rate if no table
            premium_rate = Decimal('0.05')  # 5%
            monthly_premium = self.basic_salary * premium_rate
            employee_share = monthly_premium / 2
            employer_share = monthly_premium / 2

            return {
                'employee_share': employee_share.quantize(Decimal('0.01')),
                'employer_share': employer_share.quantize(Decimal('0.01')),
                'monthly_premium': monthly_premium.quantize(Decimal('0.01')),
                'premium_rate': premium_rate
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
        """
        pagibig_table = PhilippinesPagIbigContribution.objects.filter(
            effective_date__lte=self.computation_date,
            min_salary__lte=self.basic_salary
        ).filter(
            Q(max_salary__gte=self.basic_salary) | Q(max_salary__isnull=True)
        ).order_by('-effective_date').first()

        if not pagibig_table:
            # Default calculation: 2% employee, 2% employer
            employee_rate = Decimal('0.02')  # 2%
            employer_rate = Decimal('0.02')  # 2%
            
            employee_contribution = (self.basic_salary * employee_rate).quantize(Decimal('0.01'))
            employer_contribution = (self.basic_salary * employer_rate).quantize(Decimal('0.01'))
            
            # Cap at ₱100 for employee if salary <= ₱1,500
            if self.basic_salary <= Decimal('1500.00'):
                employee_contribution = min(employee_contribution, Decimal('100.00'))
                employer_contribution = min(employer_contribution, Decimal('100.00'))

            return {
                'employee_contribution': employee_contribution,
                'employer_contribution': employer_contribution,
                'total_contribution': employee_contribution + employer_contribution,
                'employee_rate': employee_rate,
                'employer_rate': employer_rate
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
        thirteenth_month_pay: Decimal = Decimal('0.00')
    ) -> Dict[str, Decimal]:
        """
        Calculate withholding tax based on TRAIN Law (Tax Reform for Acceleration and Inclusion)
        
        Args:
            taxable_income: Monthly taxable income
            thirteenth_month_pay: 13th month pay amount (exempt up to ₱90,000/year)
        
        Returns:
            Dict with tax details
        """
        # Convert monthly to annual income
        annual_taxable_income = taxable_income * 12

        # Handle 13th month pay exemption (₱90,000 max)
        thirteenth_month_config = PhilippinesThirteenthMonthPay.objects.filter(
            year=self.period_end.year
        ).first()
        
        tax_exempt_13th_month = Decimal('90000.00')
        if thirteenth_month_config:
            tax_exempt_13th_month = thirteenth_month_config.tax_exempt_amount

        # Taxable portion of 13th month pay
        taxable_13th_month = max(Decimal('0.00'), thirteenth_month_pay - tax_exempt_13th_month)
        total_annual_taxable = annual_taxable_income + taxable_13th_month

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
                'excess_tax': Decimal('0.00')
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
            'taxable_income': total_annual_taxable.quantize(Decimal('0.01'))
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
        # Get hourly rate (monthly salary / 8 hours / days per month)
        daily_rate = self.basic_salary / Decimal('22')  # Assuming 22 working days
        hourly_rate = daily_rate / Decimal('8')

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
            # Night differential is additional 10% of hourly rate
            ot_pay = overtime_hours * hourly_rate * multiplier
        else:
            ot_pay = overtime_hours * hourly_rate * multiplier

        return {
            'overtime_pay': ot_pay.quantize(Decimal('0.01')),
            'overtime_hours': overtime_hours,
            'hourly_rate': hourly_rate.quantize(Decimal('0.01')),
            'multiplier': multiplier,
            'overtime_type': overtime_type
        }

    def calculate_holiday_pay(
        self,
        holiday_date: date,
        worked: bool = False
    ) -> Dict[str, Decimal]:
        """
        Calculate holiday pay
        
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

        daily_rate = self.basic_salary / Decimal('22')

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
        Calculate net pay
        
        Args:
            gross_pay: Gross monthly pay
            sss: SSS employee contribution (calculated if not provided)
            philhealth: PhilHealth employee share (calculated if not provided)
            pagibig: Pag-IBIG employee contribution (calculated if not provided)
            withholding_tax: Withholding tax (calculated if not provided)
            other_deductions: Other deductions
        
        Returns:
            Dict with net pay breakdown
        """
        # Calculate mandatory deductions if not provided
        if sss is None:
            sss = self.get_sss_contribution()['employee_contribution']
        if philhealth is None:
            philhealth = self.get_philhealth_contribution()['employee_share']
        if pagibig is None:
            pagibig = self.get_pagibig_contribution()['employee_contribution']

        # Calculate taxable income (gross - non-taxable deductions)
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
            'taxable_income': taxable_income.quantize(Decimal('0.01'))
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
