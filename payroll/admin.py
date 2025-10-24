"""
admin.py

Used to register models on admin site
"""

from django.contrib import admin

from payroll.models.models import (
    Allowance,
    Contract,
    Deduction,
    FilingStatus,
    LoanAccount,
    MultipleCondition,
    Payslip,
    PayslipAutoGenerate,
    Reimbursement,
    ReimbursementrequestComment,
)
from payroll.models.tax_models import PayrollSettings, TaxBracket
from payroll.models.country_models import (
    PayrollCountryConfig,
    PhilippinesRegion,
    PhilippinesSSSContribution,
    PhilippinesPhilHealthContribution,
    PhilippinesPagIbigContribution,
    PhilippinesTaxBracket,
    PhilippinesThirteenthMonthPay,
    PhilippinesOvertimeRule,
    PhilippinesHolidayPay,
    PhilippinesCOLA,
)


# Custom Admin for Country Configuration
@admin.register(PayrollCountryConfig)
class PayrollCountryConfigAdmin(admin.ModelAdmin):
    list_display = ('country', 'is_active', 'company_id')
    list_filter = ('is_active', 'country')
    search_fields = ('country',)
    fieldsets = (
        ('Country Selection', {
            'fields': ('country', 'is_active', 'company_id'),
            'description': 'Select and activate the country for payroll calculations. Only one country can be active at a time.'
        }),
    )


@admin.register(PhilippinesRegion)
class PhilippinesRegionAdmin(admin.ModelAdmin):
    list_display = ('region_code', 'region_name', 'daily_minimum_wage', 'monthly_minimum_wage', 'effective_date')
    list_filter = ('effective_date',)
    search_fields = ('region_code', 'region_name')


@admin.register(PhilippinesSSSContribution)
class PhilippinesSSSContributionAdmin(admin.ModelAdmin):
    list_display = ('min_salary', 'max_salary', 'monthly_salary_credit', 'employee_contribution', 'employer_contribution', 'total_contribution', 'effective_date')
    list_filter = ('effective_date',)
    ordering = ('min_salary',)


@admin.register(PhilippinesPhilHealthContribution)
class PhilippinesPhilHealthContributionAdmin(admin.ModelAdmin):
    list_display = ('min_salary', 'max_salary', 'premium_rate', 'monthly_premium', 'employee_share', 'employer_share', 'effective_date')
    list_filter = ('effective_date',)
    ordering = ('min_salary',)


@admin.register(PhilippinesPagIbigContribution)
class PhilippinesPagIbigContributionAdmin(admin.ModelAdmin):
    list_display = ('min_salary', 'max_salary', 'employee_rate', 'employer_rate', 'employee_contribution', 'employer_contribution', 'effective_date')
    list_filter = ('effective_date',)
    ordering = ('min_salary',)


@admin.register(PhilippinesTaxBracket)
class PhilippinesTaxBracketAdmin(admin.ModelAdmin):
    list_display = ('min_annual_income', 'max_annual_income', 'base_tax', 'tax_rate', 'effective_date')
    list_filter = ('effective_date',)
    ordering = ('min_annual_income',)


@admin.register(PhilippinesThirteenthMonthPay)
class PhilippinesThirteenthMonthPayAdmin(admin.ModelAdmin):
    list_display = ('year', 'tax_exempt_amount', 'computation_method', 'company_id')
    list_filter = ('year', 'computation_method')


@admin.register(PhilippinesOvertimeRule)
class PhilippinesOvertimeRuleAdmin(admin.ModelAdmin):
    list_display = ('overtime_type', 'multiplier', 'company_id')
    list_filter = ('overtime_type',)


@admin.register(PhilippinesHolidayPay)
class PhilippinesHolidayPayAdmin(admin.ModelAdmin):
    list_display = ('holiday_name', 'holiday_date', 'holiday_type', 'pay_multiplier')
    list_filter = ('holiday_type', 'holiday_date')
    ordering = ('holiday_date',)


@admin.register(PhilippinesCOLA)
class PhilippinesCOLAAdmin(admin.ModelAdmin):
    list_display = ('region', 'daily_cola', 'monthly_cola', 'is_taxable', 'effective_date')
    list_filter = ('is_taxable', 'effective_date', 'region')


# Register your models here.
admin.site.register(FilingStatus)
admin.site.register(TaxBracket)
admin.site.register(Contract)
admin.site.register(Allowance)


@admin.register(Deduction)
class DeductionAdmin(admin.ModelAdmin):
    list_display = ('title', 'country', 'is_pretax', 'is_tax', 'is_condition_based', 'include_active_employees')
    list_filter = ('country', 'is_pretax', 'is_tax', 'is_condition_based')
    search_fields = ('title',)
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'country', 'one_time_date')
        }),
        ('Type & Behavior', {
            'fields': ('is_tax', 'is_pretax', 'is_condition_based')
        }),
        ('Target Employees', {
            'fields': ('include_active_employees', 'specific_employees', 'exclude_employees')
        }),
        ('Calculation', {
            'fields': ('amount', 'rate', 'employer_rate', 'based_on', 'update_compensation')
        }),
        ('Conditions', {
            'fields': ('field', 'condition', 'value'),
            'classes': ('collapse',)
        }),
    )


admin.site.register(Payslip)
admin.site.register(PayrollSettings)
admin.site.register(LoanAccount)
admin.site.register(Reimbursement)
admin.site.register(ReimbursementrequestComment)
admin.site.register(MultipleCondition)
admin.site.register(PayslipAutoGenerate)
