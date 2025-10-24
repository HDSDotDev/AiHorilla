"""
middleware.py

Middleware for handling country-specific payroll configurations
"""

from django.utils.functional import SimpleLazyObject

from payroll.models.country_models import PayrollCountryConfig


def get_active_payroll_country(request):
    """
    Get the active payroll country configuration
    """
    if not hasattr(request, '_cached_payroll_country'):
        company_id = getattr(request.session.get('selected_company'), 'id', None) if hasattr(request, 'session') else None
        request._cached_payroll_country = PayrollCountryConfig.get_active_country(company_id)
    return request._cached_payroll_country


class PayrollCountryMiddleware:
    """
    Middleware to add active payroll country to request
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Add the active payroll country to the request
        request.payroll_country = SimpleLazyObject(lambda: get_active_payroll_country(request))
        
        response = self.get_response(request)
        return response
