"""
country_models.py

This module contains models for country-specific payroll configurations.
"""

from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum
from django.utils.translation import gettext_lazy as _

from base.horilla_company_manager import HorillaCompanyManager
from base.models import Company
from horilla.models import HorillaModel


class PayrollCountryConfig(HorillaModel):
    """
    Model to configure which country's payroll system is active.
    
    CRITICAL CONSTRAINT: Only ONE country can be active per company at a time.
    This prevents mixed payroll calculations which cause legal/compliance issues.
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
    activated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Last Activated At"),
        help_text=_("Timestamp when this country was last activated")
    )
    activated_by = models.ForeignKey(
        'employee.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payroll_country_activations',
        verbose_name=_("Activated By"),
        help_text=_("User who last activated this country configuration")
    )
    
    objects = HorillaCompanyManager("company_id")
    
    class Meta:
        verbose_name = _("Payroll Country Configuration")
        verbose_name_plural = _("Payroll Country Configurations")
        ordering = ['country']
        constraints = [
            # Database-level constraint: Only one active country per company
            models.UniqueConstraint(
                fields=['company_id'],
                condition=models.Q(is_active=True),
                name='one_active_country_per_company'
            )
        ]
        indexes = [
            models.Index(fields=['is_active', 'company_id'], name='payroll_country_active_idx'),
        ]
    
    def __str__(self):
        return f"{self.get_country_display()} - {'Active' if self.is_active else 'Inactive'}"
    
    def clean(self):
        """
        Validate that only one country is active per company.
        This is critical for payroll integrity.
        """
        super().clean()
        if self.is_active:
            # Check for other active countries in same company
            active_configs = PayrollCountryConfig.objects.filter(
                is_active=True,
                company_id=self.company_id
            ).exclude(pk=self.pk)
            
            if active_configs.exists():
                active_country = active_configs.first()
                raise ValidationError({
                    'is_active': _(
                        f'Cannot activate {self.get_country_display()}. '
                        f'{active_country.get_country_display()} is already active. '
                        f'You must deactivate {active_country.get_country_display()} first.'
                    )
                })
    
    def save(self, *args, **kwargs):
        """
        Override save to enforce validation, atomic switching, and cache clearing.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Run validation
        self.full_clean()
        
        # If activating this country, deactivate all others in same company (atomic operation)
        if self.is_active:
            PayrollCountryConfig.objects.filter(
                company_id=self.company_id
            ).exclude(pk=self.pk).update(is_active=False)
            
            logger.warning(
                f"Payroll country switched to {self.get_country_display()} "
                f"for company {self.company_id or 'Global'}"
            )
        
        super().save(*args, **kwargs)
        
        # Clear middleware cache to force refresh
        try:
            from payroll.middleware import PayrollCountryMiddleware
            PayrollCountryMiddleware.clear_country_cache()
            logger.info("Cleared payroll country cache after config change")
        except ImportError:
            logger.warning("Could not clear payroll country cache - middleware not found")
    
    def delete(self, *args, **kwargs):
        """Override delete to clear cache."""
        import logging
        logger = logging.getLogger(__name__)
        
        super().delete(*args, **kwargs)
        
        try:
            from payroll.middleware import PayrollCountryMiddleware
            PayrollCountryMiddleware.clear_country_cache()
            logger.info("Cleared payroll country cache after config deletion")
        except ImportError:
            logger.warning("Could not clear payroll country cache - middleware not found")
    
    @classmethod
    def get_active_country(cls, company_id=None):
        """
        Get the currently active country configuration.
        
        Returns:
            PayrollCountryConfig or None: The active country config, or None if not found
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


class PhilippinesBIRForm2316(HorillaModel):
    """
    BIR Form 2316 - Certificate of Compensation Payment/Tax Withheld
    
    Legally required by Revenue Regulations to be issued to all employees
    by January 31 of the following year.
    
    This model stores annual compensation data for Form 2316 generation.
    """
    
    employee = models.ForeignKey(
        'employee.Employee',
        on_delete=models.CASCADE,
        related_name='bir_form_2316',
        verbose_name=_("Employee")
    )
    
    year = models.IntegerField(
        verbose_name=_("Tax Year"),
        help_text=_("Calendar year for which this form is issued")
    )
    
    # Employer Information
    employer_tin = models.CharField(
        max_length=20,
        verbose_name=_("Employer TIN"),
        help_text=_("Tax Identification Number of employer")
    )
    
    employer_name = models.CharField(
        max_length=255,
        verbose_name=_("Employer Name")
    )
    
    employer_address = models.TextField(
        verbose_name=_("Employer Address")
    )
    
    # Employee Information (from Employee model at time of generation)
    employee_tin = models.CharField(
        max_length=20,
        verbose_name=_("Employee TIN")
    )
    
    employee_name = models.CharField(
        max_length=255,
        verbose_name=_("Employee Name")
    )
    
    employee_address = models.TextField(
        verbose_name=_("Employee Address")
    )
    
    # Compensation Income
    gross_compensation = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_("Gross Compensation Income"),
        help_text=_("Total compensation before deductions")
    )
    
    non_taxable_13th_month = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_("Non-Taxable 13th Month & Other Benefits"),
        help_text=_("Up to ₱90,000 exempt")
    )
    
    non_taxable_de_minimis = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_("Non-Taxable De Minimis Benefits"),
        help_text=_("Rice, clothing, medical, laundry allowances")
    )
    
    non_taxable_sss = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_("SSS/GSIS/PHIC/HDMF Contributions"),
        help_text=_("Employee share of mandatory contributions")
    )
    
    non_taxable_salaries = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_("Salaries & Other Forms of Compensation (Non-Taxable)"),
        help_text=_("Other non-taxable compensation")
    )
    
    # Taxable Compensation
    taxable_basic_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_("Taxable Basic Salary")
    )
    
    taxable_13th_month = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_("Taxable 13th Month & Other Benefits"),
        help_text=_("Amount exceeding ₱90,000")
    )
    
    taxable_other_benefits = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_("Taxable Other Benefits")
    )
    
    # Exemptions
    personal_exemption = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=50000,
        verbose_name=_("Personal Exemption"),
        help_text=_("₱50,000 standard personal exemption")
    )
    
    additional_exemption = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_("Additional Exemption"),
        help_text=_("₱25,000 per dependent (max 4)")
    )
    
    # Premium Paid on Health/Hospital Insurance
    premium_paid = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_("Premium Paid on Health Insurance"),
        help_text=_("Max ₱2,400 or 2.4% of MWE, whichever is lower")
    )
    
    # Tax Withheld
    tax_withheld_jan_to_nov = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_("Tax Withheld January to November")
    )
    
    tax_withheld_december = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_("Tax Withheld December")
    )
    
    tax_withheld_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_("Total Tax Withheld"),
        help_text=_("Sum of January-December withholding tax")
    )
    
    # Metadata
    generated_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Generated Date")
    )
    
    generated_by = models.ForeignKey(
        'employee.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generated_bir_forms',
        verbose_name=_("Generated By")
    )
    
    is_substituted = models.BooleanField(
        default=False,
        verbose_name=_("Is Substituted Filing"),
        help_text=_("Whether this is a substituted/corrected form")
    )
    
    company_id = models.ForeignKey(
        Company,
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )
    
    objects = HorillaCompanyManager("company_id")
    
    class Meta:
        verbose_name = _("BIR Form 2316")
        verbose_name_plural = _("BIR Forms 2316")
        unique_together = [('employee', 'year', 'is_substituted')]
        ordering = ['-year', 'employee']
        indexes = [
            models.Index(fields=['employee', 'year'], name='bir_2316_emp_year_idx'),
            models.Index(fields=['year'], name='bir_2316_year_idx'),
        ]
    
    def __str__(self):
        return f"BIR Form 2316 - {self.employee_name} ({self.year})"
    
    @property
    def total_non_taxable(self):
        """Calculate total non-taxable compensation"""
        return (
            self.non_taxable_13th_month +
            self.non_taxable_de_minimis +
            self.non_taxable_sss +
            self.non_taxable_salaries
        )
    
    @property
    def total_taxable(self):
        """Calculate total taxable compensation"""
        return (
            self.taxable_basic_salary +
            self.taxable_13th_month +
            self.taxable_other_benefits
        )
    
    @property
    def net_taxable_compensation(self):
        """Calculate net taxable compensation after exemptions"""
        gross_taxable = self.total_taxable
        total_exemptions = self.personal_exemption + self.additional_exemption
        return max(0, gross_taxable - total_exemptions - self.premium_paid)


class PhilippinesDeMinimisBenefit(HorillaModel):
    """
    De Minimis Benefits - Non-taxable benefits per RR 10-2008
    
    These are benefits with minimal value that are exempt from withholding tax
    provided they don't exceed the prescribed limits.
    
    Annual Limits (as of 2024):
    - Monetized unused vacation leave: ₱10,000 for non-government
    - Medical cash allowance: ₱1,500/month or ₱18,000/year
    - Rice subsidy: ₱2,000/month or ₱24,000/year (or 1 sack/month)
    - Uniform/clothing allowance: ₱6,000/year
    - Laundry allowance: ₱300/month or ₱3,600/year
    - Employee achievement awards: ₱10,000/year
    - Gifts during Christmas/anniversaries: ₱5,000/year
    """
    
    BENEFIT_TYPE_CHOICES = [
        ('rice', _('Rice Subsidy (₱2,000/month max)')),
        ('clothing', _('Uniform/Clothing Allowance (₱6,000/year max)')),
        ('medical', _('Medical Cash Allowance (₱1,500/month max)')),
        ('laundry', _('Laundry Allowance (₱300/month max)')),
        ('vacation_leave', _('Monetized Unused Vacation Leave (₱10,000/year max)')),
        ('achievement', _('Achievement Awards (₱10,000/year max)')),
        ('gift', _('Gifts - Christmas/Anniversary (₱5,000/year max)')),
        ('other', _('Other De Minimis Benefits')),
    ]
    
    employee = models.ForeignKey(
        'employee.Employee',
        on_delete=models.CASCADE,
        related_name='de_minimis_benefits',
        verbose_name=_("Employee")
    )
    
    benefit_type = models.CharField(
        max_length=20,
        choices=BENEFIT_TYPE_CHOICES,
        verbose_name=_("Benefit Type")
    )
    
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Amount"),
        help_text=_("Amount of benefit given")
    )
    
    date_given = models.DateField(
        verbose_name=_("Date Given"),
        help_text=_("Date when benefit was provided")
    )
    
    description = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Description"),
        help_text=_("Additional details about the benefit")
    )
    
    is_within_limit = models.BooleanField(
        default=True,
        verbose_name=_("Within Tax-Free Limit"),
        help_text=_("Whether this benefit is within the tax-free limit")
    )
    
    taxable_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_("Taxable Amount"),
        help_text=_("Amount exceeding the tax-free limit (if any)")
    )
    
    year = models.IntegerField(
        verbose_name=_("Year"),
        help_text=_("Year for tracking annual limits")
    )
    
    month = models.IntegerField(
        verbose_name=_("Month"),
        help_text=_("Month (1-12) for tracking monthly limits")
    )
    
    company_id = models.ForeignKey(
        Company,
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )
    
    objects = HorillaCompanyManager("company_id")
    
    class Meta:
        verbose_name = _("De Minimis Benefit")
        verbose_name_plural = _("De Minimis Benefits")
        ordering = ['-date_given']
        indexes = [
            models.Index(fields=['employee', 'year'], name='deminimis_emp_year_idx'),
            models.Index(fields=['year', 'benefit_type'], name='deminimis_year_type_idx'),
        ]
    
    def __str__(self):
        return f"{self.get_benefit_type_display()} - {self.employee.get_full_name()} ({self.date_given})"
    
    def save(self, *args, **kwargs):
        """Auto-calculate year and month from date_given"""
        if self.date_given:
            self.year = self.date_given.year
            self.month = self.date_given.month
        super().save(*args, **kwargs)
    
    @classmethod
    def get_annual_limit(cls, benefit_type):
        """Get the annual tax-free limit for each benefit type"""
        limits = {
            'rice': Decimal('24000.00'),  # ₱2,000/month × 12
            'clothing': Decimal('6000.00'),
            'medical': Decimal('18000.00'),  # ₱1,500/month × 12
            'laundry': Decimal('3600.00'),  # ₱300/month × 12
            'vacation_leave': Decimal('10000.00'),
            'achievement': Decimal('10000.00'),
            'gift': Decimal('5000.00'),
            'other': Decimal('0.00'),  # No standard limit
        }
        return limits.get(benefit_type, Decimal('0.00'))
    
    @classmethod
    def get_monthly_limit(cls, benefit_type):
        """Get the monthly tax-free limit for each benefit type"""
        limits = {
            'rice': Decimal('2000.00'),
            'medical': Decimal('1500.00'),
            'laundry': Decimal('300.00'),
        }
        return limits.get(benefit_type, Decimal('0.00'))
    
    @classmethod
    def calculate_total_for_year(cls, employee, benefit_type, year):
        """Calculate total de minimis benefits of a type for an employee in a year"""
        total = cls.objects.filter(
            employee=employee,
            benefit_type=benefit_type,
            year=year
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        return total


class PhilippinesFinalPay(HorillaModel):
    """
    Model to track Final Pay (Clearance Pay) calculations for separating employees.
    
    Required by Philippine Labor Code for all types of employment termination:
    - Resignation, Retirement, End of Contract, Termination
    
    Components:
    1. Unpaid salary (work days from last payroll to separation)
    2. Pro-rated 13th month pay (YTD earnings ÷ 12)
    3. Unused leave credits conversion (cash equivalent)
    4. Separation pay (if applicable - retrenchment, redundancy, etc.)
    5. Final tax adjustment (year-to-date reconciliation)
    """
    
    SEPARATION_REASON_CHOICES = [
        ('resignation', _('Resignation')),
        ('retirement', _('Retirement')),
        ('end_of_contract', _('End of Contract')),
        ('termination', _('Termination (Just Cause)')),
        ('retrenchment', _('Retrenchment')),
        ('redundancy', _('Redundancy')),
        ('illness', _('Disease/Illness (Not Job-Related)')),
        ('closure', _('Business Closure')),
        ('other', _('Other')),
    ]
    
    employee = models.ForeignKey(
        'employee.Employee',
        on_delete=models.CASCADE,
        related_name='final_pay_records',
        verbose_name=_("Employee")
    )
    separation_date = models.DateField(
        verbose_name=_("Separation Date"),
        help_text=_("Last working day")
    )
    last_payroll_date = models.DateField(
        verbose_name=_("Last Payroll Date"),
        help_text=_("End date of last payroll processed")
    )
    separation_reason = models.CharField(
        max_length=20,
        choices=SEPARATION_REASON_CHOICES,
        verbose_name=_("Separation Reason")
    )
    
    # Unpaid Salary Component
    unpaid_days = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_("Unpaid Work Days"),
        help_text=_("Days worked after last payroll")
    )
    daily_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_("Daily Rate")
    )
    unpaid_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_("Unpaid Salary")
    )
    
    # 13th Month Pay Component
    total_basic_ytd = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_("Total Basic Salary YTD"),
        help_text=_("Total basic salary earned from Jan 1 to separation")
    )
    prorated_13th_month = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_("Pro-Rated 13th Month Pay")
    )
    months_worked = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_("Months Worked"),
        help_text=_("Months worked in current year")
    )
    
    # Leave Conversion Component
    unused_vacation_days = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_("Unused Vacation Leave Days")
    )
    unused_sick_days = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_("Unused Sick Leave Days")
    )
    leave_conversion_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_("Leave Conversion Amount")
    )
    
    # Separation Pay Component (if applicable)
    is_entitled_to_separation_pay = models.BooleanField(
        default=False,
        verbose_name=_("Entitled to Separation Pay"),
        help_text=_("Only for retrenchment, redundancy, closure, illness")
    )
    years_of_service = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_("Years of Service")
    )
    monthly_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_("Monthly Salary")
    )
    separation_pay = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_("Separation Pay"),
        help_text=_("Varies by reason: 1 month/year or 0.5 month/year")
    )
    
    # Deductions
    unpaid_loans = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_("Unpaid Loans/Advances")
    )
    other_deductions = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_("Other Deductions"),
        help_text=_("Damages, unreturned equipment, etc.")
    )
    
    # Tax Adjustment
    ytd_tax_withheld = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_("YTD Tax Withheld")
    )
    final_tax_due = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_("Final Tax Due"),
        help_text=_("Recalculated tax based on total YTD income")
    )
    tax_adjustment = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_("Tax Adjustment"),
        help_text=_("Positive = refund, Negative = additional tax")
    )
    
    # Totals
    gross_final_pay = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_("Gross Final Pay")
    )
    total_deductions = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_("Total Deductions")
    )
    net_final_pay = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_("Net Final Pay")
    )
    
    # Metadata
    calculated_by = models.ForeignKey(
        'employee.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='final_pays_calculated',
        verbose_name=_("Calculated By")
    )
    calculation_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Calculation Date")
    )
    is_paid = models.BooleanField(
        default=False,
        verbose_name=_("Paid")
    )
    payment_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Payment Date")
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_("Notes")
    )
    
    objects = HorillaCompanyManager()
    
    class Meta:
        ordering = ['-separation_date']
        verbose_name = _("Philippines Final Pay")
        verbose_name_plural = _("Philippines Final Pay Records")
        unique_together = [['employee', 'separation_date']]
    
    def __str__(self):
        return f"Final Pay - {self.employee.get_full_name()} ({self.separation_date})"
    
    def calculate_all_components(self):
        """
        Calculate all final pay components based on Philippine Labor Law.
        
        Returns dict with all calculated values.
        """
        # 1. Unpaid Salary
        self.unpaid_salary = self.unpaid_days * self.daily_rate
        
        # 2. Pro-rated 13th Month Pay
        # Formula: (Total Basic Salary YTD) / 12
        if self.total_basic_ytd > 0:
            self.prorated_13th_month = self.total_basic_ytd / Decimal('12.00')
        
        # 3. Leave Conversion
        # Convert unused leaves to cash at daily rate
        total_leave_days = self.unused_vacation_days + self.unused_sick_days
        self.leave_conversion_amount = total_leave_days * self.daily_rate
        
        # 4. Separation Pay (if applicable)
        if self.is_entitled_to_separation_pay:
            # Retrenchment, Redundancy, Closure, Illness: 1 month/year (or 0.5 month/year for illness)
            if self.separation_reason in ['retrenchment', 'redundancy', 'closure']:
                # 1 month salary per year of service
                self.separation_pay = self.monthly_salary * self.years_of_service
            elif self.separation_reason == 'illness':
                # 0.5 month salary per year of service
                self.separation_pay = (self.monthly_salary * Decimal('0.5')) * self.years_of_service
        else:
            self.separation_pay = Decimal('0.00')
        
        # 5. Calculate Gross Final Pay
        self.gross_final_pay = (
            self.unpaid_salary +
            self.prorated_13th_month +
            self.leave_conversion_amount +
            self.separation_pay
        )
        
        # 6. Calculate Deductions
        self.total_deductions = (
            self.unpaid_loans +
            self.other_deductions +
            max(Decimal('0.00'), -self.tax_adjustment)  # Only deduct if negative (additional tax)
        )
        
        # 7. Calculate Net Final Pay
        refund_amount = max(Decimal('0.00'), self.tax_adjustment)  # Only add if positive (refund)
        self.net_final_pay = self.gross_final_pay - self.total_deductions + refund_amount
        
        return {
            'unpaid_salary': self.unpaid_salary,
            'prorated_13th_month': self.prorated_13th_month,
            'leave_conversion': self.leave_conversion_amount,
            'separation_pay': self.separation_pay,
            'gross_final_pay': self.gross_final_pay,
            'total_deductions': self.total_deductions,
            'tax_adjustment': self.tax_adjustment,
            'net_final_pay': self.net_final_pay,
        }
    
    def save(self, *args, **kwargs):
        """Auto-calculate before saving"""
        self.calculate_all_components()
        super().save(*args, **kwargs)


class PhilippinesGovernmentRemittance(HorillaModel):
    """
    Model to generate government remittance forms (SSS R3, PhilHealth RF-1, Pag-IBIG MCRF).
    
    Required monthly submissions to government agencies.
    - SSS Form R3: Collection List (monthly remittance)
    - PhilHealth Form RF-1: Premium Remittance Form
    - Pag-IBIG MCRF: Member Contribution Remittance Form
    """
    
    FORM_TYPE_CHOICES = [
        ('sss_r3', _('SSS Form R3 (Collection List)')),
        ('philhealth_rf1', _('PhilHealth Form RF-1')),
        ('pagibig_mcrf', _('Pag-IBIG MCRF')),
    ]
    
    PERIOD_TYPE_CHOICES = [
        ('monthly', _('Monthly')),
        ('quarterly', _('Quarterly')),
    ]
    
    form_type = models.CharField(
        max_length=20,
        choices=FORM_TYPE_CHOICES,
        verbose_name=_("Form Type")
    )
    period_type = models.CharField(
        max_length=10,
        choices=PERIOD_TYPE_CHOICES,
        default='monthly',
        verbose_name=_("Period Type")
    )
    year = models.IntegerField(
        verbose_name=_("Year")
    )
    month = models.IntegerField(
        verbose_name=_("Month"),
        help_text=_("1-12 for monthly, 1/4/7/10 for quarterly")
    )
    
    # Employer Information
    employer_name = models.CharField(
        max_length=200,
        verbose_name=_("Employer Name")
    )
    employer_id = models.CharField(
        max_length=50,
        verbose_name=_("Employer ID/Number"),
        help_text=_("SSS Number, PhilHealth Number, or Pag-IBIG Number")
    )
    employer_address = models.TextField(
        verbose_name=_("Employer Address")
    )
    
    # Summary Totals
    total_employees = models.IntegerField(
        default=0,
        verbose_name=_("Total Employees")
    )
    total_employee_contribution = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_("Total Employee Contribution")
    )
    total_employer_contribution = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_("Total Employer Contribution")
    )
    total_ec_contribution = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_("Total EC (Employees Compensation)"),
        help_text=_("SSS only")
    )
    grand_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_("Grand Total")
    )
    
    # Metadata
    generated_by = models.ForeignKey(
        'employee.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='government_forms_generated',
        verbose_name=_("Generated By")
    )
    generated_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Generated Date")
    )
    is_submitted = models.BooleanField(
        default=False,
        verbose_name=_("Submitted to Agency")
    )
    submission_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Submission Date")
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_("Notes")
    )
    
    objects = HorillaCompanyManager()
    
    class Meta:
        ordering = ['-year', '-month']
        verbose_name = _("Philippines Government Remittance")
        verbose_name_plural = _("Philippines Government Remittances")
        unique_together = [['form_type', 'year', 'month']]
    
    def __str__(self):
        month_name = [
            'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
            'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
        ][self.month - 1]
        return f"{self.get_form_type_display()} - {month_name} {self.year}"
    
    def get_period_display_text(self):
        """Get human-readable period text"""
        month_names = {
            1: 'January', 2: 'February', 3: 'March', 4: 'April',
            5: 'May', 6: 'June', 7: 'July', 8: 'August',
            9: 'September', 10: 'October', 11: 'November', 12: 'December'
        }
        
        if self.period_type == 'monthly':
            return f"{month_names[self.month]} {self.year}"
        else:
            # Quarterly
            quarter = (self.month - 1) // 3 + 1
            return f"Q{quarter} {self.year}"
    
    def calculate_totals(self):
        """Calculate totals from related employee contributions"""
        entries = self.employee_entries.all()
        
        self.total_employees = entries.count()
        self.total_employee_contribution = entries.aggregate(
            total=Sum('employee_contribution')
        )['total'] or Decimal('0.00')
        self.total_employer_contribution = entries.aggregate(
            total=Sum('employer_contribution')
        )['total'] or Decimal('0.00')
        self.total_ec_contribution = entries.aggregate(
            total=Sum('ec_contribution')
        )['total'] or Decimal('0.00')
        
        self.grand_total = (
            self.total_employee_contribution +
            self.total_employer_contribution +
            self.total_ec_contribution
        )


class PhilippinesGovernmentRemittanceEntry(HorillaModel):
    """
    Individual employee entries for government remittance forms.
    Each entry represents one employee's contribution for the period.
    """
    
    remittance = models.ForeignKey(
        PhilippinesGovernmentRemittance,
        on_delete=models.CASCADE,
        related_name='employee_entries',
        verbose_name=_("Remittance Form")
    )
    employee = models.ForeignKey(
        'employee.Employee',
        on_delete=models.CASCADE,
        verbose_name=_("Employee")
    )
    
    # Employee Identifiers
    employee_id_number = models.CharField(
        max_length=50,
        verbose_name=_("Employee ID Number"),
        help_text=_("SSS Number, PhilHealth Number, or Pag-IBIG Number")
    )
    employee_full_name = models.CharField(
        max_length=200,
        verbose_name=_("Employee Full Name")
    )
    
    # Salary Information
    monthly_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_("Monthly Salary Credit")
    )
    
    # Contribution Breakdown
    employee_contribution = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_("Employee Contribution")
    )
    employer_contribution = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_("Employer Contribution")
    )
    ec_contribution = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_("EC Contribution"),
        help_text=_("SSS Employees Compensation - always ₱10")
    )
    total_contribution = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_("Total Contribution")
    )
    
    objects = HorillaCompanyManager()
    
    class Meta:
        ordering = ['employee_full_name']
        verbose_name = _("Government Remittance Entry")
        verbose_name_plural = _("Government Remittance Entries")
        unique_together = [['remittance', 'employee']]
    
    def __str__(self):
        return f"{self.employee_full_name} - {self.remittance}"
    
    def save(self, *args, **kwargs):
        """Auto-calculate total before saving"""
        self.total_contribution = (
            self.employee_contribution +
            self.employer_contribution +
            self.ec_contribution
        )
        super().save(*args, **kwargs)
