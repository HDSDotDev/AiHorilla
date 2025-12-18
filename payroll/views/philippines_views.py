"""
philippines_views.py

Views for Philippines payroll system - frontend pages for clients
NO ADMIN ACCESS REQUIRED - All features accessible to regular users
"""

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.http import HttpResponse
from datetime import datetime
from decimal import Decimal
import csv

from payroll.models.country_models import (
    PhilippinesRegion,
    PhilippinesSSSContribution,
    PhilippinesPhilHealthContribution,
    PhilippinesPagIbigContribution,
    PhilippinesTaxBracket,
    PhilippinesThirteenthMonthPay,
    PhilippinesOvertimeRule,
    PhilippinesHolidayPay,
    PhilippinesCOLA,
    PhilippinesBIRForm2316,
    PhilippinesFinalPay,
    PhilippinesGovernmentRemittance,
    PhilippinesGovernmentRemittanceEntry,
)
from payroll.models.models import Payslip
from employee.models import Employee


@login_required
def philippines_payroll_reference(request):
    """
    Unified Philippine Payroll Reference Page
    Combines all informational pages: SSS, PhilHealth, Pag-IBIG, Tax Brackets, 
    Regional Wages, 13th Month, Overtime, Holidays, COLA
    """
    # Get all reference data
    sss_contributions = PhilippinesSSSContribution.objects.all().order_by('min_salary')
    philhealth_contributions = PhilippinesPhilHealthContribution.objects.all().order_by('min_salary')
    pagibig_contributions = PhilippinesPagIbigContribution.objects.all().order_by('min_salary')
    tax_brackets = PhilippinesTaxBracket.objects.all().order_by('min_annual_income')
    regions = PhilippinesRegion.objects.all().order_by('region_code')
    thirteenth_month_configs = PhilippinesThirteenthMonthPay.objects.all().order_by('-year')
    overtime_rules = PhilippinesOvertimeRule.objects.all()
    holidays = PhilippinesHolidayPay.objects.all().order_by('holiday_date')
    cola_list = PhilippinesCOLA.objects.all().select_related('region').order_by('region__region_code')
    
    # Pagination for SSS (largest table)
    paginator = Paginator(sss_contributions, 25)
    page_number = request.GET.get('page')
    sss_page_obj = paginator.get_page(page_number)
    
    context = {
        'sss_contributions': sss_page_obj,
        'philhealth_contributions': philhealth_contributions,
        'pagibig_contributions': pagibig_contributions,
        'tax_brackets': tax_brackets,
        'regions': regions,
        'thirteenth_month_configs': thirteenth_month_configs,
        'overtime_rules': overtime_rules,
        'holidays': holidays,
        'cola_list': cola_list,
        'title': 'Philippine Payroll Reference',
    }
    return render(request, 'payroll/philippines/payroll_reference.html', context)


@login_required
def philippines_sss_contributions(request):
    """View SSS contribution table"""
    contributions = PhilippinesSSSContribution.objects.all().order_by('min_salary')
    
    # Pagination
    paginator = Paginator(contributions, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'contributions': page_obj,
        'title': 'SSS Contribution Table',
    }
    return render(request, 'payroll/philippines/sss_contributions.html', context)


@login_required
def philippines_philhealth_contributions(request):
    """View PhilHealth contribution table"""
    contributions = PhilippinesPhilHealthContribution.objects.all().order_by('min_salary')
    
    context = {
        'contributions': contributions,
        'title': 'PhilHealth Contribution Table',
    }
    return render(request, 'payroll/philippines/philhealth_contributions.html', context)


@login_required
def philippines_pagibig_contributions(request):
    """View Pag-IBIG contribution table"""
    contributions = PhilippinesPagIbigContribution.objects.all().order_by('min_salary')
    
    context = {
        'contributions': contributions,
        'title': 'Pag-IBIG Contribution Table',
    }
    return render(request, 'payroll/philippines/pagibig_contributions.html', context)


@login_required
def philippines_tax_brackets(request):
    """View BIR tax brackets"""
    brackets = PhilippinesTaxBracket.objects.all().order_by('min_annual_income')
    
    context = {
        'brackets': brackets,
        'title': 'BIR Tax Brackets (TRAIN Law)',
    }
    return render(request, 'payroll/philippines/tax_brackets.html', context)


@login_required
def philippines_regions(request):
    """View regional minimum wage"""
    regions = PhilippinesRegion.objects.all().order_by('region_code')
    
    context = {
        'regions': regions,
        'title': 'Regional Minimum Wage',
    }
    return render(request, 'payroll/philippines/regions.html', context)


@login_required
def philippines_thirteenth_month(request):
    """View 13th month pay configuration"""
    configs = PhilippinesThirteenthMonthPay.objects.all().order_by('-year')
    
    context = {
        'configs': configs,
        'title': '13th Month Pay Configuration',
    }
    return render(request, 'payroll/philippines/thirteenth_month.html', context)


@login_required
def philippines_overtime_rules(request):
    """View overtime rules"""
    rules = PhilippinesOvertimeRule.objects.all()
    
    context = {
        'rules': rules,
        'title': 'Overtime Rules',
    }
    return render(request, 'payroll/philippines/overtime_rules.html', context)


@login_required
def philippines_holiday_pay(request):
    """View holiday pay schedule"""
    holidays = PhilippinesHolidayPay.objects.all().order_by('holiday_date')
    
    context = {
        'holidays': holidays,
        'title': 'Holiday Pay Schedule',
    }
    return render(request, 'payroll/philippines/holiday_pay.html', context)


@login_required
def philippines_cola(request):
    """View COLA (Cost of Living Allowance)"""
    cola_list = PhilippinesCOLA.objects.all().select_related('region').order_by('region__region_code')
    
    context = {
        'cola_list': cola_list,
        'title': 'COLA (Cost of Living Allowance)',
    }
    return render(request, 'payroll/philippines/cola.html', context)


@login_required
def bir_form_2316_list(request):
    """
    List all BIR Form 2316 records
    Employees can see their own, HR/payroll staff can see all
    """
    user_employee = request.user.employee_get
    
    # Check if user has permission to view all forms
    can_view_all = request.user.has_perm('payroll.view_philippinesbirform2316')
    
    if can_view_all:
        forms = PhilippinesBIRForm2316.objects.all().select_related('employee').order_by('-year', 'employee')
    else:
        # Employees can only see their own forms
        forms = PhilippinesBIRForm2316.objects.filter(employee=user_employee).order_by('-year')
    
    # Year filter
    year_filter = request.GET.get('year')
    if year_filter:
        forms = forms.filter(year=year_filter)
    
    # Get available years for filter
    available_years = PhilippinesBIRForm2316.objects.values_list('year', flat=True).distinct().order_by('-year')
    
    # Pagination
    paginator = Paginator(forms, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'forms': page_obj,
        'available_years': available_years,
        'selected_year': year_filter,
        'can_view_all': can_view_all,
        'title': 'BIR Form 2316 - Certificate of Compensation Payment/Tax Withheld',
    }
    return render(request, 'payroll/philippines/bir_form_2316_list.html', context)


@login_required
def bir_form_2316_generate(request, year=None):
    """
    Generate BIR Form 2316 for current user or specified employee
    
    AUTO-GENERATES from payslip data for the year
    """
    # Determine year (default to previous year)
    if not year:
        year = datetime.now().year - 1
    else:
        year = int(year)
    
    # Determine employee
    employee_id = request.GET.get('employee_id')
    if employee_id and request.user.has_perm('payroll.add_philippinesbirform2316'):
        # HR staff generating for specific employee
        try:
            employee = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            messages.error(request, "Employee not found.")
            return redirect('philippines-bir-form-2316-list')
    else:
        # Employee generating their own
        employee = request.user.employee_get
    
    # Check if form already exists
    existing_form = PhilippinesBIRForm2316.objects.filter(
        employee=employee,
        year=year,
        is_substituted=False
    ).first()
    
    if existing_form and not request.GET.get('regenerate'):
        messages.info(request, f"BIR Form 2316 for {year} already exists. Add '?regenerate=true' to regenerate.")
        return redirect('philippines-bir-form-2316-view', pk=existing_form.id)
    
    # Get all payslips for the year
    payslips = Payslip.objects.filter(
        employee_id=employee,
        start_date__year=year
    ).select_related('employee_id')
    
    if not payslips.exists():
        messages.error(request, f"No payslips found for {employee.get_full_name()} in {year}.")
        return redirect('philippines-bir-form-2316-list')
    
    # Calculate totals from payslips
    gross_compensation = Decimal('0.00')
    taxable_basic = Decimal('0.00')
    total_tax_withheld = Decimal('0.00')
    sss_employee = Decimal('0.00')
    philhealth_employee = Decimal('0.00')
    pagibig_employee = Decimal('0.00')
    
    for payslip in payslips:
        # Gross compensation
        gross_compensation += Decimal(str(payslip.basic_pay or 0))
        gross_compensation += Decimal(str(payslip.gross_pay or 0))
        
        # Taxable basic salary
        taxable_basic += Decimal(str(payslip.basic_pay or 0))
        
        # Tax withheld
        total_tax_withheld += Decimal(str(payslip.income_tax or 0))
        
        # Government contributions (employee share)
        # Note: These field names may vary - adjust based on actual Payslip model
        if hasattr(payslip, 'sss_deduction'):
            sss_employee += Decimal(str(payslip.sss_deduction or 0))
        if hasattr(payslip, 'philhealth_deduction'):
            philhealth_employee += Decimal(str(payslip.philhealth_deduction or 0))
        if hasattr(payslip, 'pagibig_deduction'):
            pagibig_employee += Decimal(str(payslip.pagibig_deduction or 0))
    
    # Calculate 13th month pay (non-taxable up to ₱90,000)
    thirteenth_month_total = Decimal('0.00')  # TODO: Get from 13th month payslips when implemented
    non_taxable_13th = min(thirteenth_month_total, Decimal('90000.00'))
    taxable_13th = max(Decimal('0.00'), thirteenth_month_total - Decimal('90000.00'))
    
    # Calculate exemptions based on tax status
    num_dependents = 0
    if employee.ph_tax_status:
        # Extract dependent count from tax status (S1, S2, ME1, etc.)
        tax_status = employee.ph_tax_status
        if tax_status and len(tax_status) > 1 and tax_status[-1].isdigit():
            num_dependents = int(tax_status[-1])
    
    personal_exemption = Decimal('50000.00')
    additional_exemption = Decimal('25000.00') * min(num_dependents, 4)
    
    # Employer information (from Company settings - TODO: Get from actual company)
    employer_tin = "000-000-000-000"  # TODO: Get from company settings
    employer_name = "Company Name"  # TODO: Get from company
    employer_address = "Company Address"  # TODO: Get from company
    
    # Create or update BIR Form 2316
    form_data = {
        'year': year,
        'employer_tin': employer_tin,
        'employer_name': employer_name,
        'employer_address': employer_address,
        'employee_tin': employee.tin_number or '',
        'employee_name': employee.get_full_name(),
        'employee_address': getattr(employee, 'address', 'N/A'),
        'gross_compensation': gross_compensation,
        'non_taxable_13th_month': non_taxable_13th,
        'non_taxable_de_minimis': Decimal('0.00'),  # TODO: Implement de minimis tracking
        'non_taxable_sss': sss_employee + philhealth_employee + pagibig_employee,
        'non_taxable_salaries': Decimal('0.00'),
        'taxable_basic_salary': taxable_basic,
        'taxable_13th_month': taxable_13th,
        'taxable_other_benefits': Decimal('0.00'),
        'personal_exemption': personal_exemption,
        'additional_exemption': additional_exemption,
        'premium_paid': Decimal('0.00'),  # TODO: Health insurance premium tracking
        'tax_withheld_jan_to_nov': total_tax_withheld,  # Simplified - split later
        'tax_withheld_december': Decimal('0.00'),
        'tax_withheld_total': total_tax_withheld,
        'generated_by': request.user.employee_get,
    }
    
    if existing_form:
        # Update existing form
        for key, value in form_data.items():
            setattr(existing_form, key, value)
        existing_form.save()
        bir_form = existing_form
        messages.success(request, f"BIR Form 2316 for {year} regenerated successfully.")
    else:
        # Create new form
        bir_form = PhilippinesBIRForm2316.objects.create(
            employee=employee,
            **form_data
        )
        messages.success(request, f"BIR Form 2316 for {year} generated successfully.")
    
    return redirect('philippines-bir-form-2316-view', pk=bir_form.id)


@login_required
def bir_form_2316_view(request, pk):
    """
    View/Print BIR Form 2316
    """
    try:
        bir_form = PhilippinesBIRForm2316.objects.select_related('employee').get(pk=pk)
    except PhilippinesBIRForm2316.DoesNotExist:
        messages.error(request, "BIR Form 2316 not found.")
        return redirect('philippines-bir-form-2316-list')
    
    # Permission check: user can view their own or has permission
    user_employee = request.user.employee_get
    if bir_form.employee != user_employee and not request.user.has_perm('payroll.view_philippinesbirform2316'):
        messages.error(request, "You don't have permission to view this form.")
        return redirect('philippines-bir-form-2316-list')
    
    context = {
        'form': bir_form,
        'title': f'BIR Form 2316 - {bir_form.employee_name} ({bir_form.year})',
    }
    
    # Check if PDF download requested
    if request.GET.get('download') == 'pdf':
        return bir_form_2316_pdf(request, bir_form)
    
    return render(request, 'payroll/philippines/bir_form_2316_view.html', context)


def bir_form_2316_pdf(request, bir_form):
    """
    Generate PDF for BIR Form 2316
    TODO: Implement PDF generation using reportlab or weasyprint
    """
    # For now, return HTML that can be printed as PDF
    context = {'form': bir_form}
    response = HttpResponse(content_type='text/html')
    response['Content-Disposition'] = f'inline; filename="BIR_Form_2316_{bir_form.employee_name}_{bir_form.year}.html"'
    
    from django.template.loader import render_to_string
    html = render_to_string('payroll/philippines/bir_form_2316_pdf.html', context)
    response.write(html)
    
    return response


@login_required
def bir_alphalist_export(request):
    """
    Generate BIR Alphalist of Employees
    
    Annual submission to BIR listing all employees and their compensation/taxes.
    This is derived from BIR Form 2316 data.
    
    Required by Revenue Regulations for annual filing.
    """
    # Check permission - only HR/payroll staff can export
    if not request.user.has_perm('payroll.view_philippinesbirform2316'):
        messages.error(request, "You don't have permission to export the Alphalist.")
        return redirect('philippines-bir-form-2316-list')
    
    # Get year parameter
    year = request.GET.get('year')
    if not year:
        year = datetime.now().year - 1
    else:
        year = int(year)
    
    # Get all Form 2316 records for the year
    forms = PhilippinesBIRForm2316.objects.filter(
        year=year,
        is_substituted=False
    ).select_related('employee').order_by('employee__employee_last_name', 'employee__employee_first_name')
    
    if not forms.exists():
        messages.error(request, f"No BIR Form 2316 records found for {year}. Generate forms first.")
        return redirect('philippines-bir-form-2316-list')
    
    # Determine export format
    export_format = request.GET.get('format', 'csv')
    
    if export_format == 'excel':
        return alphalist_export_excel(request, forms, year)
    else:
        return alphalist_export_csv(request, forms, year)


def alphalist_export_csv(request, forms, year):
    """Export Alphalist as CSV file"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="BIR_Alphalist_{year}.csv"'
    
    writer = csv.writer(response)
    
    # Write header
    writer.writerow([
        'SEQ NO',
        'TIN',
        'TAXPAYER NAME',
        'LAST NAME',
        'FIRST NAME',
        'MIDDLE NAME',
        'GROSS COMPENSATION',
        'NON-TAXABLE 13TH MONTH',
        'NON-TAXABLE DE MINIMIS',
        'NON-TAXABLE SSS/GSIS/PHIC/HDMF',
        'NON-TAXABLE SALARIES',
        'TOTAL NON-TAXABLE',
        'TAXABLE BASIC SALARY',
        'TAXABLE 13TH MONTH',
        'TAXABLE OTHER BENEFITS',
        'TOTAL TAXABLE',
        'PERSONAL EXEMPTION',
        'ADDITIONAL EXEMPTION',
        'PREMIUM PAID',
        'NET TAXABLE',
        'TAX WITHHELD',
    ])
    
    # Write data rows
    seq_no = 1
    total_gross = Decimal('0.00')
    total_tax_withheld = Decimal('0.00')
    
    for form in forms:
        # Parse employee name
        name_parts = form.employee_name.split()
        last_name = name_parts[-1] if name_parts else ''
        first_name = name_parts[0] if len(name_parts) > 0 else ''
        middle_name = name_parts[1] if len(name_parts) > 2 else ''
        
        writer.writerow([
            seq_no,
            form.employee_tin,
            form.employee_name,
            last_name,
            first_name,
            middle_name,
            f"{form.gross_compensation:.2f}",
            f"{form.non_taxable_13th_month:.2f}",
            f"{form.non_taxable_de_minimis:.2f}",
            f"{form.non_taxable_sss:.2f}",
            f"{form.non_taxable_salaries:.2f}",
            f"{form.total_non_taxable:.2f}",
            f"{form.taxable_basic_salary:.2f}",
            f"{form.taxable_13th_month:.2f}",
            f"{form.taxable_other_benefits:.2f}",
            f"{form.total_taxable:.2f}",
            f"{form.personal_exemption:.2f}",
            f"{form.additional_exemption:.2f}",
            f"{form.premium_paid:.2f}",
            f"{form.net_taxable_compensation:.2f}",
            f"{form.tax_withheld_total:.2f}",
        ])
        
        seq_no += 1
        total_gross += form.gross_compensation
        total_tax_withheld += form.tax_withheld_total
    
    # Write totals row
    writer.writerow([])
    writer.writerow([
        '',
        '',
        'TOTAL',
        '',
        '',
        '',
        f"{total_gross:.2f}",
        '',
        '',
        '',
        '',
        '',
        '',
        '',
        '',
        '',
        '',
        '',
        '',
        '',
        f"{total_tax_withheld:.2f}",
    ])
    
    return response


def alphalist_export_excel(request, forms, year):
    """
    Export Alphalist as Excel file
    Requires openpyxl library
    """
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, Alignment, PatternFill
        from openpyxl.utils import get_column_letter
    except ImportError:
        messages.error(request, "Excel export requires 'openpyxl' library. Please install it or use CSV format.")
        return redirect('philippines-bir-form-2316-list')
    
    # Create workbook
    wb = Workbook()
    ws = wb.active
    ws.title = f"Alphalist {year}"
    
    # Header styling
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center")
    
    # Write title
    ws.merge_cells('A1:U1')
    title_cell = ws['A1']
    title_cell.value = f"BIR ALPHALIST OF EMPLOYEES FOR CALENDAR YEAR {year}"
    title_cell.font = Font(bold=True, size=14)
    title_cell.alignment = Alignment(horizontal="center")
    
    # Write headers
    headers = [
        'SEQ NO', 'TIN', 'TAXPAYER NAME', 'LAST NAME', 'FIRST NAME', 'MIDDLE NAME',
        'GROSS COMP', 'NON-TAX 13TH', 'NON-TAX DEMIN', 'NON-TAX SSS',
        'NON-TAX SAL', 'TOTAL NON-TAX', 'TAX BASIC', 'TAX 13TH',
        'TAX OTHER', 'TOTAL TAX', 'PERS EXEMPT', 'ADD EXEMPT',
        'PREMIUM', 'NET TAXABLE', 'TAX WITHHELD'
    ]
    
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=3, column=col_num)
        cell.value = header
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
    
    # Write data
    row_num = 4
    seq_no = 1
    total_gross = Decimal('0.00')
    total_tax_withheld = Decimal('0.00')
    
    for form in forms:
        # Parse employee name
        name_parts = form.employee_name.split()
        last_name = name_parts[-1] if name_parts else ''
        first_name = name_parts[0] if len(name_parts) > 0 else ''
        middle_name = name_parts[1] if len(name_parts) > 2 else ''
        
        data = [
            seq_no,
            form.employee_tin,
            form.employee_name,
            last_name,
            first_name,
            middle_name,
            float(form.gross_compensation),
            float(form.non_taxable_13th_month),
            float(form.non_taxable_de_minimis),
            float(form.non_taxable_sss),
            float(form.non_taxable_salaries),
            float(form.total_non_taxable),
            float(form.taxable_basic_salary),
            float(form.taxable_13th_month),
            float(form.taxable_other_benefits),
            float(form.total_taxable),
            float(form.personal_exemption),
            float(form.additional_exemption),
            float(form.premium_paid),
            float(form.net_taxable_compensation),
            float(form.tax_withheld_total),
        ]
        
        for col_num, value in enumerate(data, 1):
            cell = ws.cell(row=row_num, column=col_num)
            cell.value = value
            if col_num >= 7:  # Money columns
                cell.number_format = '#,##0.00'
        
        seq_no += 1
        row_num += 1
        total_gross += form.gross_compensation
        total_tax_withheld += form.tax_withheld_total
    
    # Write totals
    row_num += 1
    ws.cell(row=row_num, column=3).value = "TOTAL"
    ws.cell(row=row_num, column=3).font = Font(bold=True)
    ws.cell(row=row_num, column=7).value = float(total_gross)
    ws.cell(row=row_num, column=7).number_format = '#,##0.00'
    ws.cell(row=row_num, column=7).font = Font(bold=True)
    ws.cell(row=row_num, column=21).value = float(total_tax_withheld)
    ws.cell(row=row_num, column=21).number_format = '#,##0.00'
    ws.cell(row=row_num, column=21).font = Font(bold=True)
    
    # Auto-adjust column widths
    for column in ws.columns:
        max_length = 0
        column_letter = get_column_letter(column[0].column)
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(cell.value)
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column_letter].width = adjusted_width
    
    # Create response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="BIR_Alphalist_{year}.xlsx"'
    wb.save(response)
    
    return response


@login_required
def thirteenth_month_generator(request):
    """
    Generate 13th Month Pay for employees
    
    Required by Presidential Decree No. 851 - must be paid on or before December 24.
    Calculates as: Total Basic Salary for the Year / 12
    """
    # Check permission - only HR/payroll staff can generate
    if not request.user.has_perm('payroll.add_payslip'):
        messages.error(request, "You don't have permission to generate 13th month pay.")
        return redirect('view-payslip')
    
    # Get year parameter (default to current year)
    year = request.GET.get('year')
    if not year:
        year = datetime.now().year
    else:
        year = int(year)
    
    # Get all active employees
    employees = Employee.objects.filter(
        is_active=True,
        employee_work_info__isnull=False
    ).order_by('employee_first_name', 'employee_last_name')
    
    if request.method == 'POST':
        # Generate 13th month pay for selected employees
        selected_employee_ids = request.POST.getlist('employee_ids')
        
        if not selected_employee_ids:
            messages.error(request, "Please select at least one employee.")
            return redirect('philippines-thirteenth-month-generator')
        
        generated_count = 0
        errors = []
        
        for emp_id in selected_employee_ids:
            try:
                employee = Employee.objects.get(id=emp_id)
                
                # Get all payslips for the year
                year_payslips = Payslip.objects.filter(
                    employee_id=employee,
                    start_date__year=year
                )
                
                if not year_payslips.exists():
                    errors.append(f"{employee.get_full_name()}: No payslips found for {year}")
                    continue
                
                # Calculate total basic salary for the year
                total_basic_ytd = year_payslips.aggregate(
                    total=Sum('basic_pay')
                )['total'] or Decimal('0.00')
                
                if total_basic_ytd == 0:
                    errors.append(f"{employee.get_full_name()}: Total basic salary is zero")
                    continue
                
                # Calculate months worked
                months_worked = year_payslips.values('start_date__month').distinct().count()
                
                # Use Philippines payroll calculator
                from payroll.methods.philippines_payroll import PhilippinesPayrollCalculator
                
                # Get basic salary (use most recent)
                latest_payslip = year_payslips.order_by('-start_date').first()
                basic_salary = latest_payslip.basic_pay or Decimal('0.00')
                
                calculator = PhilippinesPayrollCalculator(
                    employee=employee,
                    basic_salary=basic_salary,
                    period_start=datetime(year, 12, 1).date(),
                    period_end=datetime(year, 12, 31).date()
                )
                
                # Calculate 13th month pay
                thirteenth_result = calculator.calculate_thirteenth_month_pay(
                    total_basic_salary_ytd=total_basic_ytd,
                    months_worked=months_worked
                )
                
                # Create a special payslip for 13th month pay
                # Note: This creates a record but doesn't generate actual payment
                # The company should integrate this with their payment process
                
                thirteenth_month_amount = thirteenth_result['thirteenth_month_pay']
                tax_exempt = thirteenth_result['tax_exempt_portion']
                taxable = thirteenth_result['taxable_portion']
                
                # Store in session for confirmation page
                if 'thirteenth_month_results' not in request.session:
                    request.session['thirteenth_month_results'] = []
                
                request.session['thirteenth_month_results'].append({
                    'employee_name': employee.get_full_name(),
                    'employee_id': employee.id,
                    'total_basic_ytd': str(total_basic_ytd),
                    'months_worked': months_worked,
                    'thirteenth_month_pay': str(thirteenth_month_amount),
                    'tax_exempt_portion': str(tax_exempt),
                    'taxable_portion': str(taxable),
                })
                
                generated_count += 1
                
            except Employee.DoesNotExist:
                errors.append(f"Employee ID {emp_id} not found")
            except Exception as e:
                errors.append(f"Error processing employee ID {emp_id}: {str(e)}")
        
        request.session.modified = True
        
        if generated_count > 0:
            messages.success(request, f"Successfully calculated 13th month pay for {generated_count} employee(s).")
        
        if errors:
            for error in errors:
                messages.warning(request, error)
        
        return redirect('philippines-thirteenth-month-results')
    
    # GET request - show form
    # Calculate preview data for each employee
    employee_data = []
    for employee in employees:
        year_payslips = Payslip.objects.filter(
            employee_id=employee,
            start_date__year=year
        )
        
        total_basic = year_payslips.aggregate(total=Sum('basic_pay'))['total'] or Decimal('0.00')
        months_worked = year_payslips.values('start_date__month').distinct().count()
        estimated_13th = total_basic / 12 if total_basic > 0 else Decimal('0.00')
        
        employee_data.append({
            'employee': employee,
            'total_basic_ytd': total_basic,
            'months_worked': months_worked,
            'estimated_13th_month': estimated_13th,
            'has_payslips': year_payslips.exists()
        })
    
    context = {
        'employees': employee_data,
        'year': year,
        'title': f'Generate 13th Month Pay ({year})',
        'deadline': f'December 24, {year}',
    }
    
    return render(request, 'payroll/philippines/thirteenth_month_generator.html', context)


@login_required
def thirteenth_month_results(request):
    """Display 13th month pay calculation results"""
    results = request.session.get('thirteenth_month_results', [])
    
    if not results:
        messages.info(request, "No 13th month pay calculations found. Please generate first.")
        return redirect('philippines-thirteenth-month-generator')
    
    # Calculate totals
    total_13th = sum(Decimal(r['thirteenth_month_pay']) for r in results)
    total_tax_exempt = sum(Decimal(r['tax_exempt_portion']) for r in results)
    total_taxable = sum(Decimal(r['taxable_portion']) for r in results)
    
    context = {
        'results': results,
        'total_13th_month': total_13th,
        'total_tax_exempt': total_tax_exempt,
        'total_taxable': total_taxable,
        'title': '13th Month Pay Calculation Results',
    }
    
    # Clear session data if requested
    if request.GET.get('clear'):
        request.session.pop('thirteenth_month_results', None)
        messages.success(request, "Results cleared.")
        return redirect('philippines-thirteenth-month-generator')
    
    return render(request, 'payroll/philippines/thirteenth_month_results.html', context)


@login_required
def final_pay_calculator(request):
    """
    Final Pay Calculator for separating employees
    
    Calculates:
    1. Unpaid salary (last working days)
    2. Pro-rated 13th month pay
    3. Unused leave conversion
    4. Separation pay (if applicable)
    5. Tax adjustments
    """
    if request.method == 'POST':
        try:
            # Get employee
            employee_id = request.POST.get('employee_id')
            employee = Employee.objects.get(id=employee_id)
            
            # Get separation details
            separation_date = datetime.strptime(request.POST.get('separation_date'), '%Y-%m-%d').date()
            last_payroll_date = datetime.strptime(request.POST.get('last_payroll_date'), '%Y-%m-%d').date()
            separation_reason = request.POST.get('separation_reason')
            
            # Get work information
            work_info = employee.employee_work_info
            date_joining = work_info.date_joining if work_info else None
            
            # Calculate years of service
            if date_joining:
                years_of_service = Decimal((separation_date - date_joining).days) / Decimal('365.25')
            else:
                years_of_service = Decimal('0.00')
            
            # Get salary information from latest contract
            from payroll.models.models import Contract
            latest_contract = Contract.objects.filter(
                employee=employee,
                contract_status='active'
            ).first()
            
            if not latest_contract:
                messages.error(request, "No active contract found for employee.")
                return redirect('philippines-final-pay-calculator')
            
            monthly_salary = latest_contract.wage
            
            # Calculate daily rate: (Monthly × 12) ÷ 261 working days
            daily_rate = (monthly_salary * Decimal('12.00')) / Decimal('261.00')
            
            # Get unpaid days
            unpaid_days = Decimal(request.POST.get('unpaid_days', '0'))
            
            # Get YTD basic salary from payslips
            current_year = separation_date.year
            ytd_payslips = Payslip.objects.filter(
                employee=employee,
                start_date__year=current_year,
                status='paid'
            )
            total_basic_ytd = ytd_payslips.aggregate(total=Sum('basic_pay'))['total'] or Decimal('0.00')
            
            # Calculate months worked in current year
            from datetime import date
            year_start = date(current_year, 1, 1)
            days_worked = (separation_date - year_start).days + 1
            months_worked = Decimal(days_worked) / Decimal('30.4375')  # Average days per month
            
            # Get leave balances
            unused_vacation_days = Decimal(request.POST.get('unused_vacation_days', '0'))
            unused_sick_days = Decimal(request.POST.get('unused_sick_days', '0'))
            
            # Determine if entitled to separation pay
            entitled_reasons = ['retrenchment', 'redundancy', 'illness', 'closure']
            is_entitled = separation_reason in entitled_reasons
            
            # Get loan/deduction information
            unpaid_loans = Decimal(request.POST.get('unpaid_loans', '0'))
            other_deductions = Decimal(request.POST.get('other_deductions', '0'))
            
            # Get tax information
            ytd_tax_withheld = ytd_payslips.aggregate(total=Sum('employee_tax'))['total'] or Decimal('0.00')
            
            # Calculate final tax (simplified - would need full tax recalculation)
            # For now, assume no adjustment needed (would require full PhilippinesPayrollCalculator integration)
            final_tax_due = ytd_tax_withheld
            tax_adjustment = Decimal('0.00')  # Positive = refund, Negative = additional
            
            # Create Final Pay record
            final_pay = PhilippinesFinalPay.objects.create(
                employee=employee,
                separation_date=separation_date,
                last_payroll_date=last_payroll_date,
                separation_reason=separation_reason,
                unpaid_days=unpaid_days,
                daily_rate=daily_rate,
                total_basic_ytd=total_basic_ytd,
                months_worked=months_worked,
                unused_vacation_days=unused_vacation_days,
                unused_sick_days=unused_sick_days,
                is_entitled_to_separation_pay=is_entitled,
                years_of_service=years_of_service,
                monthly_salary=monthly_salary,
                unpaid_loans=unpaid_loans,
                other_deductions=other_deductions,
                ytd_tax_withheld=ytd_tax_withheld,
                final_tax_due=final_tax_due,
                tax_adjustment=tax_adjustment,
                calculated_by=request.user.employee_get,
            )
            
            # The save() method auto-calculates all components
            final_pay.save()
            
            messages.success(request, f"Final pay calculated successfully for {employee.get_full_name()}")
            return redirect('philippines-final-pay-view', pk=final_pay.pk)
            
        except Employee.DoesNotExist:
            messages.error(request, "Employee not found.")
        except Exception as e:
            messages.error(request, f"Error calculating final pay: {str(e)}")
    
    # GET request - show form
    employees = Employee.objects.filter(
        is_active=True
    ).order_by('employee_first_name', 'employee_last_name')
    
    context = {
        'title': 'Final Pay Calculator',
        'employees': employees,
        'separation_reasons': PhilippinesFinalPay.SEPARATION_REASON_CHOICES,
        'deadline': 'Within 30 days of separation',
    }
    
    return render(request, 'payroll/philippines/final_pay_calculator.html', context)


@login_required
def final_pay_list(request):
    """List all final pay records with filters"""
    final_pays = PhilippinesFinalPay.objects.select_related('employee', 'calculated_by').all()
    
    # Apply filters
    if request.GET.get('is_paid'):
        is_paid = request.GET.get('is_paid') == 'true'
        final_pays = final_pays.filter(is_paid=is_paid)
    
    if request.GET.get('year'):
        year = int(request.GET.get('year'))
        final_pays = final_pays.filter(separation_date__year=year)
    
    if request.GET.get('search'):
        search = request.GET.get('search')
        final_pays = final_pays.filter(
            Q(employee__employee_first_name__icontains=search) |
            Q(employee__employee_last_name__icontains=search) |
            Q(employee__badge_id__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(final_pays, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculate totals
    from django.db.models import Sum
    totals = final_pays.aggregate(
        total_gross=Sum('gross_final_pay'),
        total_deductions=Sum('total_deductions'),
        total_net=Sum('net_final_pay')
    )
    
    context = {
        'title': 'Final Pay Records',
        'page_obj': page_obj,
        'final_pays': page_obj.object_list,
        'total_gross_final_pay': totals['total_gross'] or 0,
        'total_deductions': totals['total_deductions'] or 0,
        'total_net_final_pay': totals['total_net'] or 0,
    }
    
    return render(request, 'payroll/philippines/final_pay_list.html', context)


@login_required
def final_pay_view(request, pk):
    """View individual final pay record with detailed breakdown"""
    final_pay = PhilippinesFinalPay.objects.select_related('employee', 'calculated_by').get(pk=pk)
    
    # Mark as paid if requested
    if request.method == 'POST' and request.POST.get('action') == 'mark_paid':
        final_pay.is_paid = True
        final_pay.payment_date = datetime.now().date()
        final_pay.save(update_fields=['is_paid', 'payment_date'])
        messages.success(request, f"Final pay marked as paid for {final_pay.employee.get_full_name()}")
        return redirect('philippines-final-pay-view', pk=pk)
    
    context = {
        'title': f'Final Pay - {final_pay.employee.get_full_name()}',
        'final_pay': final_pay,
    }
    
    return render(request, 'payroll/philippines/final_pay_view.html', context)


@login_required
def government_forms_generator(request):
    """
    Generate government remittance forms (SSS R3, PhilHealth RF-1, Pag-IBIG MCRF)
    """
    if request.method == 'POST':
        try:
            form_type = request.POST.get('form_type')
            year = int(request.POST.get('year'))
            month = int(request.POST.get('month'))
            
            # Get company information (would come from settings in production)
            from base.models import Company
            company = Company.objects.first()
            
            # Get employer IDs based on form type
            employer_ids = {
                'sss_r3': '34-1234567-8',  # Sample SSS Number
                'philhealth_rf1': '12345678901',  # Sample PhilHealth Number
                'pagibig_mcrf': '123456789012',  # Sample Pag-IBIG Number
            }
            
            # Create remittance record
            remittance = PhilippinesGovernmentRemittance.objects.create(
                form_type=form_type,
                period_type='monthly',
                year=year,
                month=month,
                employer_name=company.company if company else "Sample Company",
                employer_id=employer_ids.get(form_type, 'N/A'),
                employer_address=company.address if company else "Sample Address",
                generated_by=request.user.employee_get,
            )
            
            # Get all employees with payslips for the period
            from payroll.models.models import Payslip
            from datetime import date
            
            # Get first and last day of month
            if month == 12:
                next_month = date(year + 1, 1, 1)
            else:
                next_month = date(year, month + 1, 1)
            
            period_start = date(year, month, 1)
            period_end = date(next_month.year, next_month.month, 1) if month < 12 else date(year, 12, 31)
            
            # Get payslips for the period
            payslips = Payslip.objects.filter(
                start_date__gte=period_start,
                start_date__lt=period_end,
                status='paid'
            ).select_related('employee')
            
            # Group by employee
            from collections import defaultdict
            employee_data = defaultdict(lambda: {
                'employee': None,
                'total_basic': Decimal('0.00'),
                'count': 0
            })
            
            for payslip in payslips:
                emp_id = payslip.employee.id
                employee_data[emp_id]['employee'] = payslip.employee
                employee_data[emp_id]['total_basic'] += payslip.basic_pay or Decimal('0.00')
                employee_data[emp_id]['count'] += 1
            
            # Import payroll calculator
            from payroll.methods.philippines_payroll import PhilippinesPayrollCalculator
            
            # Create entry for each employee
            for emp_id, data in employee_data.items():
                employee = data['employee']
                avg_basic = data['total_basic'] / Decimal(data['count']) if data['count'] > 0 else Decimal('0.00')
                
                # Get employee government IDs
                sss_number = getattr(employee, 'sss_number', 'N/A')
                philhealth_number = getattr(employee, 'philhealth_number', 'N/A')
                pagibig_number = getattr(employee, 'pagibig_number', 'N/A')
                
                # Calculate contributions based on form type
                calculator = PhilippinesPayrollCalculator(employee, avg_basic, year, month)
                
                if form_type == 'sss_r3':
                    sss_contrib = calculator.get_sss_contribution()
                    employee_contrib = sss_contrib['employee_share']
                    employer_contrib = sss_contrib['employer_share']
                    ec_contrib = sss_contrib['ec']
                    id_number = sss_number
                    
                elif form_type == 'philhealth_rf1':
                    philhealth_contrib = calculator.get_philhealth_contribution()
                    employee_contrib = philhealth_contrib['employee_share']
                    employer_contrib = philhealth_contrib['employer_share']
                    ec_contrib = Decimal('0.00')
                    id_number = philhealth_number
                    
                elif form_type == 'pagibig_mcrf':
                    pagibig_contrib = calculator.get_pagibig_contribution()
                    employee_contrib = pagibig_contrib['employee_share']
                    employer_contrib = pagibig_contrib['employer_share']
                    ec_contrib = Decimal('0.00')
                    id_number = pagibig_number
                
                # Create entry
                PhilippinesGovernmentRemittanceEntry.objects.create(
                    remittance=remittance,
                    employee=employee,
                    employee_id_number=id_number,
                    employee_full_name=employee.get_full_name(),
                    monthly_salary=avg_basic,
                    employee_contribution=employee_contrib,
                    employer_contribution=employer_contrib,
                    ec_contribution=ec_contrib,
                )
            
            # Calculate totals
            remittance.calculate_totals()
            remittance.save()
            
            messages.success(request, f"Government form generated successfully: {remittance}")
            return redirect('philippines-government-forms-view', pk=remittance.pk)
            
        except Exception as e:
            messages.error(request, f"Error generating form: {str(e)}")
    
    # GET request - show form
    context = {
        'title': 'Government Forms Generator',
        'form_types': PhilippinesGovernmentRemittance.FORM_TYPE_CHOICES,
        'current_year': datetime.now().year,
        'current_month': datetime.now().month,
    }
    
    return render(request, 'payroll/philippines/government_forms_generator.html', context)


@login_required
def government_forms_list(request):
    """List all government remittance forms"""
    forms = PhilippinesGovernmentRemittance.objects.select_related('generated_by').all()
    
    # Filters
    if request.GET.get('form_type'):
        forms = forms.filter(form_type=request.GET.get('form_type'))
    
    if request.GET.get('year'):
        forms = forms.filter(year=int(request.GET.get('year')))
    
    if request.GET.get('is_submitted'):
        is_submitted = request.GET.get('is_submitted') == 'true'
        forms = forms.filter(is_submitted=is_submitted)
    
    # Pagination
    paginator = Paginator(forms, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'title': 'Government Remittance Forms',
        'page_obj': page_obj,
        'forms': page_obj.object_list,
        'form_types': PhilippinesGovernmentRemittance.FORM_TYPE_CHOICES,
    }
    
    return render(request, 'payroll/philippines/government_forms_list.html', context)


@login_required
def government_forms_view(request, pk):
    """View individual government remittance form"""
    remittance = PhilippinesGovernmentRemittance.objects.prefetch_related('employee_entries__employee').get(pk=pk)
    
    # Mark as submitted if requested
    if request.method == 'POST' and request.POST.get('action') == 'mark_submitted':
        remittance.is_submitted = True
        remittance.submission_date = datetime.now().date()
        remittance.save(update_fields=['is_submitted', 'submission_date'])
        messages.success(request, f"Form marked as submitted")
        return redirect('philippines-government-forms-view', pk=pk)
    
    context = {
        'title': f'{remittance.get_form_type_display()} - {remittance.get_period_display_text()}',
        'remittance': remittance,
        'entries': remittance.employee_entries.all(),
    }
    
    return render(request, 'payroll/philippines/government_forms_view.html', context)


@login_required
def government_forms_export_excel(request, pk):
    """Export government form to Excel"""
    remittance = PhilippinesGovernmentRemittance.objects.prefetch_related('employee_entries').get(pk=pk)
    
    try:
        import openpyxl
        from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
        
        # Create workbook
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = remittance.get_form_type_display()[:31]  # Excel limit
        
        # Styles
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=12)
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        # Title
        ws.merge_cells('A1:G1')
        ws['A1'] = remittance.get_form_type_display()
        ws['A1'].font = Font(bold=True, size=14)
        ws['A1'].alignment = Alignment(horizontal='center')
        
        # Period
        ws.merge_cells('A2:G2')
        ws['A2'] = f"Period: {remittance.get_period_display_text()}"
        ws['A2'].alignment = Alignment(horizontal='center')
        
        # Employer Info
        ws['A4'] = "Employer Name:"
        ws['B4'] = remittance.employer_name
        ws['A5'] = "Employer ID:"
        ws['B5'] = remittance.employer_id
        
        # Headers (row 7)
        headers = ['No.', 'Employee ID Number', 'Employee Name', 'Monthly Salary', 
                   'Employee Share', 'Employer Share']
        
        if remittance.form_type == 'sss_r3':
            headers.append('EC')
        
        headers.append('Total')
        
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=7, column=col_num)
            cell.value = header
            cell.fill = header_fill
            cell.font = header_font
            cell.border = border
            cell.alignment = Alignment(horizontal='center')
        
        # Data rows
        row_num = 8
        for idx, entry in enumerate(remittance.employee_entries.all(), 1):
            ws.cell(row=row_num, column=1, value=idx).border = border
            ws.cell(row=row_num, column=2, value=entry.employee_id_number).border = border
            ws.cell(row=row_num, column=3, value=entry.employee_full_name).border = border
            ws.cell(row=row_num, column=4, value=float(entry.monthly_salary)).border = border
            ws.cell(row=row_num, column=5, value=float(entry.employee_contribution)).border = border
            ws.cell(row=row_num, column=6, value=float(entry.employer_contribution)).border = border
            
            col = 7
            if remittance.form_type == 'sss_r3':
                ws.cell(row=row_num, column=col, value=float(entry.ec_contribution)).border = border
                col += 1
            
            ws.cell(row=row_num, column=col, value=float(entry.total_contribution)).border = border
            
            # Format currency
            for c in range(4, col + 1):
                ws.cell(row=row_num, column=c).number_format = '#,##0.00'
            
            row_num += 1
        
        # Totals row
        total_row = row_num
        ws.cell(row=total_row, column=1, value="TOTAL:").font = Font(bold=True)
        ws.cell(row=total_row, column=3, value=f"{remittance.total_employees} employees").font = Font(bold=True)
        ws.cell(row=total_row, column=5, value=float(remittance.total_employee_contribution)).font = Font(bold=True)
        ws.cell(row=total_row, column=6, value=float(remittance.total_employer_contribution)).font = Font(bold=True)
        
        col = 7
        if remittance.form_type == 'sss_r3':
            ws.cell(row=total_row, column=col, value=float(remittance.total_ec_contribution)).font = Font(bold=True)
            col += 1
        
        ws.cell(row=total_row, column=col, value=float(remittance.grand_total)).font = Font(bold=True)
        
        # Format totals
        for c in range(5, col + 1):
            ws.cell(row=total_row, column=c).number_format = '#,##0.00'
        
        # Adjust column widths
        ws.column_dimensions['A'].width = 8
        ws.column_dimensions['B'].width = 20
        ws.column_dimensions['C'].width = 30
        ws.column_dimensions['D'].width = 15
        ws.column_dimensions['E'].width = 15
        ws.column_dimensions['F'].width = 15
        if remittance.form_type == 'sss_r3':
            ws.column_dimensions['G'].width = 12
            ws.column_dimensions['H'].width = 15
        else:
            ws.column_dimensions['G'].width = 15
        
        # Create response
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        filename = f"{remittance.get_form_type_display()}_{remittance.year}_{remittance.month:02d}.xlsx"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        wb.save(response)
        return response
        
    except ImportError:
        messages.error(request, "openpyxl not installed. Cannot export to Excel.")
        return redirect('philippines-government-forms-view', pk=pk)
    except Exception as e:
        messages.error(request, f"Error exporting to Excel: {str(e)}")
        return redirect('philippines-government-forms-view', pk=pk)


