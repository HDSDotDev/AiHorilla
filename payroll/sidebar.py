"""
payroll/sidebar.py

"""

from django.urls import reverse
from django.utils.translation import gettext_lazy as trans

MENU = trans("Payroll")
IMG_SRC = "images/ui/wallet-outline.svg"

SUBMENUS = [
    {
        "menu": trans("Dashboard"),
        "redirect": reverse("view-payroll-dashboard"),
        "accessibility": "payroll.sidebar.dasbhoard_accessibility",
    },
    {
        "menu": trans("Contract"),
        "redirect": reverse("view-contract"),
        "accessibility": "payroll.sidebar.dasbhoard_accessibility",
    },
    {
        "menu": trans("Allowances"),
        "redirect": reverse("view-allowance"),
        "accessibility": "payroll.sidebar.allowance_accessibility",
    },
    {
        "menu": trans("Deductions"),
        "redirect": reverse("view-deduction"),
        "accessibility": "payroll.sidebar.deduction_accessibility",
    },
    {
        "menu": trans("Payslips"),
        "redirect": reverse("view-payslip"),
    },
    {
        "menu": trans("Loan / Advanced Salary"),
        "redirect": reverse("view-loan"),
        "accessibility": "payroll.sidebar.loan_accessibility",
    },
    {
        "menu": trans("Encashments & Reimbursements"),
        "redirect": reverse("view-reimbursement"),
    },
    {
        "menu": trans("Federal Tax"),
        "redirect": reverse("filing-status-view"),
        "accessibility": "payroll.sidebar.federal_tax_accessibility",
    },
    {
        "menu": trans("SSS Contributions"),
        "redirect": reverse("philippines-sss-contributions"),
        "accessibility": "payroll.sidebar.philippines_only_menu",
    },
    {
        "menu": trans("PhilHealth Contributions"),
        "redirect": reverse("philippines-philhealth-contributions"),
        "accessibility": "payroll.sidebar.philippines_only_menu",
    },
    {
        "menu": trans("Pag-IBIG Contributions"),
        "redirect": reverse("philippines-pagibig-contributions"),
        "accessibility": "payroll.sidebar.philippines_only_menu",
    },
    {
        "menu": trans("BIR Tax Brackets"),
        "redirect": reverse("philippines-tax-brackets"),
        "accessibility": "payroll.sidebar.philippines_only_menu",
    },
    {
        "menu": trans("Regional Minimum Wage"),
        "redirect": reverse("philippines-regions"),
        "accessibility": "payroll.sidebar.philippines_only_menu",
    },
    {
        "menu": trans("13th Month Pay"),
        "redirect": reverse("philippines-thirteenth-month"),
        "accessibility": "payroll.sidebar.philippines_only_menu",
    },
    {
        "menu": trans("Generate 13th Month Pay"),
        "redirect": reverse("philippines-thirteenth-month-generator"),
        "accessibility": "payroll.sidebar.philippines_only_menu",
    },
    {
        "menu": trans("Overtime Rules"),
        "redirect": reverse("philippines-overtime-rules"),
        "accessibility": "payroll.sidebar.philippines_only_menu",
    },
    {
        "menu": trans("Holiday Pay"),
        "redirect": reverse("philippines-holiday-pay"),
        "accessibility": "payroll.sidebar.philippines_only_menu",
    },
    {
        "menu": trans("COLA (Cost of Living)"),
        "redirect": reverse("philippines-cola"),
        "accessibility": "payroll.sidebar.philippines_only_menu",
    },
    {
        "menu": trans("BIR Form 2316"),
        "redirect": reverse("philippines-bir-form-2316-list"),
        "accessibility": "payroll.sidebar.philippines_only_menu",
    },
    {
        "menu": trans("Final Pay Calculator"),
        "redirect": reverse("philippines-final-pay-calculator"),
        "accessibility": "payroll.sidebar.philippines_only_menu",
    },
    {
        "menu": trans("Final Pay Records"),
        "redirect": reverse("philippines-final-pay-list"),
        "accessibility": "payroll.sidebar.philippines_only_menu",
    },
    {
        "menu": trans("Government Forms"),
        "redirect": reverse("philippines-government-forms-generator"),
        "accessibility": "payroll.sidebar.philippines_only_menu",
    },
]


def dasbhoard_accessibility(request, submenu, user_perms, *args, **kwargs):
    return request.user.has_perm("payroll.view_contract")


def allowance_accessibility(request, submenu, user_perms, *args, **kwargs):
    return request.user.has_perm("payroll.view_allowance")


def deduction_accessibility(request, submenu, user_perms, *args, **kwargs):
    return request.user.has_perm("payroll.view_deduction")


def loan_accessibility(request, submenu, user_perms, *args, **kwargs):
    return request.user.has_perm("payroll.view_loanaccount")


def federal_tax_accessibility(request, submenu, user_perms, *args, **kwargs):
    """Show Federal Tax only when USA is the active country"""
    from payroll.models.country_models import PayrollCountryConfig
    try:
        active_country = PayrollCountryConfig.objects.filter(is_active=True).first()
        if active_country and active_country.country == 'USA':
            return request.user.has_perm("payroll.view_filingstatus")
        return False
    except:
        # Default to showing USA menus if no country config exists
        return request.user.has_perm("payroll.view_filingstatus")


def country_settings_accessibility(request, submenu, user_perms, *args, **kwargs):
    """Access to country settings - admin only"""
    return request.user.is_staff or request.user.is_superuser


def philippines_only_menu(request, submenu, user_perms, *args, **kwargs):
    """Show this menu only when Philippines is the active country"""
    from payroll.models.country_models import PayrollCountryConfig
    try:
        active_country = PayrollCountryConfig.objects.filter(is_active=True).first()
        if active_country and active_country.country == 'PH':
            return True
        return False
    except Exception as e:
        return False
