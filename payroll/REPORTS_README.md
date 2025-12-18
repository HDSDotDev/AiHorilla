# Payroll Reports Module

## Overview

The Payroll Reports module is a comprehensive, enterprise-grade reporting system designed to compete with leading HRIS platforms like Sprout. It provides flexible, configurable report generation with support for multiple formats and statutory compliance.

## Features

### Core Features
- **Multiple Report Formats**: PDF, Excel, CSV, DAT, TXT, JSON
- **Configurable Templates**: Create custom report templates with flexible configurations
- **Report Categories**: Organize reports into logical categories for easy navigation
- **Report History**: Track all generated reports with full audit trail
- **Scheduled Reports**: Automate report generation and email delivery
- **Bank File Generation**: Export payroll data in various bank formats
- **Access Control**: Fine-grained permissions for reports by department

### Report Types

#### 1. Payroll Reports
- **Payroll Register** (PDF/Excel): Comprehensive payroll register with all earnings and deductions
- **Variance Report**: Period-over-period comparison
- **Basic Salary Report**: Salary breakdown
- **Recurring Adjustments**: Income and deduction summaries

#### 2. Statutory Reports (Philippines)
- **SSS Report**: Social Security System contributions
- **PhilHealth Report**: Health insurance contributions
- **PAG-IBIG Report**: Home Development Mutual Fund contributions
- **BIR Reports**: 
  - Alphalist of Employees
  - Form 2316 (Certificate of Compensation)
  - Form 1601C (Monthly Remittance)
- **Statutory Summary**: Combined statutory report

#### 3. Bank Files
- **Bank Transfer Files**: CSV/DAT/TXT formats
- **Bank Advice List**: Detailed transfer documentation
- **Multiple Bank Support**: BDO, BPI, Metrobank, Security Bank, UnionBank, etc.

#### 4. Validation Reports
- **Net Pay Validation**: Verify net pay calculations
- **Withholding Tax Validation**: Tax computation verification
- **Employer Contributions**: Summary of employer share

#### 5. Employee Reports
- **Certificate of Contribution**: Individual contribution certificates
- **Certificate of Loan**: Loan deduction certificates
- **13th Month Pay**: Annual 13th month computation
- **Year-End Reports**: Annual summaries

#### 6. Analytics
- **Demographic Report**: Employee statistics and demographics
- **Cost Center Analysis**: Payroll costs by department
- **Headcount Report**: Employee count analysis
- **Turnover Report**: Employee turnover metrics

## Installation

### 1. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 2. Populate Initial Templates
```bash
python manage.py populate_report_templates
```

### 3. Install Required Dependencies
```bash
pip install reportlab  # For PDF generation
pip install openpyxl   # For Excel generation
```

## Usage

### Accessing Reports
1. Navigate to **Payroll → Reports** from the main menu
2. Browse reports by category
3. Click on a report to configure and generate

### Generating a Report
1. Select a report template
2. Configure parameters:
   - Date range (if required)
   - Company/Department filters
   - Additional options
3. Click "Generate Report"
4. Download the generated file

### Managing Report Templates (Admin)
1. Go to **Reports → Manage Templates**
2. Create new templates or edit existing ones
3. Configure:
   - Report type and format
   - Required parameters
   - Access permissions
   - Custom configurations

### Scheduling Reports
1. Navigate to **Reports → Schedules**
2. Create a new schedule
3. Configure:
   - Report template
   - Frequency (daily, weekly, monthly, etc.)
   - Email recipients
   - Filter parameters
4. Reports will be generated and emailed automatically

### Bank File Configuration
1. Go to **Reports → Bank Configuration**
2. Create a configuration for your bank
3. Set up field mapping and file format
4. Use in bank file reports

## Configuration

### Report Template Configuration

```python
{
    "columns_config": {
        "columns": [
            {"field": "employee_id", "label": "ID", "width": 10},
            {"field": "employee_name", "label": "Name", "width": 30},
            {"field": "basic_pay", "label": "Basic Pay", "width": 15, "format": "currency"}
        ]
    },
    "filters_config": {
        "filters": [
            {"field": "department", "type": "select"},
            {"field": "employee_type", "type": "select"}
        ]
    },
    "sorting_config": {
        "sort_by": "employee_id",
        "order": "asc"
    }
}
```

### Bank File Field Mapping

```python
{
    "field_mapping": {
        "employee_id": "Employee ID",
        "employee_name": "Full Name",
        "bank_account": "Account Number",
        "net_pay": "Amount",
        "email": "Email Address"
    }
}
```

## API Endpoints

### REST API (if enabled)
- `GET /payroll/reports/api/statistics/` - Get report statistics
- `POST /payroll/reports/export-data/` - Export raw report data as JSON

## Customization

### Adding a New Report Type

1. **Add report type to models**:
```python
REPORT_TYPE_CHOICES = [
    # ... existing types
    ('my_custom_report', _('My Custom Report')),
]
```

2. **Create generator function**:
```python
def generate_my_custom_report(parameters, generated_report):
    # Report generation logic
    return response
```

3. **Register in report_views.py**:
```python
generators = {
    'my_custom_report': {
        'pdf': generate_my_custom_report,
    },
}
```

### Custom Templates
Place custom report templates in:
```
payroll/templates/payroll/reports/custom/
```

Reference in ReportTemplate:
```python
template_path = 'payroll/reports/custom/my_report.html'
```

## Database Models

### ReportCategory
Organizes reports into categories

### ReportTemplate
Defines report structure and configuration

### ReportSchedule
Automated report generation schedules

### GeneratedReport
History of all generated reports

### BankFileConfiguration
Bank-specific file format configurations

## Permissions

Reports respect Django's permission system:
- `payroll.view_reporttemplate` - View reports
- `payroll.add_reporttemplate` - Create templates
- `payroll.change_reporttemplate` - Edit templates
- `payroll.delete_reporttemplate` - Delete templates

Department-level access can be configured per report template.

## Performance Considerations

- Large reports are generated asynchronously (if Celery is configured)
- Reports are cached for quick re-download
- Database queries are optimized with select_related/prefetch_related
- Pagination for large datasets

## Troubleshooting

### PDF Generation Errors
Ensure ReportLab is installed:
```bash
pip install reportlab
```

### Excel Generation Errors
Ensure openpyxl is installed:
```bash
pip install openpyxl
```

### Missing Data
- Check date range parameters
- Verify payslip status (should be 'confirmed')
- Check company/department filters

## Future Enhancements

- [ ] Interactive dashboard with charts
- [ ] Report comparison tool
- [ ] Advanced filtering options
- [ ] Report templates marketplace
- [ ] Multi-language support for reports
- [ ] Digital signatures for official reports
- [ ] Integration with external accounting systems

## Support

For issues or questions:
1. Check the documentation
2. Review error logs in GeneratedReport
3. Contact system administrator

---

**Competitive with Sprout**: This module matches and exceeds Sprout's reporting capabilities with:
- More flexible configuration
- More report types
- Better customization options
- Modern, intuitive UI
- Open-source and extensible
