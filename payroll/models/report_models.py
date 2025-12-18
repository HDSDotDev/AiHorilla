"""
report_models.py

Models for payroll reporting system - competitive with Sprout
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from horilla.models import HorillaModel
from base.models import Company, Department
from employee.models import Employee


class ReportCategory(HorillaModel):
    """
    Report categories for organizing reports
    """
    name = models.CharField(
        max_length=100,
        verbose_name=_("Category Name"),
        help_text=_("e.g., Payroll, Statutory, Bank Files, etc.")
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Description")
    )
    icon = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name=_("Icon Class"),
        help_text=_("CSS icon class for display")
    )
    order = models.IntegerField(
        default=0,
        verbose_name=_("Display Order")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active")
    )

    class Meta:
        ordering = ['order', 'name']
        verbose_name = _("Report Category")
        verbose_name_plural = _("Report Categories")

    def __str__(self):
        return self.name


class ReportTemplate(HorillaModel):
    """
    Configurable report templates
    """
    REPORT_TYPE_CHOICES = [
        ('payroll_register', _('Payroll Register')),
        ('variance_report', _('Variance Report')),
        ('employer_contributions', _('Employer Contributions')),
        ('bank_advice_list', _('Bank Advice List')),
        ('bank_file', _('Bank File')),
        ('sss_report', _('SSS Report')),
        ('philhealth_report', _('PhilHealth Report')),
        ('pagibig_report', _('PAG-IBIG Report')),
        ('bir_report', _('BIR Report')),
        ('bir_alphalist', _('BIR Alphalist')),
        ('bir_1601c', _('BIR 1601C')),
        ('bir_2316', _('BIR 2316')),
        ('net_pay_validation', _('Net Pay Validation')),
        ('basic_salary_report', _('Basic Salary Report')),
        ('recurring_adjustment_income', _('Recurring Adjustment Income')),
        ('recurring_adjustment_deduction', _('Recurring Adjustment Deduction')),
        ('withholding_tax_validation', _('Withholding Tax Validation')),
        ('certificate_contribution', _('Certificate of Contribution')),
        ('certificate_loan', _('Certificate of Loan')),
        ('statutory_report', _('Statutory Report')),
        ('demographic_report', _('Demographic Report')),
        ('leave_credits_report', _('Leave Credits Report')),
        ('attendance_summary', _('Attendance Summary')),
        ('overtime_report', _('Overtime Report')),
        ('13th_month_pay', _('13th Month Pay Report')),
        ('year_end_report', _('Year End Report')),
        ('cost_center_analysis', _('Cost Center Analysis')),
        ('headcount_report', _('Headcount Report')),
        ('turnover_report', _('Turnover Report')),
        ('custom', _('Custom Report')),
    ]

    FORMAT_CHOICES = [
        ('pdf', _('PDF')),
        ('excel', _('Excel')),
        ('csv', _('CSV')),
        ('dat', _('DAT File')),
        ('txt', _('Text File')),
        ('json', _('JSON')),
    ]

    name = models.CharField(
        max_length=200,
        verbose_name=_("Report Name")
    )
    category = models.ForeignKey(
        ReportCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reports',
        verbose_name=_("Category")
    )
    report_type = models.CharField(
        max_length=50,
        choices=REPORT_TYPE_CHOICES,
        verbose_name=_("Report Type")
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Description")
    )
    output_format = models.CharField(
        max_length=20,
        choices=FORMAT_CHOICES,
        default='pdf',
        verbose_name=_("Output Format")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active")
    )
    requires_date_range = models.BooleanField(
        default=True,
        verbose_name=_("Requires Date Range")
    )
    requires_company = models.BooleanField(
        default=False,
        verbose_name=_("Requires Company Selection")
    )
    requires_department = models.BooleanField(
        default=False,
        verbose_name=_("Requires Department Selection")
    )
    requires_employee = models.BooleanField(
        default=False,
        verbose_name=_("Requires Employee Selection")
    )
    
    # Configuration fields
    columns_config = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Columns Configuration"),
        help_text=_("JSON configuration for report columns")
    )
    filters_config = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Filters Configuration"),
        help_text=_("JSON configuration for report filters")
    )
    sorting_config = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Sorting Configuration"),
        help_text=_("JSON configuration for default sorting")
    )
    template_path = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_("Custom Template Path"),
        help_text=_("Path to custom template file")
    )
    
    # Access control
    accessible_by_all = models.BooleanField(
        default=False,
        verbose_name=_("Accessible by All Users")
    )
    accessible_departments = models.ManyToManyField(
        Department,
        blank=True,
        related_name='accessible_reports',
        verbose_name=_("Accessible Departments")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'name']
        verbose_name = _("Report Template")
        verbose_name_plural = _("Report Templates")

    def __str__(self):
        return f"{self.name} ({self.get_output_format_display()})"


class ReportSchedule(HorillaModel):
    """
    Scheduled report generation and delivery
    """
    FREQUENCY_CHOICES = [
        ('daily', _('Daily')),
        ('weekly', _('Weekly')),
        ('biweekly', _('Bi-weekly')),
        ('monthly', _('Monthly')),
        ('quarterly', _('Quarterly')),
        ('yearly', _('Yearly')),
    ]

    report_template = models.ForeignKey(
        ReportTemplate,
        on_delete=models.CASCADE,
        related_name='schedules',
        verbose_name=_("Report Template")
    )
    name = models.CharField(
        max_length=200,
        verbose_name=_("Schedule Name")
    )
    frequency = models.CharField(
        max_length=20,
        choices=FREQUENCY_CHOICES,
        verbose_name=_("Frequency")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active")
    )
    next_run_date = models.DateTimeField(
        verbose_name=_("Next Run Date")
    )
    last_run_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Last Run Date")
    )
    
    # Email delivery
    email_recipients = models.TextField(
        verbose_name=_("Email Recipients"),
        help_text=_("Comma-separated email addresses")
    )
    email_subject = models.CharField(
        max_length=255,
        verbose_name=_("Email Subject")
    )
    email_body = models.TextField(
        blank=True,
        verbose_name=_("Email Body")
    )
    
    # Filter settings
    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Company")
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Department")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _("Report Schedule")
        verbose_name_plural = _("Report Schedules")

    def __str__(self):
        return f"{self.name} - {self.get_frequency_display()}"


class GeneratedReport(HorillaModel):
    """
    History of generated reports
    """
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('processing', _('Processing')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
    ]

    report_template = models.ForeignKey(
        ReportTemplate,
        on_delete=models.SET_NULL,
        null=True,
        related_name='generated_reports',
        verbose_name=_("Report Template")
    )
    generated_by = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        related_name='generated_reports',
        verbose_name=_("Generated By")
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name=_("Status")
    )
    file_path = models.FileField(
        upload_to='payroll_reports/%Y/%m/%d/',
        null=True,
        blank=True,
        verbose_name=_("Report File")
    )
    file_name = models.CharField(
        max_length=255,
        verbose_name=_("File Name")
    )
    
    # Filter parameters used
    date_from = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Date From")
    )
    date_to = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Date To")
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Company")
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Department")
    )
    employee = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reports_about',
        verbose_name=_("Employee")
    )
    
    # Generation metadata
    parameters = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Generation Parameters")
    )
    error_message = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Error Message")
    )
    generated_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Completed At")
    )
    processing_time = models.DurationField(
        null=True,
        blank=True,
        verbose_name=_("Processing Time")
    )

    class Meta:
        ordering = ['-generated_at']
        verbose_name = _("Generated Report")
        verbose_name_plural = _("Generated Reports")

    def __str__(self):
        return f"{self.file_name} - {self.status}"


class BankFileConfiguration(HorillaModel):
    """
    Configuration for bank file exports
    """
    BANK_CHOICES = [
        ('bdo', _('BDO')),
        ('bpi', _('BPI')),
        ('metrobank', _('Metrobank')),
        ('security_bank', _('Security Bank')),
        ('unionbank', _('UnionBank')),
        ('landbank', _('Landbank')),
        ('pnb', _('PNB')),
        ('rcbc', _('RCBC')),
        ('eastwest', _('EastWest Bank')),
        ('chinabank', _('China Bank')),
        ('generic', _('Generic Format')),
    ]

    FILE_FORMAT_CHOICES = [
        ('csv', _('CSV')),
        ('txt', _('Text File')),
        ('dat', _('DAT File')),
        ('excel', _('Excel')),
    ]

    name = models.CharField(
        max_length=200,
        verbose_name=_("Configuration Name")
    )
    bank = models.CharField(
        max_length=50,
        choices=BANK_CHOICES,
        verbose_name=_("Bank")
    )
    file_format = models.CharField(
        max_length=20,
        choices=FILE_FORMAT_CHOICES,
        default='csv',
        verbose_name=_("File Format")
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='bank_configs',
        verbose_name=_("Company")
    )
    
    # File structure configuration
    delimiter = models.CharField(
        max_length=10,
        default=',',
        verbose_name=_("Delimiter"),
        help_text=_("Field delimiter for text files")
    )
    include_header = models.BooleanField(
        default=True,
        verbose_name=_("Include Header Row")
    )
    date_format = models.CharField(
        max_length=50,
        default='%Y-%m-%d',
        verbose_name=_("Date Format"),
        help_text=_("Python strftime format")
    )
    
    # Field mapping
    field_mapping = models.JSONField(
        default=dict,
        verbose_name=_("Field Mapping"),
        help_text=_("Maps internal fields to bank file columns")
    )
    
    # File naming
    file_name_template = models.CharField(
        max_length=255,
        default='payroll_{date}.csv',
        verbose_name=_("File Name Template"),
        help_text=_("Use {date}, {company}, etc. as placeholders")
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active")
    )

    class Meta:
        ordering = ['bank', 'name']
        verbose_name = _("Bank File Configuration")
        verbose_name_plural = _("Bank File Configurations")

    def __str__(self):
        return f"{self.get_bank_display()} - {self.name}"
