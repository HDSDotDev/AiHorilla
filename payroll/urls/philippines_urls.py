"""
philippines_urls.py

URL patterns for Philippines payroll system
"""

from django.urls import path
from payroll.views import philippines_views

urlpatterns = [
    path(
        'philippines/sss-contributions/',
        philippines_views.philippines_sss_contributions,
        name='philippines-sss-contributions'
    ),
    path(
        'philippines/philhealth-contributions/',
        philippines_views.philippines_philhealth_contributions,
        name='philippines-philhealth-contributions'
    ),
    path(
        'philippines/pagibig-contributions/',
        philippines_views.philippines_pagibig_contributions,
        name='philippines-pagibig-contributions'
    ),
    path(
        'philippines/tax-brackets/',
        philippines_views.philippines_tax_brackets,
        name='philippines-tax-brackets'
    ),
    path(
        'philippines/regions/',
        philippines_views.philippines_regions,
        name='philippines-regions'
    ),
    path(
        'philippines/thirteenth-month/',
        philippines_views.philippines_thirteenth_month,
        name='philippines-thirteenth-month'
    ),
    path(
        'philippines/overtime-rules/',
        philippines_views.philippines_overtime_rules,
        name='philippines-overtime-rules'
    ),
    path(
        'philippines/holiday-pay/',
        philippines_views.philippines_holiday_pay,
        name='philippines-holiday-pay'
    ),
    path(
        'philippines/cola/',
        philippines_views.philippines_cola,
        name='philippines-cola'
    ),
]
