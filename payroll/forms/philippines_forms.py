"""
philippines_forms.py

Forms for Philippines payroll system (frontend - client-facing)
"""

from django import forms
from django.utils.translation import gettext_lazy as _

from base.forms import ModelForm
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


class PhilippinesEmployeePayrollInfoForm(forms.ModelForm):
    """
    Form for employee's Philippines payroll information
    User-facing form for clients to manage employee payroll details
    """
    
    region = forms.ModelChoiceField(
        queryset=PhilippinesRegion.objects.all(),
        required=True,
        label=_("Region"),
        help_text=_("Select the region where the employee is based")
    )
    
    sss_number = forms.CharField(
        max_length=20,
        required=False,
        label=_("SSS Number"),
        help_text=_("Social Security System number (e.g., 01-2345678-9)")
    )
    
    philhealth_number = forms.CharField(
        max_length=20,
        required=False,
        label=_("PhilHealth Number"),
        help_text=_("PhilHealth ID number (e.g., 12-345678901-2)")
    )
    
    pagibig_number = forms.CharField(
        max_length=20,
        required=False,
        label=_("Pag-IBIG Number"),
        help_text=_("Pag-IBIG MID number (e.g., 1234-5678-9012)")
    )
    
    tin_number = forms.CharField(
        max_length=20,
        required=False,
        label=_("TIN (Tax Identification Number)"),
        help_text=_("BIR TIN number (e.g., 123-456-789-000)")
    )
    
    class Meta:
        model = Employee
        fields = ['region', 'sss_number', 'philhealth_number', 'pagibig_number', 'tin_number']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})


class PhilippinesPayslipGenerationForm(forms.Form):
    """
    Form for generating Philippines payslips
    Allows clients to compute payroll with PH-specific fields
    """
    
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.filter(is_active=True),
        required=True,
        label=_("Employee"),
        widget=forms.Select(attrs={'class': 'form-control select2'})
    )
    
    period_start = forms.DateField(
        required=True,
        label=_("Period Start Date"),
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    period_end = forms.DateField(
        required=True,
        label=_("Period End Date"),
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    basic_salary = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=True,
        label=_("Basic Salary"),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    
    # Allowances
    cola = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        initial=0,
        label=_("COLA (Cost of Living Allowance)"),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    
    meal_allowance = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        initial=0,
        label=_("Meal Allowance"),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    
    transportation_allowance = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        initial=0,
        label=_("Transportation Allowance"),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    
    # Overtime
    regular_ot_hours = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        initial=0,
        label=_("Regular Overtime Hours (125%)"),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    
    rest_day_ot_hours = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        initial=0,
        label=_("Rest Day Overtime Hours (130%)"),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    
    night_diff_hours = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        initial=0,
        label=_("Night Differential Hours (10 PM - 6 AM)"),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    
    # Deductions
    sss_loan = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        initial=0,
        label=_("SSS Loan Deduction"),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    
    pagibig_loan = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        initial=0,
        label=_("Pag-IBIG Loan Deduction"),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    
    cash_advance = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        initial=0,
        label=_("Cash Advance"),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    
    other_deductions = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        initial=0,
        label=_("Other Deductions"),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    
    # Working days
    working_days = forms.IntegerField(
        required=False,
        initial=22,
        label=_("Working Days"),
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    days_worked = forms.IntegerField(
        required=False,
        label=_("Days Actually Worked"),
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    # 13th month pay
    include_13th_month = forms.BooleanField(
        required=False,
        initial=False,
        label=_("Include 13th Month Pay"),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class PhilippinesThirteenthMonthPayForm(forms.Form):
    """
    Form for calculating 13th month pay
    """
    
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.filter(is_active=True),
        required=True,
        label=_("Employee"),
        widget=forms.Select(attrs={'class': 'form-control select2'})
    )
    
    year = forms.IntegerField(
        required=True,
        label=_("Year"),
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    total_basic_salary_ytd = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=True,
        label=_("Total Basic Salary (Year-to-Date)"),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    
    months_worked = forms.IntegerField(
        required=True,
        initial=12,
        label=_("Months Worked"),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 12})
    )


class PhilippinesGovernmentReportForm(forms.Form):
    """
    Form for generating Philippines government reports
    """
    
    REPORT_CHOICES = [
        ('bir_2316', _('BIR Form 2316 - Annual ITR')),
        ('alphalist', _('Alphalist - Annual Information Return')),
        ('sss_r3', _('SSS R3 - Monthly Remittance')),
        ('sss_r5', _('SSS R5 - Employer Contribution')),
        ('philhealth_rf1', _('PhilHealth RF-1 - Monthly Remittance')),
        ('pagibig_mcrf', _('Pag-IBIG MCRF - Monthly Contribution')),
    ]
    
    report_type = forms.ChoiceField(
        choices=REPORT_CHOICES,
        required=True,
        label=_("Report Type"),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    period_start = forms.DateField(
        required=True,
        label=_("Period Start"),
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    period_end = forms.DateField(
        required=True,
        label=_("Period End"),
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    employees = forms.ModelMultipleChoiceField(
        queryset=Employee.objects.filter(is_active=True),
        required=False,
        label=_("Employees (leave blank for all)"),
        widget=forms.SelectMultiple(attrs={'class': 'form-control select2'})
    )


class PhilippinesSSSLoanForm(ModelForm):
    """
    Form for SSS loan deductions
    """
    
    loan_type = forms.ChoiceField(
        choices=[
            ('salary', _('Salary Loan')),
            ('calamity', _('Calamity Loan')),
        ],
        required=True,
        label=_("SSS Loan Type"),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    loan_amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=True,
        label=_("Loan Amount"),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    
    monthly_amortization = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=True,
        label=_("Monthly Amortization"),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    
    start_date = forms.DateField(
        required=True,
        label=_("Start Date"),
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    number_of_months = forms.IntegerField(
        required=True,
        label=_("Number of Months"),
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )


class PhilippinesPagIbigLoanForm(ModelForm):
    """
    Form for Pag-IBIG loan deductions
    """
    
    loan_type = forms.ChoiceField(
        choices=[
            ('housing', _('Housing Loan')),
            ('multi_purpose', _('Multi-Purpose Loan')),
            ('calamity', _('Calamity Loan')),
        ],
        required=True,
        label=_("Pag-IBIG Loan Type"),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    loan_amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=True,
        label=_("Loan Amount"),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    
    monthly_amortization = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=True,
        label=_("Monthly Amortization"),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    
    start_date = forms.DateField(
        required=True,
        label=_("Start Date"),
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    number_of_months = forms.IntegerField(
        required=True,
        label=_("Number of Months"),
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )


class PhilippinesContributionAdjustmentForm(forms.Form):
    """
    Form for adjusting government contributions manually
    For special cases or corrections
    """
    
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.filter(is_active=True),
        required=True,
        label=_("Employee"),
        widget=forms.Select(attrs={'class': 'form-control select2'})
    )
    
    period = forms.DateField(
        required=True,
        label=_("Period"),
        widget=forms.DateInput(attrs={'type': 'month', 'class': 'form-control'})
    )
    
    # SSS
    override_sss = forms.BooleanField(
        required=False,
        label=_("Override SSS Contribution"),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    sss_employee = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        label=_("SSS Employee Share"),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    
    sss_employer = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        label=_("SSS Employer Share"),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    
    # PhilHealth
    override_philhealth = forms.BooleanField(
        required=False,
        label=_("Override PhilHealth Contribution"),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    philhealth_employee = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        label=_("PhilHealth Employee Share"),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    
    philhealth_employer = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        label=_("PhilHealth Employer Share"),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    
    # Pag-IBIG
    override_pagibig = forms.BooleanField(
        required=False,
        label=_("Override Pag-IBIG Contribution"),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    pagibig_employee = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        label=_("Pag-IBIG Employee Share"),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    
    pagibig_employer = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        label=_("Pag-IBIG Employer Share"),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    
    reason = forms.CharField(
        required=True,
        label=_("Reason for Adjustment"),
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
