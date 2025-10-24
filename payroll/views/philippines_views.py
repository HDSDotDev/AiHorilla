"""
philippines_views.py

Views for Philippines payroll system - frontend pages for clients
NO ADMIN ACCESS REQUIRED - All features accessible to regular users
"""

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
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
)


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
