"""
context_processor.py

This module is used to register context processor`
"""

from employee.models import Employee
from payroll.models import tax_models as models
from payroll.models.models import Deduction
from payroll.models.country_models import PayrollCountryConfig


def default_currency(request):
    """
    This method will return the currency
    """
    # Check active country config
    active_country = getattr(request, 'payroll_country', None)
    
    # Set currency based on active country
    default_symbol = "$"
    if active_country and active_country.country == 'PH':
        default_symbol = "₱"
    
    if models.PayrollSettings.objects.first() is None:
        settings = models.PayrollSettings()
        settings.currency_symbol = default_symbol
        settings.save()
    
    symbol = models.PayrollSettings.objects.first().currency_symbol
    position = models.PayrollSettings.objects.first().position
    
    return {
        "currency": request.session.get("currency", symbol),
        "position": request.session.get("position", position),
    }


def active_payroll_country(request):
    """
    This method will return the active payroll country configuration
    """
    active_country = getattr(request, 'payroll_country', None)
    return {
        "active_payroll_country": active_country,
        "is_philippines_payroll": active_country and active_country.country == 'PH',
        "is_usa_payroll": active_country and active_country.country == 'USA',
    }


def host(request):
    """
    This method will return the host
    """
    protocol = "https" if request.is_secure() else "http"
    return {"host": request.get_host(), "protocol": protocol}


def get_deductions(request):
    """
    This method used to return the deduction
    """
    deductions = Deduction.objects.filter(
        only_show_under_employee=False, employer_rate__gt=0
    )
    return {"get_deductions": deductions}


def get_active_employees(request):
    """
    This method used to return the deduction
    """
    employees = Employee.objects.filter(
        is_active=True, contract_set__isnull=False, payslip__isnull=False
    ).distinct()
    return {"get_active_employees": employees}
