"""
report_forms.py

Forms for payroll reporting system
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from payroll.models.report_models import (
    ReportCategory,
    ReportTemplate,
    ReportSchedule,
    BankFileConfiguration
)
from base.models import Company, Department
from employee.models import Employee


class ReportCategoryForm(forms.ModelForm):
    """
    Form for creating/updating report categories
    """
    class Meta:
        model = ReportCategory
        fields = ['name', 'description', 'icon', 'order', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., bi-file-earmark-text'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ReportTemplateForm(forms.ModelForm):
    """
    Form for creating/updating report templates
    """
    class Meta:
        model = ReportTemplate
        fields = [
            'name', 'category', 'report_type', 'description', 
            'output_format', 'is_active', 'requires_date_range',
            'requires_company', 'requires_department', 'requires_employee',
            'columns_config', 'filters_config', 'sorting_config',
            'template_path', 'accessible_by_all', 'accessible_departments'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'report_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'output_format': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'requires_date_range': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'requires_company': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'requires_department': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'requires_employee': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'columns_config': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': '{"columns": []}'}),
            'filters_config': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': '{"filters": []}'}),
            'sorting_config': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '{"sort_by": "field_name"}'}),
            'template_path': forms.TextInput(attrs={'class': 'form-control'}),
            'accessible_by_all': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'accessible_departments': forms.SelectMultiple(attrs={'class': 'form-select', 'size': 5}),
        }


class ReportGenerationForm(forms.Form):
    """
    Dynamic form for generating reports based on template requirements
    """
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label=_('Date From')
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label=_('Date To')
    )
    company = forms.ModelChoiceField(
        queryset=Company.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_('Company')
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_('Department')
    )
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_('Employee')
    )
    
    # Additional filters
    include_inactive = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label=_('Include Inactive Employees')
    )
    group_by = forms.ChoiceField(
        required=False,
        choices=[
            ('', _('No Grouping')),
            ('department', _('Department')),
            ('company', _('Company')),
            ('position', _('Position')),
            ('employee_type', _('Employee Type')),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_('Group By')
    )
    
    def __init__(self, *args, report_template=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        if report_template:
            # Make fields required based on template configuration
            if report_template.requires_date_range:
                self.fields['date_from'].required = True
                self.fields['date_to'].required = True
            else:
                del self.fields['date_from']
                del self.fields['date_to']
            
            if not report_template.requires_company:
                del self.fields['company']
            
            if not report_template.requires_department:
                del self.fields['department']
            
            if not report_template.requires_employee:
                del self.fields['employee']


class ReportScheduleForm(forms.ModelForm):
    """
    Form for creating/updating report schedules
    """
    class Meta:
        model = ReportSchedule
        fields = [
            'report_template', 'name', 'frequency', 'is_active',
            'next_run_date', 'email_recipients', 'email_subject',
            'email_body', 'company', 'department'
        ]
        widgets = {
            'report_template': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'frequency': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'next_run_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'email_recipients': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'email1@example.com, email2@example.com'
            }),
            'email_subject': forms.TextInput(attrs={'class': 'form-control'}),
            'email_body': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'company': forms.Select(attrs={'class': 'form-select'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
        }


class BankFileConfigurationForm(forms.ModelForm):
    """
    Form for creating/updating bank file configurations
    """
    class Meta:
        model = BankFileConfiguration
        fields = [
            'name', 'bank', 'file_format', 'company',
            'delimiter', 'include_header', 'date_format',
            'field_mapping', 'file_name_template', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'bank': forms.Select(attrs={'class': 'form-select'}),
            'file_format': forms.Select(attrs={'class': 'form-select'}),
            'company': forms.Select(attrs={'class': 'form-select'}),
            'delimiter': forms.TextInput(attrs={'class': 'form-control'}),
            'include_header': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'date_format': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '%Y-%m-%d'
            }),
            'field_mapping': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 10,
                'placeholder': '{"employee_id": "Employee ID", "name": "Employee Name", ...}'
            }),
            'file_name_template': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'payroll_{date}.csv'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class QuickReportFilterForm(forms.Form):
    """
    Quick filter form for report dashboard
    """
    report_category = forms.ModelChoiceField(
        queryset=ReportCategory.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_('Category')
    )
    output_format = forms.ChoiceField(
        required=False,
        choices=[
            ('', _('All Formats')),
            ('pdf', _('PDF')),
            ('excel', _('Excel')),
            ('csv', _('CSV')),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_('Format')
    )
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Search reports...')
        }),
        label=_('Search')
    )
