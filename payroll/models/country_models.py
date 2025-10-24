"""
country_models.py

This module contains models for country-specific payroll configurations.
"""

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from base.horilla_company_manager import HorillaCompanyManager
from base.models import Company
from horilla.models import HorillaModel


class PayrollCountryConfig(HorillaModel):
    """
    Model to configure which country's payroll system is active
    """
    
    COUNTRY_CHOICES = [
        ('USA', _('United States')),
        ('PH', _('Philippines')),
    ]
    
    country = models.CharField(
        max_length=3,
        choices=COUNTRY_CHOICES,
        unique=True,
        verbose_name=_("Country")
    )
    is_active = models.BooleanField(
        default=False,
        verbose_name=_("Is Active"),
        help_text=_("Only one country can be active at a time")
    )
    company_id = models.ForeignKey(
        Company, 
        null=True, 
        blank=True,
        on_delete=models.CASCADE,
        verbose_name=_("Company"),
        help_text=_("Leave blank to apply globally")
    )
    objects = HorillaCompanyManager("company_id")
    
    class Meta:
        verbose_name = _("Payroll Country Configuration")
        verbose_name_plural = _("Payroll Country Configurations")
        ordering = ['country']
    
    def __str__(self):
        return f"{self.get_country_display()} - {'Active' if self.is_active else 'Inactive'}"
    
    def clean(self):
        super().clean()
        if self.is_active:
            # Ensure only one country is active at a time
            active_configs = PayrollCountryConfig.objects.filter(
                is_active=True,
                company_id=self.company_id
            ).exclude(pk=self.pk)
            
            if active_configs.exists():
                raise ValidationError({
                    'is_active': _('Only one country configuration can be active at a time. Please deactivate other countries first.')
                })
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @classmethod
    def get_active_country(cls, company_id=None):
        """
        Get the currently active country configuration
        """
        try:
            return cls.objects.filter(is_active=True, company_id=company_id).first()
        except cls.DoesNotExist:
            return None


class PhilippinesRegion(HorillaModel):
    """
    Model for Philippines regions with their minimum wage rates
    """
    
    region_code = models.CharField(
        max_length=10,
        unique=True,
        verbose_name=_("Region Code"),
        help_text=_("e.g., NCR, Region I, CAR")
    )
    region_name = models.CharField(
        max_length=100,
        verbose_name=_("Region Name")
    )
    daily_minimum_wage = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_("Daily Minimum Wage"),
        help_text=_("Current daily minimum wage for this region")
    )
    monthly_minimum_wage = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_("Monthly Minimum Wage"),
        help_text=_("Computed as daily wage × working days")
    )
    effective_date = models.DateField(
        verbose_name=_("Effective Date"),
        help_text=_("Date when this wage rate became effective")
    )
    company_id = models.ForeignKey(
        Company, 
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )
    objects = HorillaCompanyManager("company_id")
    
    class Meta:
        verbose_name = _("Philippines Region")
        verbose_name_plural = _("Philippines Regions")
        ordering = ['region_code']
    
    def __str__(self):
        return f"{self.region_code} - {self.region_name}"


class PhilippinesSSSContribution(HorillaModel):
    """
    SSS (Social Security System) Contribution Table for Philippines
    Based on SSS contribution schedule
    """
    
    min_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Minimum Salary Range")
    )
    max_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Maximum Salary Range")
    )
    monthly_salary_credit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Monthly Salary Credit (MSC)")
    )
    employee_contribution = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Employee Contribution"),
        help_text=_("Employee's share (typically 4.5%)")
    )
    employer_contribution = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Employer Contribution"),
        help_text=_("Employer's share (typically 9.5%)")
    )
    total_contribution = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Total Contribution"),
        help_text=_("Total SSS contribution (14%)")
    )
    ec_contribution = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=10.00,
        verbose_name=_("EC (Employer's Compensation)"),
        help_text=_("Employer's Compensation contribution (typically ₱10)")
    )
    effective_date = models.DateField(
        verbose_name=_("Effective Date")
    )
    company_id = models.ForeignKey(
        Company, 
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )
    objects = HorillaCompanyManager("company_id")
    
    class Meta:
        verbose_name = _("SSS Contribution Table")
        verbose_name_plural = _("SSS Contribution Tables")
        ordering = ['min_salary']
    
    def __str__(self):
        max_display = f"{self.max_salary}" if self.max_salary else "Above"
        return f"₱{self.min_salary} - {max_display} (MSC: ₱{self.monthly_salary_credit})"
    
    def clean(self):
        super().clean()
        if self.max_salary and self.min_salary >= self.max_salary:
            raise ValidationError({
                'max_salary': _("Maximum salary must be greater than minimum salary")
            })


class PhilippinesPhilHealthContribution(HorillaModel):
    """
    PhilHealth (Philippine Health Insurance Corporation) Contribution Table
    Based on PhilHealth premium rate schedule
    """
    
    min_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Minimum Salary Range")
    )
    max_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Maximum Salary Range")
    )
    premium_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=5.00,
        verbose_name=_("Premium Rate (%)"),
        help_text=_("Currently 5% of basic salary")
    )
    monthly_premium = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Monthly Premium"),
        help_text=_("Total monthly premium")
    )
    employee_share = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Employee Share"),
        help_text=_("Employee's share (50%)")
    )
    employer_share = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Employer Share"),
        help_text=_("Employer's share (50%)")
    )
    effective_date = models.DateField(
        verbose_name=_("Effective Date")
    )
    company_id = models.ForeignKey(
        Company, 
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )
    objects = HorillaCompanyManager("company_id")
    
    class Meta:
        verbose_name = _("PhilHealth Contribution Table")
        verbose_name_plural = _("PhilHealth Contribution Tables")
        ordering = ['min_salary']
    
    def __str__(self):
        max_display = f"{self.max_salary}" if self.max_salary else "Above"
        return f"₱{self.min_salary} - {max_display} (Premium: ₱{self.monthly_premium})"


class PhilippinesPagIbigContribution(HorillaModel):
    """
    Pag-IBIG (HDMF - Home Development Mutual Fund) Contribution Table
    Based on Pag-IBIG contribution schedule
    """
    
    min_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Minimum Salary Range")
    )
    max_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Maximum Salary Range")
    )
    employee_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=2.00,
        verbose_name=_("Employee Rate (%)"),
        help_text=_("Employee contribution rate")
    )
    employer_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=2.00,
        verbose_name=_("Employer Rate (%)"),
        help_text=_("Employer contribution rate")
    )
    employee_contribution = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Employee Contribution")
    )
    employer_contribution = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Employer Contribution")
    )
    total_contribution = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Total Contribution")
    )
    effective_date = models.DateField(
        verbose_name=_("Effective Date")
    )
    company_id = models.ForeignKey(
        Company, 
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )
    objects = HorillaCompanyManager("company_id")
    
    class Meta:
        verbose_name = _("Pag-IBIG Contribution Table")
        verbose_name_plural = _("Pag-IBIG Contribution Tables")
        ordering = ['min_salary']
    
    def __str__(self):
        max_display = f"{self.max_salary}" if self.max_salary else "Above"
        return f"₱{self.min_salary} - {max_display} (Total: ₱{self.total_contribution})"


class PhilippinesTaxBracket(HorillaModel):
    """
    Philippines BIR Tax Brackets based on TRAIN Law
    Withholding tax on compensation
    """
    
    min_annual_income = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_("Minimum Annual Income")
    )
    max_annual_income = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Maximum Annual Income")
    )
    base_tax = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_("Base Tax"),
        help_text=_("Fixed tax amount for this bracket")
    )
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name=_("Tax Rate (%)"),
        help_text=_("Tax rate for excess over minimum")
    )
    effective_date = models.DateField(
        verbose_name=_("Effective Date")
    )
    company_id = models.ForeignKey(
        Company, 
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )
    objects = HorillaCompanyManager("company_id")
    
    class Meta:
        verbose_name = _("Philippines Tax Bracket (TRAIN Law)")
        verbose_name_plural = _("Philippines Tax Brackets (TRAIN Law)")
        ordering = ['min_annual_income']
    
    def __str__(self):
        max_display = f"{self.max_annual_income}" if self.max_annual_income else "Above"
        return f"₱{self.min_annual_income} - {max_display} ({self.tax_rate}%)"
    
    def clean(self):
        super().clean()
        if self.max_annual_income and self.min_annual_income >= self.max_annual_income:
            raise ValidationError({
                'max_annual_income': _("Maximum income must be greater than minimum income")
            })


class PhilippinesThirteenthMonthPay(HorillaModel):
    """
    13th Month Pay configuration and tracking
    """
    
    year = models.IntegerField(
        verbose_name=_("Year")
    )
    tax_exempt_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=90000.00,
        verbose_name=_("Tax Exempt Amount"),
        help_text=_("Maximum tax-exempt 13th month pay (currently ₱90,000)")
    )
    computation_method = models.CharField(
        max_length=20,
        choices=[
            ('total_basic', _('Total Basic Salary / 12')),
            ('prorated', _('Prorated Based on Months Worked')),
        ],
        default='total_basic',
        verbose_name=_("Computation Method")
    )
    company_id = models.ForeignKey(
        Company, 
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )
    objects = HorillaCompanyManager("company_id")
    
    class Meta:
        verbose_name = _("13th Month Pay Configuration")
        verbose_name_plural = _("13th Month Pay Configurations")
        unique_together = ['year', 'company_id']
    
    def __str__(self):
        return f"13th Month Pay {self.year} - Exempt: ₱{self.tax_exempt_amount}"


class PhilippinesOvertimeRule(HorillaModel):
    """
    Overtime pay rules based on Philippines Labor Code
    """
    
    OVERTIME_TYPE_CHOICES = [
        ('regular_day_ot', _('Regular Day Overtime - 125%')),
        ('rest_day_ot', _('Rest Day Overtime - 130%')),
        ('special_holiday_ot', _('Special Holiday Overtime - 130%')),
        ('special_holiday_rest_day_ot', _('Special Holiday + Rest Day OT - 150%')),
        ('regular_holiday_ot', _('Regular Holiday Overtime - 160%')),
        ('regular_holiday_rest_day_ot', _('Regular Holiday + Rest Day OT - 260%')),
        ('night_differential', _('Night Differential - 10%')),
    ]
    
    overtime_type = models.CharField(
        max_length=50,
        choices=OVERTIME_TYPE_CHOICES,
        unique=True,
        verbose_name=_("Overtime Type")
    )
    multiplier = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name=_("Pay Multiplier"),
        help_text=_("Multiplier for the hourly rate")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Description")
    )
    company_id = models.ForeignKey(
        Company, 
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )
    objects = HorillaCompanyManager("company_id")
    
    class Meta:
        verbose_name = _("Overtime Rule")
        verbose_name_plural = _("Overtime Rules")
    
    def __str__(self):
        return f"{self.get_overtime_type_display()} - {self.multiplier}x"


class PhilippinesHolidayPay(HorillaModel):
    """
    Holiday pay configuration for Philippines
    """
    
    HOLIDAY_TYPE_CHOICES = [
        ('regular', _('Regular Holiday - 200%')),
        ('special', _('Special Non-Working Day - 130%')),
    ]
    
    holiday_date = models.DateField(
        verbose_name=_("Holiday Date")
    )
    holiday_name = models.CharField(
        max_length=100,
        verbose_name=_("Holiday Name")
    )
    holiday_type = models.CharField(
        max_length=20,
        choices=HOLIDAY_TYPE_CHOICES,
        verbose_name=_("Holiday Type")
    )
    pay_multiplier = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name=_("Pay Multiplier")
    )
    company_id = models.ForeignKey(
        Company, 
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )
    objects = HorillaCompanyManager("company_id")
    
    class Meta:
        verbose_name = _("Holiday Pay Configuration")
        verbose_name_plural = _("Holiday Pay Configurations")
        unique_together = ['holiday_date', 'company_id']
    
    def __str__(self):
        return f"{self.holiday_name} - {self.holiday_date} ({self.pay_multiplier}x)"


class PhilippinesCOLA(HorillaModel):
    """
    Cost of Living Allowance (COLA) for Philippines
    """
    
    region = models.ForeignKey(
        PhilippinesRegion,
        on_delete=models.CASCADE,
        verbose_name=_("Region")
    )
    daily_cola = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_("Daily COLA Amount")
    )
    monthly_cola = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_("Monthly COLA Amount")
    )
    is_taxable = models.BooleanField(
        default=False,
        verbose_name=_("Is Taxable"),
        help_text=_("Whether COLA is subject to withholding tax")
    )
    effective_date = models.DateField(
        verbose_name=_("Effective Date")
    )
    company_id = models.ForeignKey(
        Company, 
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )
    objects = HorillaCompanyManager("company_id")
    
    class Meta:
        verbose_name = _("COLA Configuration")
        verbose_name_plural = _("COLA Configurations")
    
    def __str__(self):
        return f"COLA - {self.region.region_code}: ₱{self.daily_cola}/day"
