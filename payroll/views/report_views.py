"""
report_views.py

Views for payroll reporting system - competitive with Sprout
"""

import csv
import json
from datetime import datetime, timedelta
from io import BytesIO

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum, Count, Avg
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods

from base.methods import get_key_instances
from base.models import Company, Department
from employee.models import Employee
from payroll.models.models import Payslip, Contract
from payroll.models.report_models import (
    ReportCategory,
    ReportTemplate,
    ReportSchedule,
    GeneratedReport,
    BankFileConfiguration
)
from payroll.forms.report_forms import (
    ReportTemplateForm,
    ReportGenerationForm,
    ReportScheduleForm,
    BankFileConfigurationForm
)

# Import report generators
from payroll.methods.report_generators import (
    generate_payroll_register_pdf,
    generate_payroll_register_excel,
    generate_variance_report,
    generate_employer_contributions,
    generate_bank_advice_list,
    generate_bank_file,
    generate_sss_report,
    generate_philhealth_report,
    generate_pagibig_report,
    generate_bir_report,
    generate_net_pay_validation,
    generate_basic_salary_report,
    generate_withholding_tax_validation,
    generate_certificate_contribution,
    generate_demographic_report,
)


@login_required
def report_dashboard(request):
    """
    Main dashboard for reports module
    """
    categories = ReportCategory.objects.filter(is_active=True)
    reports = ReportTemplate.objects.filter(is_active=True)
    recent_reports = GeneratedReport.objects.filter(
        generated_by__employee_user_id=request.user
    ).order_by('-generated_at')[:10]
    
    context = {
        'categories': categories,
        'reports': reports,
        'recent_reports': recent_reports,
    }
    return render(request, 'payroll/reports/dashboard.html', context)


@login_required
def report_category_view(request, category_id=None):
    """
    View reports by category
    """
    if category_id:
        category = get_object_or_404(ReportCategory, id=category_id)
        reports = ReportTemplate.objects.filter(
            category=category,
            is_active=True
        )
    else:
        category = None
        reports = ReportTemplate.objects.filter(is_active=True)
    
    categories = ReportCategory.objects.filter(is_active=True)
    
    context = {
        'category': category,
        'categories': categories,
        'reports': reports,
    }
    return render(request, 'payroll/reports/category_view.html', context)


@login_required
def report_generate(request, report_id):
    """
    Generate a report
    """
    report_template = get_object_or_404(ReportTemplate, id=report_id)
    
    if request.method == 'POST':
        form = ReportGenerationForm(request.POST, report_template=report_template)
        if form.is_valid():
            # Create generated report record
            employee = Employee.objects.filter(employee_user_id=request.user).first()
            generated_report = GeneratedReport.objects.create(
                report_template=report_template,
                generated_by=employee,
                status='processing',
                date_from=form.cleaned_data.get('date_from'),
                date_to=form.cleaned_data.get('date_to'),
                company=form.cleaned_data.get('company'),
                department=form.cleaned_data.get('department'),
                employee=form.cleaned_data.get('employee'),
                parameters=form.cleaned_data,
            )
            
            try:
                # Generate the report based on type
                result = generate_report_file(
                    report_template,
                    form.cleaned_data,
                    generated_report
                )
                
                if result:
                    generated_report.status = 'completed'
                    generated_report.completed_at = timezone.now()
                    generated_report.save()
                    
                    messages.success(request, _('Report generated successfully!'))
                    return result  # Return the file response
                else:
                    generated_report.status = 'failed'
                    generated_report.error_message = 'Report generation failed'
                    generated_report.save()
                    messages.error(request, _('Failed to generate report.'))
                    
            except Exception as e:
                generated_report.status = 'failed'
                generated_report.error_message = str(e)
                generated_report.save()
                messages.error(request, f'Error generating report: {str(e)}')
    else:
        form = ReportGenerationForm(report_template=report_template)
    
    context = {
        'report_template': report_template,
        'form': form,
    }
    return render(request, 'payroll/reports/generate.html', context)


def generate_report_file(report_template, parameters, generated_report):
    """
    Generate report file based on report type and format
    """
    report_type = report_template.report_type
    output_format = report_template.output_format
    
    # Map report types to generator functions
    generators = {
        'payroll_register': {
            'pdf': generate_payroll_register_pdf,
            'excel': generate_payroll_register_excel,
        },
        'variance_report': {
            'pdf': generate_variance_report,
            'excel': generate_variance_report,
        },
        'employer_contributions': {
            'pdf': generate_employer_contributions,
            'excel': generate_employer_contributions,
        },
        'bank_advice_list': {
            'pdf': generate_bank_advice_list,
        },
        'bank_file': {
            'csv': generate_bank_file,
            'txt': generate_bank_file,
        },
        'sss_report': {
            'pdf': generate_sss_report,
            'excel': generate_sss_report,
        },
        'philhealth_report': {
            'pdf': generate_philhealth_report,
            'excel': generate_philhealth_report,
        },
        'pagibig_report': {
            'pdf': generate_pagibig_report,
            'excel': generate_pagibig_report,
        },
        'bir_report': {
            'pdf': generate_bir_report,
            'excel': generate_bir_report,
        },
        'net_pay_validation': {
            'pdf': generate_net_pay_validation,
            'excel': generate_net_pay_validation,
        },
        'basic_salary_report': {
            'pdf': generate_basic_salary_report,
            'excel': generate_basic_salary_report,
        },
        'withholding_tax_validation': {
            'pdf': generate_withholding_tax_validation,
            'excel': generate_withholding_tax_validation,
        },
        'certificate_contribution': {
            'pdf': generate_certificate_contribution,
        },
        'demographic_report': {
            'pdf': generate_demographic_report,
            'excel': generate_demographic_report,
        },
    }
    
    # Get the appropriate generator
    if report_type in generators and output_format in generators[report_type]:
        generator_func = generators[report_type][output_format]
        return generator_func(parameters, generated_report)
    else:
        raise ValueError(f'No generator found for {report_type} in {output_format} format')


@login_required
def report_history(request):
    """
    View report generation history
    """
    employee = Employee.objects.filter(employee_user_id=request.user).first()
    reports = GeneratedReport.objects.filter(
        generated_by=employee
    ).order_by('-generated_at')
    
    context = {
        'reports': reports,
    }
    return render(request, 'payroll/reports/history.html', context)


@login_required
def report_download(request, report_id):
    """
    Download a generated report
    """
    report = get_object_or_404(GeneratedReport, id=report_id)
    
    # Check permissions
    employee = Employee.objects.filter(employee_user_id=request.user).first()
    if report.generated_by != employee and not request.user.is_superuser:
        messages.error(request, _('You do not have permission to download this report.'))
        return redirect('report-history')
    
    if report.status != 'completed' or not report.file_path:
        messages.error(request, _('Report file not available.'))
        return redirect('report-history')
    
    # Serve the file
    response = HttpResponse(report.file_path, content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{report.file_name}"'
    return response


@login_required
def report_template_list(request):
    """
    List all report templates (admin)
    """
    templates = ReportTemplate.objects.all().order_by('category', 'name')
    
    context = {
        'templates': templates,
    }
    return render(request, 'payroll/reports/template_list.html', context)


@login_required
def report_template_create(request):
    """
    Create a new report template (admin)
    """
    if request.method == 'POST':
        form = ReportTemplateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _('Report template created successfully!'))
            return redirect('report-template-list')
    else:
        form = ReportTemplateForm()
    
    context = {
        'form': form,
    }
    return render(request, 'payroll/reports/template_form.html', context)


@login_required
def report_template_update(request, template_id):
    """
    Update report template (admin)
    """
    template = get_object_or_404(ReportTemplate, id=template_id)
    
    if request.method == 'POST':
        form = ReportTemplateForm(request.POST, instance=template)
        if form.is_valid():
            form.save()
            messages.success(request, _('Report template updated successfully!'))
            return redirect('report-template-list')
    else:
        form = ReportTemplateForm(instance=template)
    
    context = {
        'form': form,
        'template': template,
    }
    return render(request, 'payroll/reports/template_form.html', context)


@login_required
def report_template_delete(request, template_id):
    """
    Delete report template (admin)
    """
    template = get_object_or_404(ReportTemplate, id=template_id)
    
    if request.method == 'POST':
        template.delete()
        messages.success(request, _('Report template deleted successfully!'))
        return redirect('report-template-list')
    
    context = {
        'template': template,
    }
    return render(request, 'payroll/reports/template_confirm_delete.html', context)


@login_required
def bank_file_config_list(request):
    """
    List bank file configurations
    """
    configs = BankFileConfiguration.objects.all()
    
    context = {
        'configs': configs,
    }
    return render(request, 'payroll/reports/bank_config_list.html', context)


@login_required
def bank_file_config_create(request):
    """
    Create bank file configuration
    """
    if request.method == 'POST':
        form = BankFileConfigurationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _('Bank file configuration created successfully!'))
            return redirect('bank-config-list')
    else:
        form = BankFileConfigurationForm()
    
    context = {
        'form': form,
    }
    return render(request, 'payroll/reports/bank_config_form.html', context)


@login_required
def report_schedule_list(request):
    """
    List scheduled reports
    """
    schedules = ReportSchedule.objects.all().order_by('next_run_date')
    
    context = {
        'schedules': schedules,
    }
    return render(request, 'payroll/reports/schedule_list.html', context)


@login_required
def report_schedule_create(request):
    """
    Create report schedule
    """
    if request.method == 'POST':
        form = ReportScheduleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _('Report schedule created successfully!'))
            return redirect('report-schedule-list')
    else:
        form = ReportScheduleForm()
    
    context = {
        'form': form,
    }
    return render(request, 'payroll/reports/schedule_form.html', context)


@login_required
@require_http_methods(["GET"])
def get_report_statistics(request):
    """
    Get statistics for report dashboard (AJAX)
    """
    employee = Employee.objects.filter(employee_user_id=request.user).first()
    
    total_reports = GeneratedReport.objects.filter(generated_by=employee).count()
    completed_reports = GeneratedReport.objects.filter(
        generated_by=employee,
        status='completed'
    ).count()
    failed_reports = GeneratedReport.objects.filter(
        generated_by=employee,
        status='failed'
    ).count()
    
    # Reports by type
    reports_by_type = {}
    for report in ReportTemplate.objects.filter(is_active=True):
        count = GeneratedReport.objects.filter(
            generated_by=employee,
            report_template=report,
            status='completed'
        ).count()
        if count > 0:
            reports_by_type[report.name] = count
    
    data = {
        'total_reports': total_reports,
        'completed_reports': completed_reports,
        'failed_reports': failed_reports,
        'reports_by_type': reports_by_type,
    }
    
    return JsonResponse(data)


@login_required
def export_report_data(request):
    """
    Export raw report data as JSON (for custom processing)
    """
    if request.method == 'POST':
        date_from = request.POST.get('date_from')
        date_to = request.POST.get('date_to')
        
        payslips = Payslip.objects.filter(
            start_date__gte=date_from,
            end_date__lte=date_to,
            status='confirmed'
        )
        
        data = []
        for payslip in payslips:
            data.append({
                'employee_id': payslip.employee.employee_id,
                'employee_name': str(payslip.employee),
                'period': f"{payslip.start_date} to {payslip.end_date}",
                'basic_pay': float(payslip.basic_pay),
                'gross_pay': float(payslip.gross_pay),
                'deductions': float(payslip.deduction),
                'net_pay': float(payslip.net_pay),
            })
        
        response = JsonResponse(data, safe=False)
        response['Content-Disposition'] = f'attachment; filename="payroll_data_{date_from}_to_{date_to}.json"'
        return response
    
    return render(request, 'payroll/reports/export_data.html')
