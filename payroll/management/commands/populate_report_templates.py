"""
Management command to populate initial report templates
"""

from django.core.management.base import BaseCommand
from payroll.models.report_models import ReportCategory, ReportTemplate


class Command(BaseCommand):
    help = 'Populate initial report templates and categories'

    def handle(self, *args, **options):
        self.stdout.write('Creating report categories...')
        
        # Create categories
        categories_data = [
            {
                'name': 'Payroll Reports',
                'description': 'Core payroll reports including registers and summaries',
                'icon': 'bi-cash-stack',
                'order': 1
            },
            {
                'name': 'Statutory Reports',
                'description': 'Government-mandated reports (SSS, PhilHealth, PAG-IBIG, BIR)',
                'icon': 'bi-file-earmark-ruled',
                'order': 2
            },
            {
                'name': 'Bank Files',
                'description': 'Bank transfer files and advice lists',
                'icon': 'bi-bank',
                'order': 3
            },
            {
                'name': 'Validation Reports',
                'description': 'Reports for validating payroll calculations',
                'icon': 'bi-check2-square',
                'order': 4
            },
            {
                'name': 'Employee Reports',
                'description': 'Employee-specific reports and certificates',
                'icon': 'bi-person-badge',
                'order': 5
            },
            {
                'name': 'Analytics',
                'description': 'Analysis and demographic reports',
                'icon': 'bi-graph-up',
                'order': 6
            },
        ]
        
        categories = {}
        for cat_data in categories_data:
            category, created = ReportCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults=cat_data
            )
            categories[cat_data['name']] = category
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Created category: {category.name}'))
            else:
                self.stdout.write(f'  Category already exists: {category.name}')
        
        self.stdout.write('\nCreating report templates...')
        
        # Create report templates
        templates_data = [
            # Payroll Reports
            {
                'name': 'Payroll Register (PDF)',
                'category': categories['Payroll Reports'],
                'report_type': 'payroll_register',
                'description': 'Comprehensive payroll register with all employee earnings and deductions',
                'output_format': 'pdf',
                'requires_date_range': True,
                'requires_company': False,
                'requires_department': False,
            },
            {
                'name': 'Payroll Register (Excel)',
                'category': categories['Payroll Reports'],
                'report_type': 'payroll_register',
                'description': 'Editable Excel format payroll register for further analysis',
                'output_format': 'excel',
                'requires_date_range': True,
                'requires_company': False,
                'requires_department': False,
            },
            {
                'name': 'Variance Report',
                'category': categories['Payroll Reports'],
                'report_type': 'variance_report',
                'description': 'Compare current period payroll vs previous period',
                'output_format': 'pdf',
                'requires_date_range': True,
            },
            {
                'name': 'Basic Salary Report',
                'category': categories['Payroll Reports'],
                'report_type': 'basic_salary_report',
                'description': 'Report showing basic salaries only',
                'output_format': 'excel',
                'requires_date_range': True,
            },
            
            # Statutory Reports
            {
                'name': 'SSS Contribution Report',
                'category': categories['Statutory Reports'],
                'report_type': 'sss_report',
                'description': 'SSS contribution report for remittance',
                'output_format': 'excel',
                'requires_date_range': True,
            },
            {
                'name': 'PhilHealth Contribution Report',
                'category': categories['Statutory Reports'],
                'report_type': 'philhealth_report',
                'description': 'PhilHealth contribution report for remittance',
                'output_format': 'excel',
                'requires_date_range': True,
            },
            {
                'name': 'PAG-IBIG Contribution Report',
                'category': categories['Statutory Reports'],
                'report_type': 'pagibig_report',
                'description': 'PAG-IBIG contribution report for remittance',
                'output_format': 'excel',
                'requires_date_range': True,
            },
            {
                'name': 'BIR Alphalist',
                'category': categories['Statutory Reports'],
                'report_type': 'bir_alphalist',
                'description': 'BIR Alphalist of Employees for tax filing',
                'output_format': 'excel',
                'requires_date_range': True,
            },
            {
                'name': 'BIR Form 2316',
                'category': categories['Statutory Reports'],
                'report_type': 'bir_2316',
                'description': 'Certificate of Compensation Payment/Tax Withheld',
                'output_format': 'pdf',
                'requires_date_range': True,
                'requires_employee': True,
            },
            
            # Bank Files
            {
                'name': 'Bank File (CSV)',
                'category': categories['Bank Files'],
                'report_type': 'bank_file',
                'description': 'Bank transfer file in CSV format',
                'output_format': 'csv',
                'requires_date_range': True,
            },
            {
                'name': 'Bank Advice List',
                'category': categories['Bank Files'],
                'report_type': 'bank_advice_list',
                'description': 'Detailed list of bank transfers',
                'output_format': 'pdf',
                'requires_date_range': True,
            },
            
            # Validation Reports
            {
                'name': 'Net Pay Validation',
                'category': categories['Validation Reports'],
                'report_type': 'net_pay_validation',
                'description': 'Validate net pay calculations',
                'output_format': 'excel',
                'requires_date_range': True,
            },
            {
                'name': 'Withholding Tax Validation',
                'category': categories['Validation Reports'],
                'report_type': 'withholding_tax_validation',
                'description': 'Validate withholding tax computations',
                'output_format': 'excel',
                'requires_date_range': True,
            },
            {
                'name': 'Employer Contributions Summary',
                'category': categories['Validation Reports'],
                'report_type': 'employer_contributions',
                'description': 'Summary of all employer contributions',
                'output_format': 'excel',
                'requires_date_range': True,
            },
            
            # Employee Reports
            {
                'name': 'Certificate of Contribution',
                'category': categories['Employee Reports'],
                'report_type': 'certificate_contribution',
                'description': 'Certificate of government contributions for employees',
                'output_format': 'pdf',
                'requires_date_range': True,
                'requires_employee': True,
            },
            {
                'name': 'Certificate of Loan',
                'category': categories['Employee Reports'],
                'report_type': 'certificate_loan',
                'description': 'Certificate of loan deductions',
                'output_format': 'pdf',
                'requires_employee': True,
            },
            {
                'name': '13th Month Pay Report',
                'category': categories['Employee Reports'],
                'report_type': '13th_month_pay',
                'description': '13th month pay computation report',
                'output_format': 'excel',
                'requires_date_range': True,
            },
            
            # Analytics
            {
                'name': 'Demographic Report',
                'category': categories['Analytics'],
                'report_type': 'demographic_report',
                'description': 'Employee demographics and statistics',
                'output_format': 'excel',
                'requires_date_range': False,
            },
            {
                'name': 'Cost Center Analysis',
                'category': categories['Analytics'],
                'report_type': 'cost_center_analysis',
                'description': 'Payroll costs by department/cost center',
                'output_format': 'excel',
                'requires_date_range': True,
            },
            {
                'name': 'Headcount Report',
                'category': categories['Analytics'],
                'report_type': 'headcount_report',
                'description': 'Employee headcount analysis',
                'output_format': 'excel',
                'requires_date_range': False,
            },
        ]
        
        for template_data in templates_data:
            template, created = ReportTemplate.objects.get_or_create(
                name=template_data['name'],
                defaults=template_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Created template: {template.name}'))
            else:
                self.stdout.write(f'  Template already exists: {template.name}')
        
        self.stdout.write(self.style.SUCCESS('\n✓ Report templates population completed!'))
